import os
import re
import json
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify'
]

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(WORKSPACE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(WORKSPACE_DIR, 'token.json')

def get_gmail_service():
    """Authenticates and returns the Gmail service using stored token."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)
        except Exception:
            creds = None
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(f"Missing credentials.json at: {CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)

try:
    from .scorecard_validator import validate_draft_against_scorecard
except ImportError:
    from scorecard_validator import validate_draft_against_scorecard

def extract_message_html(msg_payload):
    def _extract(part):
        if part.get('mimeType') == 'text/html' and 'data' in part.get('body', {}):
            return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
            raw = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            return f"<pre style='white-space: pre-wrap; font-family: inherit;'>{raw}</pre>"
        for p in part.get('parts', []):
            res = _extract(p)
            if res:
                return res
        return ""
    return _extract(msg_payload)

def build_parent_gmail_quote(service, thread_id: str) -> str:
    """
    Fetches the latest message in thread_id and returns the standard Gmail quote block:
    <div class="gmail_quote gmail_quote_container">...<blockquote class="gmail_quote">...</blockquote></div>
    This ensures Gmail renders the native 'three dots' (...) button!
    """
    try:
        tdata = service.users().threads().get(userId='me', id=thread_id, format='full').execute()
        msgs = tdata.get('messages', [])
        if not msgs:
            return ""
        
        real_msgs = [m for m in msgs if 'DRAFT' not in m.get('labelIds', [])]
        if not real_msgs:
            return ""
        
        last_msg = real_msgs[-1]
        headers = {h['name'].lower(): h['value'] for h in last_msg.get('payload', {}).get('headers', [])}
        
        parent_date = headers.get('date', '')
        parent_from = headers.get('from', '')
        parent_body = extract_message_html(last_msg.get('payload', {}))
        
        quote_html = (
            f'<br><div class="gmail_quote gmail_quote_container">'
            f'<div dir="ltr" class="gmail_attr">On {parent_date}, {parent_from} wrote:<br></div>'
            f'<blockquote class="gmail_quote" style="margin:0px 0px 0px 0.8ex;border-left:1px solid rgb(204,204,204);padding-left:1ex">'
            f'{parent_body}'
            f'</blockquote></div>'
        )
        return quote_html
    except Exception as e:
        print(f"Warning: Could not fetch parent email quote for thread {thread_id}: {e}")
        return ""

def extract_greeting_name(text_or_html: str) -> str:
    """Extracts the exact addressee name from an email greeting line."""
    clean_text = re.sub(r'<[^>]+>', ' ', text_or_html)
    clean_text = ' '.join(clean_text.split())
    # Match greeting up to comma, newline, exclamation mark, or HTML boundary
    m = re.search(r'\b(?:Hi|Hello|Hey|Dear)\s+([A-Za-z0-9\.\s\-\'&]+?)(?:,|\n|!|<|$)', clean_text)
    if m:
        return m.group(1).strip()
    return ""

def validate_thread_salutation_consistency(service, thread_id: str, html_body: str):
    """
    STRICT SALUTATION & THREAD IDENTITY GUARDRAIL:
    Inspects previous sent messages in thread_id.
    If the thread was previously addressed to a specific person (e.g. 'Liam'),
    and the new draft uses 'there', a generic team greeting, or a contradicting name (e.g. 'True Shine Windows Team'),
    raises a fatal ValueError and REFUSES to touch the Gmail API!
    """
    if not thread_id:
        return

    draft_name = extract_greeting_name(html_body)

    try:
        tdata = service.users().threads().get(userId='me', id=thread_id, format='full').execute()
        msgs = tdata.get('messages', [])

        for m in reversed(msgs):
            headers = {h['name'].lower(): h['value'] for h in m.get('payload', {}).get('headers', [])}
            m_from = headers.get('from', '')
            if any(k in m_from.lower() for k in ['shiv', 'innovatemarketers']) and 'DRAFT' not in m.get('labelIds', []):
                sent_body = extract_message_html(m.get('payload', {}))
                prev_name = extract_greeting_name(sent_body)
                if not prev_name:
                    continue

                prev_is_person = prev_name.lower() not in ['there', 'all', 'everyone']
                draft_is_generic = draft_name.lower() in ['there', 'all', 'everyone'] or not draft_name

                # If previous email addressed a specific person, new email CANNOT be downgraded to 'there' or switched
                if prev_is_person and draft_is_generic:
                    err_msg = (
                        f"\n{'='*70}\n"
                        f"FATAL SALUTATION GUARDRAIL ERROR!\n"
                        f"Thread ID: {thread_id}\n"
                        f"Previous sent email in thread was addressed to verified person: '{prev_name}'\n"
                        f"New draft attempted generic fallback:                        '{draft_name or '(empty)'}'\n"
                        f"BLOCKED: You cannot downgrade a personal recipient to generic mid-thread!\n"
                        f"Draft creation is COMPLETELY BLOCKED. Use 'Hi {prev_name},'.\n"
                        f"{'='*70}"
                    )
                    raise ValueError(err_msg)

                if prev_name.lower() != draft_name.lower():
                    # Substring check (e.g. "Lanett" in "Lanett Smith")
                    if draft_name.lower() in prev_name.lower() or prev_name.lower() in draft_name.lower():
                        continue
                    # Team greetings check
                    if 'team' in draft_name.lower() and 'team' in prev_name.lower():
                        continue

                    err_msg = (
                        f"\n{'='*70}\n"
                        f"FATAL SALUTATION GUARDRAIL ERROR!\n"
                        f"Thread ID: {thread_id}\n"
                        f"Previous sent email in thread was addressed to: '{prev_name}'\n"
                        f"New draft is addressed to:                      '{draft_name}'\n"
                        f"CONTRADICTION DETECTED: You cannot switch recipient names mid-thread!\n"
                        f"Draft creation is COMPLETELY BLOCKED to prevent sending wrong names.\n"
                        f"{'='*70}"
                    )
                    raise ValueError(err_msg)
                break
    except ValueError:
        raise
    except Exception as e:
        print(f"Warning in salutation validator: {e}")

def validate_not_suppressed(to_email: str):
    """
    STRICT SUPPRESSION GUARDRAIL:
    Blocks draft creation if to_email is in the suppression list (lost leads / unsubscribed).
    """
    if not to_email:
        return
    suppressed = [
        "sales@testequipmentusa.com",
        "marc@vehicleinspectors.com",
        "autopartsbling@gmail.com",
        "cooleyjana.rsu@outlook.com",
        "nuggetglass@gmail.com"
    ]
    suppression_file = os.path.join(WORKSPACE_DIR, "data", "suppression_list.json")
    if os.path.exists(suppression_file):
        try:
            with open(suppression_file, "r", encoding="utf-8") as sf:
                s_data = json.load(sf)
                suppressed.extend(s_data.get("suppressed_emails", []))
                suppressed.extend(s_data.get("suppressed_domains", []))
        except Exception:
            pass
    for s_email in suppressed:
        if s_email.lower() in to_email.lower():
            err_msg = (
                f"\n{'='*70}\n"
                f"FATAL SUPPRESSION GUARDRAIL ERROR!\n"
                f"Recipient: '{to_email}' is marked as LOST / NOT INTERESTED in data/suppression_list.json!\n"
                f"Draft creation is COMPLETELY BLOCKED to prevent sending emails to lost leads.\n"
                f"{'='*70}"
            )
            raise ValueError(err_msg)

def create_gmail_draft(to_email: str, subject: str, html_body: str, image_path: str = None, bounce_image_path: str = None, thread_id: str = None, last_message_id: str = None, references: str = None, include_gmail_quote: bool = True, attachment_paths: list = None):
    """Creates a draft in Gmail with inline CID image and Gmail-compatible inline styles.
    Supports both primary semrush_screenshot and optional bounce_screenshot, plus arbitrary file attachments.
    When thread_id is provided, automatically appends Gmail's native quote block so the 'three dots' (...)
    appear in Gmail web UI, seamlessly docking the draft inside the existing conversation thread.
    STRICT 1: Automatically validates that all numbers in html_body match the scorecard image OCR 100%.
    STRICT 2: Automatically validates that the salutation matches the previously sent email in the thread.
    STRICT 3: Programmatically blocks draft creation if recipient is marked LOST or suppressed.
    """
    # Programmatic gate 1: Check suppression / blacklist
    validate_not_suppressed(to_email)

    if image_path and os.path.exists(image_path):
        validate_draft_against_scorecard(html_body, image_path)

    service = get_gmail_service()
    
    # Programmatic gate: Validate thread salutation consistency
    if thread_id:
        validate_thread_salutation_consistency(service, thread_id, html_body)
    
    # If drafting inside an existing thread, automatically attach the native Gmail quote
    final_html = html_body
    if thread_id and include_gmail_quote and 'gmail_quote' not in html_body:
        quote_block = build_parent_gmail_quote(service, thread_id)
        if quote_block:
            final_html = html_body + quote_block
    
    # Inline image preparation & base64 replacement for 100% visibility in Web Gmail draft composer
    img_data = None
    bounce_data = None
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            img_data = f.read()
            b64_img = base64.b64encode(img_data).decode('utf-8')
            final_html = final_html.replace('cid:semrush_screenshot', f'data:image/png;base64,{b64_img}')
            
    if bounce_image_path and os.path.exists(bounce_image_path):
        with open(bounce_image_path, 'rb') as f:
            bounce_data = f.read()
            b64_bounce = base64.b64encode(bounce_data).decode('utf-8')
            final_html = final_html.replace('cid:bounce_screenshot', f'data:image/png;base64,{b64_bounce}')

    from email.mime.base import MIMEBase
    from email import encoders

    if attachment_paths:
        # Proper MIME hierarchy for HTML + inline images + file attachments: multipart/mixed -> multipart/related -> multipart/alternative
        msg_root = MIMEMultipart('mixed')
        msg_root['Subject'] = subject
        msg_root['To'] = to_email
        if last_message_id:
            msg_root['In-Reply-To'] = last_message_id
        if references:
            msg_root['References'] = references
        elif last_message_id:
            msg_root['References'] = last_message_id

        msg_related = MIMEMultipart('related')
        msg_root.attach(msg_related)

        msg_alt = MIMEMultipart('alternative')
        msg_related.attach(msg_alt)
        msg_alt.attach(MIMEText(final_html, 'html', 'utf-8'))

        if img_data:
            img = MIMEImage(img_data)
            img.add_header('Content-ID', '<semrush_screenshot>')
            img.add_header('Content-Disposition', 'inline', filename='scorecard.png')
            msg_related.attach(img)

        if bounce_data:
            img2 = MIMEImage(bounce_data)
            img2.add_header('Content-ID', '<bounce_screenshot>')
            img2.add_header('Content-Disposition', 'inline', filename='bounce.png')
            msg_related.attach(img2)

        for a_path in attachment_paths:
            if os.path.exists(a_path):
                part = MIMEBase('application', 'octet-stream')
                with open(a_path, 'rb') as af:
                    part.set_payload(af.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(a_path)}"')
                msg_root.attach(part)
        msg = msg_root
    else:
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['To'] = to_email
        if last_message_id:
            msg['In-Reply-To'] = last_message_id
        if references:
            msg['References'] = references
        elif last_message_id:
            msg['References'] = last_message_id
            
        msg_alt = MIMEMultipart('alternative')
        msg.attach(msg_alt)
        msg_alt.attach(MIMEText(final_html, 'html', 'utf-8'))
        
        if img_data:
            img = MIMEImage(img_data)
            img.add_header('Content-ID', '<semrush_screenshot>')
            img.add_header('Content-Disposition', 'inline', filename='scorecard.png')
            msg.attach(img)
                
        if bounce_data:
            img2 = MIMEImage(bounce_data)
            img2.add_header('Content-ID', '<bounce_screenshot>')
            img2.add_header('Content-Disposition', 'inline', filename='bounce.png')
            msg.attach(img2)
            
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
    body_data = {'message': {'raw': raw_message}}
    if thread_id:
        body_data['message']['threadId'] = thread_id

    # Anti-Duplicate Guardrail: Clean up any existing un-sent drafts for this recipient/thread
    try:
        existing_drafts = service.users().drafts().list(userId='me', q=f"to:{to_email}").execute().get('drafts', [])
        for d in existing_drafts:
            try:
                d_thread = d.get('message', {}).get('threadId', '')
                if not thread_id or thread_id == d_thread:
                    service.users().drafts().delete(userId='me', id=d['id']).execute()
                    print(f"Cleaned up superseded previous draft {d['id']}")
            except Exception:
                pass
    except Exception:
        pass

    try:
        draft = service.users().drafts().create(
            userId='me',
            body=body_data
        ).execute()
    except Exception as e:
        if '404' in str(e) and thread_id:
            print(f"Warning: Thread {thread_id} not found in Gmail. Retrying as standalone draft...")
            body_data['message'].pop('threadId', None)
            draft = service.users().drafts().create(
                userId='me',
                body=body_data
            ).execute()
        else:
            raise
    
    print(f"SUCCESS: Created Gmail draft! Draft ID: {draft['id']}" + (f" (Thread: {thread_id} with native quote)" if thread_id and 'threadId' in body_data['message'] else ""))
    return draft

def find_thread_by_email(to_email: str) -> dict:
    """Searches for the most recent thread involving to_email (either sent or received).
    Filters out internal CRM/system notifications and draft-only threads.
    Returns dict with thread_id, subject, last_message_id, references, or None if not found.
    """
    service = get_gmail_service()
    query = f"(from:{to_email} OR to:{to_email}) -from:noreply@mailer.innovatemarketers.com -from:mailer-daemon"
    try:
        res = service.users().threads().list(userId='me', q=query, maxResults=5).execute()
    except Exception:
        return None

    threads = res.get('threads', [])
    for t in threads:
        t_id = t['id']
        try:
            thread_detail = service.users().threads().get(userId='me', id=t_id, format='full').execute()
        except Exception:
            continue
        messages = thread_detail.get('messages', [])
        real_msgs = [m for m in messages if 'DRAFT' not in m.get('labelIds', [])]
        if not real_msgs:
            continue
        
        has_prospect = False
        for m in real_msgs:
            m_headers = {h['name'].lower(): h['value'] for h in m.get('payload', {}).get('headers', [])}
            m_from = m_headers.get('from', '').lower()
            m_to = m_headers.get('to', '').lower()
            if to_email.lower() in m_from or to_email.lower() in m_to:
                has_prospect = True
                break
        if not has_prospect:
            continue
        
        last_msg = real_msgs[-1]
        last_headers = {h['name'].lower(): h['value'] for h in last_msg.get('payload', {}).get('headers', [])}
        first_msg = real_msgs[0]
        first_headers = {h['name'].lower(): h['value'] for h in first_msg.get('payload', {}).get('headers', [])}
        
        subject = last_headers.get('subject') or first_headers.get('subject') or "Re: Quick question"
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
            
        last_msg_id = last_headers.get('message-id')
        existing_refs = last_headers.get('references', '')
        if existing_refs and last_msg_id:
            if last_msg_id not in existing_refs:
                references = f"{existing_refs} {last_msg_id}".strip()
            else:
                references = existing_refs
        elif last_msg_id:
            references = last_msg_id
        else:
            references = None
            
        return {
            'thread_id': t_id,
            'subject': subject,
            'last_message_id': last_msg_id,
            'references': references,
            'messages_count': len(real_msgs)
        }
        
    return None

def create_in_thread_draft(to_email: str, subject: str, html_body: str, thread_id: str, last_message_id: str = None, references: str = None, image_path: str = None, bounce_image_path: str = None):
    """Creates a draft directly inside an existing Gmail conversation thread
    containing ONLY the clean follow-up lines without attaching the entire past thread history.
    """
    return create_gmail_draft(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        image_path=image_path,
        bounce_image_path=bounce_image_path,
        thread_id=thread_id,
        last_message_id=last_message_id,
        references=references,
        include_gmail_quote=True
    )
