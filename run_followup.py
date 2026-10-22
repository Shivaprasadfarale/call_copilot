import os
import sys
import argparse
import glob
import re

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from src.gmail_helper import find_thread_by_email, create_in_thread_draft
from src.followup_generator import generate_followup_body

LEADS_KB_DIR = os.path.join(WORKSPACE_DIR, "knowledge_base", "leads")

KNOWN_LEADS = {
    "canyondavetours": {"email": "canyondavetours@gmail.com", "first_name": "Dave & Dora", "company_name": "Canyon Dave Tours", "niche": "Grand Canyon Tours", "fatal_flaw": "89% foreign bot traffic leak"},
    "rcmacapital": {"email": "colin@rcmacapital.com", "first_name": "Colin", "company_name": "RCMA Capital Markets Corp.", "niche": "Capital Markets Advisory", "fatal_flaw": "backlink/traffic disconnect and zero traffic"},
    "studiorue": {"email": "rue3406@gmail.com", "first_name": "Mark", "company_name": "Studio Rue", "niche": "Commercial & Architectural Photography", "fatal_flaw": "zero traffic on commercial keywords in San Antonio"},
    "mksdevelopment": {"email": "kc@mksdevelopment.com", "first_name": "KC", "company_name": "MKS Development", "niche": "Commercial Real Estate Development", "fatal_flaw": "71% foreign bot traffic and page 1 competitor dominance"},
    "nicotinefreecigarettes": {"email": "info@nicotinefreecigarettes.com", "first_name": "there", "company_name": "Smoke Free USA", "niche": "Nicotine-Free Cigarettes", "fatal_flaw": "296 backlinks but 1 visit/mo and 0% US traffic"},
    "k9sinflight": {"email": "k9sinflight@gmail.com", "first_name": "John", "company_name": "K9s in Flight", "niche": "Dog Entertainment & Stunt Shows", "fatal_flaw": "under 10 visits/mo and 5% US share"},
    "fenceinvestments": {"email": "greg@fenceinvestments.com", "first_name": "Greg", "company_name": "Fence Investments", "niche": "Fence Installation & Construction", "fatal_flaw": "technical indexing errors and low local rankings"},
    "buenossabores": {"email": "gromeroh4@gmail.com", "first_name": "Gerardo", "company_name": "Buenos Sabores", "niche": "Food Manufacturing & Catering", "fatal_flaw": "missing commercial search keywords"},
    "airborneroofing": {"email": "airborneroofing@gmail.com", "first_name": "George", "company_name": "Airborne Roofing", "niche": "Commercial & Residential Roofing", "fatal_flaw": "competitors ranking on page 1 for local roofing"},
    "penningtonsecurity": {"email": "info@penningtonsecurity.com", "first_name": "there", "company_name": "Pennington Security", "niche": "Security Guard Services", "fatal_flaw": "severe keyword dilution and foreign bot crawl"},
    "chakraflowuniversity": {"email": "hello@chakraflowuniversity.com", "first_name": "Victoria", "company_name": "Chakra Flow University", "niche": "Holistic Healing & Coaching", "fatal_flaw": "traffic drop and low US search visibility"},
    "alaskahighwaynews": {"email": "alaskahighwaynews@outlook.com", "first_name": "Todd", "company_name": "Alaska Highway News", "niche": "Regional News & Advertising", "fatal_flaw": "314 referring domains but 0% US traffic and traffic dropping 7.5%"},
    "headintheclouds": {"email": "headintheclouds.headspa@gmail.com", "first_name": "Gabriela", "company_name": "Head In the Clouds Head Spa", "niche": "Japanese Head Spa & Scalp Treatments", "fatal_flaw": "96% foreign bot traffic leak and competitor dominance in Reno"},
    "smrrental": {"email": "SMR@smrrental.com", "first_name": "Sarah", "company_name": "SMR Management", "niche": "Property Management & Rental Housing", "fatal_flaw": "94% foreign bot traffic leak and Mankato competitor dominance"},
    "trashhounds": {"email": "lamarterrell87@gmail.com", "first_name": "Lamar", "company_name": "Trash Hounds CT", "niche": "Dumpster Rental & Cleanouts", "fatal_flaw": "148 backlinks but zero search traffic while Danny's Dump Runs takes Glastonbury jobs"},
    "asphaltexps": {"email": "reparationdasphaltexps@gmail.com", "first_name": "Tony", "company_name": "Réparation d'Asphalte XPS", "niche": "Asphalt Paving & Repair", "fatal_flaw": "472 backlinks but only 156 visits/mo while Pavage Élite and Asphalte Laval take Montreal paving contracts"},
    "raspberryhills": {"email": "raspberryhillsclothes@gmail.com", "first_name": "there", "company_name": "Raspberry Hills Clothes", "niche": "Streetwear & Apparel", "fatal_flaw": "99% foreign bot traffic and only 1% US visitors while Represent Clo and MNML take streetwear sales"}
}

