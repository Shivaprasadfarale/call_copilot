import os
import sys
import json
import re
import email.utils
from datetime import datetime, timezone
from typing import Dict, Any, List

sys.path.insert(0, os.getcwd())

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.gmail_helper import (
    get_gmail_service,
    extract_message_html,
    extract_greeting_name,
    create_in_thread_draft,
    validate_thread_salutation_consistency
)
from src.followup_generator import generate_followup_body

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(WORKSPACE_DIR, "clients", "index.json")

TARGET_SLUGS = [
    "billingsrental",
    "donithanlogistics",
    "drcarol",
    "dreamearthbowl",
    "ecosystemsnorthwest",
    "emergencytreeservices",
    "ericahomes",
    "experiencedetailing",
    "firstteammedia",
    "fixknix",
    "halalfoodbank",
    "hearthpropertycare",
    "myhomesworks",
    "northernproducts",
    "nuggetglass",
    "phillylawyers",
    "rchitects",
    "wadadlisolar",
    "canyondavetours",
    "mksdevelopment",
    "nicotinefreecigarettes",
    "studiorue",
    "willowcreekminihighlands"
]

def clean_company_name(comp: str, slug: str) -> str:
    if not comp:
        return slug.replace("-", " ").title()
    comp = re.sub(r'^(?:https?:\/\/)?(?:www\.)?', '', comp)
    comp = comp.split('/')[0]
    comp = re.sub(r'\.(?:com|org|net|us|ca|io|biz|info)$', '', comp, flags=re.IGNORECASE)
    comp = comp.replace("**", "").replace("`", "").strip()
    return comp

def run_inject_batch_2(dry_run: bool = False):
    print("=" * 80)
    print("🚀 BATCH 2 IN-THREAD FOLLOW-UP INJECTOR (23 RECOVERED LEADS)")
    print(f"Mode: {'DRY RUN (Preview Only)' if dry_run else 'LIVE INJECTION TO GMAIL'}")
    print("=" * 80 + "\n")

    service = get_gmail_service()
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        clients_idx = json.load(f)

    now = datetime.now(timezone.utc)
    success_count = 0
    errors = []

    for idx, slug in enumerate(TARGET_SLUGS, 1):
        cdata = clients_idx.get(slug, {})
        to_em = cdata.get("email", "").strip()
        comp = clean_company_name(cdata.get("company_name", ""), slug)

        print(f"[{idx}/{len(TARGET_SLUGS)}] Processing {comp} ({to_em}) [slug: {slug}]")

        try:
            res = service.users().threads().list(userId='me', q=to_em, maxResults=1).execute()
            threads = res.get('threads', [])
            if not threads:
                print(f"    ❌ No thread found in Gmail for {to_em}")
                continue

            th_id = threads[0]['id']
            th_data = service.users().threads().get(userId='me', id=th_id, format='full').execute()
            msgs = th_data.get('messages', [])
            if not msgs:
                print(f"    ❌ Empty thread")
                continue

            # Check if there is already an existing draft in this thread
            has_existing_draft = False
            for m in msgs:
                if 'DRAFT' in m.get('labelIds', []):
                    has_existing_draft = True
                    break
            if has_existing_draft:
                print(f"    ⚠️ Thread already has a draft. Skipping.")
                continue

            last_m = msgs[-1]
            hdrs = {h['name'].lower(): h['value'] for h in last_m.get('payload', {}).get('headers', [])}
            last_from = hdrs.get('from', '').lower()
            last_date_str = hdrs.get('date', '')
            last_subj = hdrs.get('subject', '')
            last_mid = hdrs.get('message-id')

            # Extract established greeting name
            established_greeting = ""
            is_post_report = False

            for m in reversed(msgs):
                m_hdrs = {h['name'].lower(): h['value'] for h in m.get('payload', {}).get('headers', [])}
                m_from = m_hdrs.get('from', '').lower()
                if any(k in m_from for k in ['shiv', 'innovatemarketers']) and 'DRAFT' not in m.get('labelIds', []):
                    m_html = extract_message_html(m.get('payload', {}))
                    if not established_greeting:
                        t_name = extract_greeting_name(m_html)
                        if t_name:
                            established_greeting = t_name
                    if any(k in m_html.lower() for k in ["22-page", "visual report", "visual search audit", ".pdf", "attached report"]):
                        is_post_report = True

            if not established_greeting:
                raw_cname = cdata.get("contact_name", "").replace("**", "").strip()
                if raw_cname and raw_cname.lower() not in ["business owner", "there", "team"]:
                    established_greeting = raw_cname
                else:
                    established_greeting = "there"

            lead_info = {
                "first_name": established_greeting,
                "client_name": established_greeting,
                "company_name": comp,
                "niche": "your industry"
            }

            followup_html = generate_followup_body(lead_info, is_post_report=is_post_report)

            # Ensure salutation matches exactly
            draft_greeting = extract_greeting_name(followup_html)
            if established_greeting.lower() != "there" and draft_greeting.lower() == "there":
                followup_html = re.sub(
                    r'<p[^>]*>Hi [^,<]+[,!]?</p>',
                    f'<p style="margin: 0 0 14px 0; font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.6;">Hi {established_greeting},</p>',
                    followup_html,
                    count=1
                )

            # Extract snippet for log
            clean_snippet = re.sub(r'<[^>]+>', ' ', followup_html)
            clean_snippet = ' '.join(clean_snippet.split())[:80]
            print(f"    Greeting: 'Hi {established_greeting},' | PostReport: {is_post_report}")
            print(f"    Snippet: {clean_snippet}...")

            if dry_run:
                print(f"    [DRY RUN] Would inject draft into thread {th_id}")
                success_count += 1
                continue

            draft = create_in_thread_draft(
                to_email=to_em,
                subject=last_subj if last_subj.lower().startswith("re:") else f"Re: {last_subj}",
                html_body=followup_html,
                thread_id=th_id,
                last_message_id=last_mid
            )
            print(f"    ✅ Injected Draft ID: {draft['id']} (Thread: {th_id})")
            success_count += 1

        except Exception as e:
            print(f"    ❌ Error injecting draft for {slug}: {e}")
            errors.append({"slug": slug, "email": to_em, "error": str(e)})

    print("\n" + "=" * 80)
    print(f"BATCH COMPLETE! Successfully created {success_count} drafts out of {len(TARGET_SLUGS)} target leads.")
    if errors:
        print(f"Errors encountered on {len(errors)} leads: {errors}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    run_inject_batch_2(dry_run=is_dry)
