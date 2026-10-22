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
SUPPRESSION_FILE = os.path.join(WORKSPACE_DIR, "data", "suppression_list.json")


def load_suppressed_list() -> List[str]:
    suppressed = ["sales@testequipmentusa.com", "marc@vehicleinspectors.com"]
    if os.path.exists(SUPPRESSION_FILE):
        try:
            with open(SUPPRESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                suppressed.extend(data.get("suppressed_emails", []))
        except Exception:
            pass
    return [e.lower().strip() for e in suppressed]


def clean_company_name(comp: str, slug: str) -> str:
    if not comp:
        return slug.replace("_", " ").title()
    clean = comp.replace("**", "").replace("`", "").strip()
    if any(x in clean.lower() for x in [".com", ".net", ".org", "www."]):
        clean = re.sub(r'https?://', '', clean)
        clean = re.sub(r'www\.', '', clean)
        clean = clean.split('.')[0].replace('-', ' ').replace('_', ' ').title()
    return clean.strip() or slug.replace("_", " ").title()


def get_all_eligible_followup_threads(service, clients_idx: dict, suppressed: list) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    eligible = []

    print(f"Scanning all {len(clients_idx)} clients for eligible follow-ups...")

    for slug, cdata in clients_idx.items():
        raw_email = cdata.get("email", "").replace("`", "").replace(" ", "").replace("*", "").strip()
        if not raw_email or "@" not in raw_email:
            continue

        clean_em = raw_email.lower()
        if any(se in clean_em for se in suppressed) or any(x in slug.lower() for x in ["testequipmentusa", "vehicleinspectors", "voicevantage", "thctechnologies"]):
            continue

        if slug in ["raspberryhills", "smrrental"]:
            continue

        try:
            res = service.users().threads().list(userId='me', q=raw_email, maxResults=1).execute()
            threads = res.get('threads', [])
            if not threads:
                continue

            th_id = threads[0]['id']
            th_data = service.users().threads().get(userId='me', id=th_id, format='full').execute()
            msgs = th_data.get('messages', [])
            if not msgs:
                continue

            # Check if there is already an existing draft in this thread
            has_existing_draft = False
            for m in msgs:
                if 'DRAFT' in m.get('labelIds', []):
                    has_existing_draft = True
                    break
            if has_existing_draft:
                continue

            last_m = msgs[-1]
            hdrs = {h['name'].lower(): h['value'] for h in last_m.get('payload', {}).get('headers', [])}
            last_from = hdrs.get('from', '').lower()
            last_date_str = hdrs.get('date', '')
            last_subj = hdrs.get('subject', '')

            # Only follow up if our email was the last one sent
            is_from_us = any(k in last_from for k in ['shiv', 'innovatemarketers'])
            if not is_from_us:
                continue

            parsed_date = email.utils.parsedate_to_datetime(last_date_str) if last_date_str else None
            if not parsed_date:
                continue

            age_hours = (now - parsed_date).total_seconds() / 3600
            if age_hours < 48:
                continue

            # Find the last message sent by us to extract the EXACT established greeting name and message-id
            established_greeting = ""
            is_post_report = False
            last_msg_id = hdrs.get('message-id')

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

            comp_name = clean_company_name(cdata.get("company_name", ""), slug)

            # Fallback to brief contact name if no greeting extracted
            if not established_greeting:
                raw_cname = cdata.get("contact_name", "").replace("**", "").strip()
                if raw_cname and raw_cname.lower() not in ["business owner", "there", "team"]:
                    established_greeting = raw_cname.split()[0]
                else:
                    established_greeting = "there"

            eligible.append({
                "slug": slug,
                "company_name": comp_name,
                "established_greeting": established_greeting,
                "email": raw_email,
                "thread_id": th_id,
                "subject": last_subj,
                "last_message_id": last_msg_id,
                "age_hours": round(age_hours, 1),
                "is_post_report": is_post_report
            })

        except Exception as e:
            # print(f"Error checking {slug}: {e}")
            pass

    return eligible


def run_batch_injection(dry_run: bool = False):
    print("=" * 80)
    print("🚀 BATCH IN-THREAD FOLLOW-UP INJECTOR")
    print(f"Mode: {'DRY RUN (Preview Only)' if dry_run else 'LIVE INJECTION TO GMAIL'}")
    print("=" * 80 + "\n")

    service = get_gmail_service()
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        clients_idx = json.load(f)

    suppressed = load_suppressed_list()
    eligible = get_all_eligible_followup_threads(service, clients_idx, suppressed)

    print(f"\nFound {len(eligible)} eligible client threads awaiting follow-up drafts.\n")

    success_count = 0
    errors = []

    for idx, item in enumerate(eligible, 1):
        slug = item["slug"]
        greeting = item["established_greeting"]
        comp = item["company_name"]
        to_em = item["email"]
        th_id = item["thread_id"]
        subj = item["subject"]
        last_mid = item["last_message_id"]
        is_post = item["is_post_report"]

        print(f"[{idx}/{len(eligible)}] Processing {comp} ({to_em})")
        print(f"    Greeting: 'Hi {greeting},' | Post-Report Mode: {is_post} | Sent {item['age_hours']}h ago")

        lead_info = {
            "first_name": greeting,
            "client_name": greeting,
            "company_name": comp,
            "niche": "your industry"
        }

        try:
            followup_html = generate_followup_body(lead_info, is_post_report=is_post)

            # Ensure salutation matches exactly
            draft_greeting = extract_greeting_name(followup_html)
            if greeting.lower() != "there" and draft_greeting.lower() == "there":
                followup_html = re.sub(r'<p[^>]*>Hi [^,<]+[,!]?</p>', f'<p style="margin: 0 0 14px 0; font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.6;">Hi {greeting},</p>', followup_html, count=1)

            if dry_run:
                print(f"    [DRY RUN] Would inject draft into thread {th_id} with greeting 'Hi {greeting},'")
                success_count += 1
                continue

            draft = create_in_thread_draft(
                to_email=to_em,
                subject=subj if subj.lower().startswith("re:") else f"Re: {subj}",
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
    print(f"BATCH COMPLETE! Successfully created {success_count} drafts out of {len(eligible)} eligible.")
    if errors:
        print(f"Errors encountered on {len(errors)} leads: {errors}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    run_batch_injection(dry_run=is_dry)