def load_lead_brief(slug_or_email: str) -> dict:
    """Loads lead details from KNOWN_LEADS or markdown files in knowledge_base/leads/"""
    query = slug_or_email.lower().strip()
    
    # Check known leads first
    for k, v in KNOWN_LEADS.items():
        if k in query or v['email'].lower() in query:
            return v.copy()

    # Search in client vaults and fallback markdown files
    vault_files = glob.glob(os.path.join(WORKSPACE_DIR, "clients", "*", "brief.md"))
    legacy_files = glob.glob(os.path.join(LEADS_KB_DIR, "*.md"))
    files = vault_files + legacy_files
    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            content = file.read()
            if query in f.lower() or query in content.lower():
                email_match = re.search(r'Email[:\*\|\s`]+([a-zA-Z0-9_.+\-\s]+@[a-zA-Z0-9-.\s]+)', content)
                name_match = re.search(r'(?:Client Contact Name|Decision Maker|First Name)[:\*\|\s]+([^\n\|(]+)', content)
                company_match = re.search(r'(?:Company Name|Business Name|Business)[:\*\|\s]+([^\n\|]+)', content)
                niche_match = re.search(r'(?:Niche|Vertical)[:\*\|\s]+([^\n\|]+)', content)

                email = email_match.group(1).replace(" ", "").replace("`", "").strip() if email_match else ""
                name = name_match.group(1).strip() if name_match else "there"
                company = company_match.group(1).strip() if company_match else "your business"
                niche = niche_match.group(1).strip() if niche_match else ""

                first_name = name.split()[0] if name else "there"
                if "&" in name:
                    first_name = name

                return {
                    "client_name": name,
                    "first_name": first_name,
                    "email": email,
                    "company_name": company,
                    "niche": niche,
                    "file": f
                }
    return {}

