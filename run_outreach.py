import os
import sys
import argparse
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure workspace root is in sys.path
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from src.lead_parser import parse_lead_file
from src.semrush_crawler import capture_semrush_overview, SCREENSHOTS_DIR
from src.outreach_generator import generate_outreach_email_and_brief
from src.gmail_helper import create_gmail_draft

def process_leads(leads_path: str = "leads.md", headless_semrush: bool = False):
    print("=" * 80)
    print("🚀 INNOVATE MARKETERS — AUTOMATED LEAD OUTREACH PIPELINE")
    print("=" * 80)

    if not os.path.exists(leads_path):
        print(f"\n❌ Error: Leads file not found at: {leads_path}")
        print("Please create leads.md and paste your lead details.")
        return

    print(f"\n📂 Reading leads intake queue: {leads_path}")
    leads = parse_leads_file(leads_path)

    if not leads:
        print("\n⚠️  No leads found in leads.md.")
        print("How to add a lead to leads.md:")
        print("  1. Open leads.md in your editor")
        print("  2. Take screenshot of PMS (Win+Shift+S) and paste (Ctrl+V) image")
        print("  3. Paste conversation text below the screenshot")
        print("  4. Add '---' between multiple leads")
        print("  5. Run: python run_outreach.py")
        return

    print(f"✅ Found {len(leads)} lead(s) to process.\n")

    results = []

    for idx, lead in enumerate(leads, 1):
        company = lead.get("company_name", "Unknown Business")
        client = lead.get("client_name", "Lead")
        domain = lead.get("domain", "")
        slug = lead.get("client_slug", "lead")
        colleague = lead.get("colleague_name", "My colleague")
        to_email = lead.get("email", "")

        print("-" * 80)
        print(f"📍 [{idx}/{len(leads)}] Processing: {company} | Client: {client} | Colleague: {colleague}")
        print(f"   Domain: {domain} | Email: {to_email}")
        print("-" * 80)

        # 1. Semrush Card Capture
        metrics = {}
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{slug}_seo.png")
        if domain:
            try:
                metrics = capture_semrush_overview(domain=domain, client_slug=slug, headless=headless_semrush)
                screenshot_path = metrics.get("screenshot_path", screenshot_path)
            except Exception as e:
                print(f"   ⚠️  Semrush capture notice: {e}")
                if not os.path.exists(screenshot_path):
                    screenshot_path = None
        else:
            print("   ⚠️  No domain found, skipping Semrush crawl.")
            screenshot_path = None

        # 2. Outreach Synthesis (Email Copy + Call Copilot Brief)
        try:
            email_html, subject, brief_path = generate_outreach_email_and_brief(lead_info=lead, metrics=metrics)
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            continue

        # 3. Create Draft in Web Gmail
        draft_id = None
        if to_email:
            try:
                print(f"   📨 Injecting draft into web Gmail for: {to_email}...")
                draft = create_gmail_draft(
                    to_email=to_email,
                    subject=subject,
                    html_body=email_html,
                    image_path=screenshot_path
                )
                draft_id = draft.get("id")
                print(f"   ✨ DRAFT CREATED! ID: {draft_id}")
            except Exception as e:
                print(f"   ❌ Failed to inject Gmail draft: {e}")
        else:
            print("   ⚠️  No recipient email found, skipping Gmail draft injection.")

        results.append({
            "company": company,
            "client": client,
            "colleague": colleague,
            "email": to_email,
            "metrics": f"AS {metrics.get('authority_score', 'N/A')} | Traffic {metrics.get('organic_traffic', 'N/A')} | KWs {metrics.get('keywords', 'N/A')}",
            "brief": brief_path,
            "draft_id": draft_id or "Not created"
        })

    # Summary Table
    print("\n" + "=" * 80)
    print("📊 BATCH OUTREACH EXECUTION SUMMARY")
    print("=" * 80)
    for r in results:
        print(f"• {r['company']} ({r['client']})")
        print(f"  Colleague Attribution : {r['colleague']}")
        print(f"  Recipient Email       : {r['email']}")
        print(f"  SEO Metrics           : {r['metrics']}")
        print(f"  Call Copilot Brief    : {r['brief']}")
        print(f"  Gmail Draft ID        : {r['draft_id']}")
        print(f"  Next Action           : Open mail.google.com -> Drafts -> Click Send 🚀")
        print("-" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Innovate Marketers Automated Outreach Pipeline")
    parser.add_argument("--leads", default="leads.md", help="Path to leads intake markdown file (default: leads.md)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (default: visible headed mode)")
    args = parser.parse_args()

    process_leads(leads_path=args.leads, headless_semrush=args.headless)