def process_followup(email: str, slug: str = None):
    print("=" * 80)
    print("🚀 IN-THREAD 48-HOUR FOLLOW-UP GENERATOR")
    print("=" * 80)

    lead = {}
    if slug:
        lead = load_lead_brief(slug)
    if not lead and email:
        lead = load_lead_brief(email)

    target_email = email or lead.get("email")
    if not target_email:
        print(f"❌ Error: Could not determine email address for: {slug or email}")
        return

    # Strict suppression check: block lost / unsubscribed leads
    suppression_file = os.path.join(WORKSPACE_DIR, "data", "suppression_list.json")
    suppressed_emails = ["sales@testequipmentusa.com", "marc@vehicleinspectors.com"]
    if os.path.exists(suppression_file):
        try:
            import json
            with open(suppression_file, "r", encoding="utf-8") as sf:
                s_data = json.load(sf)
                suppressed_emails.extend(s_data.get("suppressed_emails", []))
        except Exception:
            pass

    if any(se.lower() in target_email.lower() for se in suppressed_emails) or (slug and any(x in slug.lower() for x in ["testequipmentusa", "vehicleinspectors"])):
        print(f"\n⛔ STOP: {target_email} is in the SUPPRESSION / LOST LEADS list!")
        print("Lead is marked LOST / NOT INTERESTED / UNSUBSCRIBED. DO NOT SEND EMAILS.")
        print("Aborting follow-up generation to strictly prevent outreach.\n")
        return

    # Strict protection: do not email on-hold or paused leads
    if lead.get("on_hold") or (slug and "voicevantage" in slug.lower()) or "thctechnologies" in target_email.lower():
        print(f"⛔ STOP: {lead.get('company_name', target_email)} is marked ON HOLD / SNOOZED!")
        print("Client is undergoing internal website updates and requested not to be contacted until November 6, 2026.")
        print("Safely aborting follow-up generation to prevent accidental email.")
        return

    first_name = lead.get("first_name", "there")
    company = lead.get("company_name", "your business")
    print(f"\n📍 Target: {first_name} at {company} ({target_email})")
    print(f"🔍 Searching Gmail for existing conversation thread...")

    try:
        thread_info = find_thread_by_email(target_email)
    except Exception as e:
        print(f"❌ Failed to query Gmail threads: {e}")
        print("\nNote: If you see insufficient permissions, re-authentication with gmail.modify is required.")
        return

    if not thread_info or not thread_info.get("thread_id"):
        print(f"⚠️  No existing Gmail thread found for recipient: {target_email}")
        print("Please check if you sent the previous email to this exact address from this account.")
        return

    thread_id = thread_info["thread_id"]
    subject = thread_info["subject"]
    last_msg_id = thread_info["last_message_id"]

    print(f"✅ Found Existing Thread ID: {thread_id}")
    print(f"   Subject: {subject}")
    print(f"   Last Message ID: {last_msg_id}")

    # Inspect previous sent messages to extract the EXACT established greeting name
    from src.gmail_helper import get_gmail_service, extract_message_html, extract_greeting_name
    try:
        service = get_gmail_service()
        tdata = service.users().threads().get(userId='me', id=thread_id, format='full').execute()
        msgs = tdata.get('messages', [])
        for m in reversed(msgs):
            headers = {h['name'].lower(): h['value'] for h in m.get('payload', {}).get('headers', [])}
            m_from = headers.get('from', '')
            if any(k in m_from.lower() for k in ['shiv', 'innovatemarketers']) and 'DRAFT' not in m.get('labelIds', []):
                sent_body = extract_message_html(m.get('payload', {}))
                t_name = extract_greeting_name(sent_body)
                if t_name:
                    print(f"   🎯 Thread Established Greeting: 'Hi {t_name},' (Inheriting 1:1)")
                    lead["first_name"] = t_name
                    lead["client_name"] = t_name
                    break
    except Exception as e:
        print(f"   ⚠️ Could not inspect thread greeting: {e}")

    # Clean company name: Never write raw domain URLs like www . domain . com as company names
    comp = lead.get("company_name", "")
    if any(x in comp.lower() for x in [".com", ".net", ".org", "www."]):
        clean_comp = re.sub(r'https?://', '', comp)
        clean_comp = re.sub(r'www\.', '', clean_comp)
        clean_comp = clean_comp.split('.')[0].replace('-', ' ').replace('_', ' ').title()
        lead["company_name"] = clean_comp

    # Check if thread already had a 22-page visual report or PDF attached
    is_post_report = False
    try:
        for m in msgs:
            sent_body = extract_message_html(m.get('payload', {}))
            if any(k in sent_body.lower() for k in ["22-page", "visual report", "visual search audit", ".pdf", "attached report"]):
                is_post_report = True
                print("   📎 Detected prior visual search audit delivery in thread (Using Post-Report meeting follow-up mode)")
                break
    except Exception:
        pass

    print(f"\n✍️  Synthesizing personalized in-thread follow-up draft (Post-Report: {is_post_report})...")
    followup_html = generate_followup_body(lead, is_post_report=is_post_report)

    print(f"📨 Injecting draft directly into thread {thread_id}...")
    try:
        draft = create_in_thread_draft(
            to_email=target_email,
            subject=subject,
            html_body=followup_html,
            thread_id=thread_id,
            last_message_id=last_msg_id
        )
        print("\n" + "=" * 80)
        print("✨ SUCCESS! DRAFT INJECTED DIRECTLY INTO THREAD!")
        print(f"   Draft ID: {draft['id']}")
        print(f"   Thread ID: {thread_id}")
        print(f"   Recipient: {target_email}")
        print(f"   Status: Un-sent draft placed inside existing conversation thread.")
        print("   👉 Open web Gmail -> Open the thread -> Review draft -> Click SEND.")
        print("=" * 80 + "\n")
    except Exception as e:
        print(f"❌ Failed to create in-thread draft: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create in-thread 48-hour follow-up draft in Gmail.")
    parser.add_argument("--email", "-e", help="Client email address", default=None)
    parser.add_argument("--slug", "-s", help="Client slug (e.g. canyondavetours)", default=None)

    args = parser.parse_args()
    if not args.email and not args.slug:
        print("Usage: python run_followup.py --email <client@email.com> OR --slug <client_slug>")
        print("Example: python run_followup.py --slug canyondavetours")
    else:
        process_followup(email=args.email, slug=args.slug)
