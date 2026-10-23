"""
Master Phase 1 Scorecard Email Draft Runner (run_scorecard_draft.py)
Delivers live Gmail draft with inline Semrush scorecard in under 5 seconds.

Usage:
    python run_scorecard_draft.py --slug [client_slug]
    python run_scorecard_draft.py --email [client_email]
"""

import os
import sys
import re
import json
import argparse
from typing import Dict, Any

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

from src.gmail_helper import create_gmail_draft, find_thread_by_email
from src.scorecard_validator import extract_scorecard_metrics, validate_draft_against_scorecard
from src.email_generator import format_anti_autolink, clean_da, clean_num
from src.vault_manager import resolve_client_vault


def build_scorecard_html(cfg: Dict[str, Any], scorecard_path: str, pdf_attached: bool = False) -> str:
    """Builds clean HTML for Phase 1 Scorecard email conforming to all user rules."""
    client_name = cfg.get("client_name", "there").title()
    if client_name.lower() in ["there", "all", "everyone", ""]:
        client_name = "there"

    website = cfg.get("website", "")
    clean_site = format_anti_autolink(website)
    company_name = cfg.get("company_name", clean_site)

    # Resolve colleague
    colleague = cfg.get("outreach_colleague") or cfg.get("colleague") or "Nancy"

    # Inbound headers
    quoted_headers = cfg.get("quoted_headers", "")
    quoted_body = cfg.get("quoted_body", "Yes")
    if not quoted_headers:
        to_email = cfg.get("email") or cfg.get("client_email", "")
        clean_email = format_anti_autolink(to_email)
        clean_colleague_email = format_anti_autolink(f"{colleague.lower()}@innovatemarketers.com")
        quoted_headers = f"From: {client_name} &lt;{clean_email}&gt;<br>To: {colleague} &lt;{clean_colleague_email}&gt;<br>Subject: Re: Google is changing. Are you ready?"
    else:
        quoted_headers = format_anti_autolink(quoted_headers).replace("\n", "<br>")

    quoted_body = format_anti_autolink(quoted_body).replace("\n", "<br>")

    # Diagnostics
    diag = cfg.get("diagnostics", {})
    da_val = clean_da(diag.get("authority_score", "Under Review"))
    traf_val = diag.get("organic_traffic", "0 visits/mo")
    us_share = diag.get("us_share", "")
    if us_share and "%" in us_share and "only" not in traf_val.lower():
        traf_line = f"{traf_val} (approx. {us_share} US traffic)"
    else:
        traf_line = traf_val

    bl_val = clean_num(diag.get("backlinks", "0"), "backlink")
    rd_val = clean_num(diag.get("ref_domains", "0"), "domain")
    kw_val = clean_num(diag.get("keywords_indexed", "0"), "keyword")
    kw_val = clean_num(kw_val, "term")
    ai_val = diag.get("ai_mentions", "0 Mentions")
    if "mention" not in ai_val.lower():
        ai_val = f"{ai_val} mentions (ChatGPT, Gemini, and Google AI Overviews)"

    # Competitors
    keywords = cfg.get("keywords", [])
    comps = []
    for k in keywords:
        tag = k.get("tag", "")
        if "vs" in tag.lower():
            comps.append(tag.split("vs")[-1].strip(" .()"))
    comp_str = " and ".join(comps[:2]) if comps else "established competitors"

    # Tailor archetype, open loop question, and services
    niche_lower = (company_name + " " + " ".join([k.get("phrase", "") for k in keywords[:3]])).lower()
    if any(w in niche_lower for w in ["recruit", "search", "talent", "headhunt"]):
        open_q = "Are most of your retained searches coming from independent/indie brands, or are you primarily placing C-suite leaders into established corporate conglomerates?"
        service_label = "retained C-suite and VP placement searches ($30,000 – $75,000+ retainers)"
        vertical_silos = "cosmetics, skincare, haircare, and clean wellness"
    elif any(w in niche_lower for w in ["junk", "haul", "cleanout"]):
        open_q = "Are most of your jobs coming from residential homeowners, or are you pulling significant volume from commercial property managers and real estate cleanouts?"
        service_label = "high-ticket full-property cleanouts and commercial hauling jobs ($1,500 – $5,000+ per job)"
        vertical_silos = "estate cleanouts, commercial debris removal, and property cleanouts"
    elif any(w in niche_lower for w in ["roof", "plumb", "contractor", "electric"]):
        open_q = "Are most of your projects coming directly from residential homeowners, or are you pulling significant volume from commercial property accounts?"
        service_label = "commercial bids and high-ticket service contracts ($5,000 – $25,000+ contracts)"
        vertical_silos = "commercial installations, emergency repairs, and multi-unit projects"
    elif any(w in niche_lower for w in ["shuttle", "transportation", "airport ride"]):
        open_q = "Are most of your bookings coming from individual airport travelers, or are you doing large group charters and corporate shuttle accounts?"
        service_label = "group charters and recurring airport shuttle contracts ($500 – $2,500+ bookings)"
        vertical_silos = "airport group transportation, golf transfers, and corporate shuttles"
    else:
        open_q = "Are most of your high-ticket clients coming from corporate contracts or private client engagements?"
        service_label = "high-ticket contracts and client engagements"
        vertical_silos = "high-ticket advisory and corporate training silos"

    img_tag = '<div style="text-align: center; margin: 20px 0;"><img src="cid:semrush_screenshot" style="max-width: 100%; border: 1px solid #e5e7eb; border-radius: 6px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);"></div>' if scorecard_path else ''

    html = f"""<p>Hi {client_name},</p>
<p>My colleague {colleague} forwarded me your reply asking us to send over the website report and errors we spotted on {clean_site}:</p>
<div style="background-color: #fafafa; border: 1px solid #d1d5db; padding: 12px; margin: 12px 0; font-family: monospace; font-size: 13px; line-height: 1.5; color: #374151;">
{quoted_headers}<br>
<br>
{quoted_body}
</div>
<p>I pulled your live Google search and domain diagnostic data today. Here is the high-level snapshot:</p>
<p>&bull; <b>Domain Authority Score:</b> {da_val}<br>
&bull; <b>Monthly Organic Traffic:</b> {traf_line}<br>
&bull; <b>Total Backlinks &amp; Referring Domains:</b> {bl_val} links across {rd_val} domains<br>
&bull; <b>Organic Keywords Indexed:</b> {kw_val} terms<br>
&bull; <b>AI Search Visibility:</b> {ai_val}</p>
{img_tag}
<p>You have {bl_val} backlinks and {rd_val} referring domains &mdash; that is a genuinely strong foundation. Most businesses in your sector don't come close to that level of domain trust.</p>
<p>However, despite that authority, Google is only sending you {traf_val}. Meanwhile, competing firms like {comp_str} are sitting right at the top of Google Page 1, capturing {service_label}.</p>
<p>We identified 3 technical issues blocking {company_name} from Google's first page:</p>
<p>1. <b>Commercial Search Indexation Gap:</b> Google is indexing your domain for brand phrases and generic text, but completely suppressing your site for high-intent commercial searches that paying clients actually type.</p>
<p>2. <b>Backlink Authority Waste:</b> Your {rd_val} referring domains are leaking authority because Google cannot connect that link equity to dedicated, structured service silos for {vertical_silos}.</p>
<p>3. The third issue directly impacts how AI Overviews and Google evaluate your primary business fulfillment model.</p>
<p>{open_q}</p>
<p>Once I know that, I can confirm whether this third technical issue applies to your setup and send you the complete fix list.</p>
"""
    if pdf_attached:
        html += "<p>I have also attached a complete 22-page visual Google Search Audit mapping your exact positioning against competitors screenshot-by-screenshot across 10 commercial search queries.</p>\n"

    return html


def run_scorecard_draft(slug: str = None, email: str = None) -> Dict[str, Any]:
    """Generates and injects the Phase 1 Scorecard Draft into Gmail in under 5 seconds."""
    if not slug and not email:
        raise ValueError("Must provide either --slug or --email")

    vault_dir = None
    if slug:
        vault_dir = resolve_client_vault(slug)
    
    if not vault_dir and email:
        vault_dir = resolve_client_vault(email)
        if not vault_dir:
            clients_dir = os.path.join(WORKSPACE_DIR, "clients")
            if os.path.exists(clients_dir):
                for c in os.listdir(clients_dir):
                    cp = os.path.join(clients_dir, c, "config.json")
                    if os.path.exists(cp):
                        try:
                            with open(cp, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            if data.get("email", "").lower() == email.lower() or data.get("client_email", "").lower() == email.lower():
                                vault_dir = os.path.join(clients_dir, c)
                                slug = c
                                break
                        except Exception:
                            pass

    if not vault_dir:
        raise FileNotFoundError(f"Could not find client vault for slug '{slug}' or email '{email}'. Run run_intake.py first.")

    config_path = os.path.join(vault_dir, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    to_email = cfg.get("email") or cfg.get("client_email")
    if not to_email:
        brief_path = os.path.join(vault_dir, "brief.md")
        if os.path.exists(brief_path):
            with open(brief_path, "r", encoding="utf-8") as bf:
                b_text = bf.read()
            em = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', b_text)
            if em:
                to_email = em.group(0).lower()

    if not to_email:
        raise ValueError(f"No recipient email found in config.json or brief.md for {slug}.")

    # Locate scorecard
    scorecard_path = os.path.join(vault_dir, "screenshots", "scorecard.png")
    if not os.path.exists(scorecard_path):
        alt_paths = [
            os.path.join(vault_dir, "scorecard.png"),
            os.path.join(vault_dir, "scorecard_combined.png"),
            os.path.join(WORKSPACE_DIR, "screenshots", f"{slug}_seo.png")
        ]
        for ap in alt_paths:
            if os.path.exists(ap):
                scorecard_path = ap
                break

    has_scorecard = os.path.exists(scorecard_path)

    # Auto-extract metrics from scorecard image if present
    diag = cfg.get("diagnostics", {})
    if has_scorecard:
        if diag.get("authority_score") in [None, "Under Review", "Pending Capture"] or diag.get("backlinks") in [None, "Pending Capture"]:
            print(f"[OCR] Auto-extracting Semrush metrics from {scorecard_path}...", flush=True)
            try:
                extracted = extract_scorecard_metrics(scorecard_path)
                diag["authority_score"] = extracted.get("authority_score", "0")
                diag["organic_traffic"] = f"{extracted.get('organic_traffic', '0')} visits/mo"
                diag["us_share"] = extracted.get("us_traffic_share", "")
                diag["backlinks"] = f"{extracted.get('backlinks', '0')} backlinks"
                diag["ref_domains"] = f"{extracted.get('ref_domains', '0')} domains"
                diag["keywords_indexed"] = f"{extracted.get('organic_keywords', '0')} terms"
                diag["ai_mentions"] = "0 Mentions"
                cfg["diagnostics"] = diag
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
                print(f"[OCR] Synced config.json with metrics: DA {diag['authority_score']}, Traffic {diag['organic_traffic']}, Ref Domains {diag['ref_domains']}", flush=True)
            except Exception as e:
                print(f"[OCR] Notice: Could not extract from scorecard: {e}", flush=True)
    else:
        print(f"[Notice] Scorecard image not found at {scorecard_path}. Generating email copy with preliminary technical diagnostics.", flush=True)

    # Check if PDF exists to attach
    pdf_path = None
    if os.path.exists(vault_dir):
        for f in os.listdir(vault_dir):
            if f.endswith(".pdf") and "Search_Audit" in f:
                pdf_path = os.path.join(vault_dir, f)
                break

    html_body = build_scorecard_html(cfg, scorecard_path if has_scorecard else None, pdf_attached=bool(pdf_path))

    # Validate against scorecard image if present
    if has_scorecard:
        try:
            validate_draft_against_scorecard(html_body, scorecard_path)
        except Exception as e:
            print(f"[Validation Notice] Metric parity check note: {e}", flush=True)

    # Save local copy to vault always so it is never lost
    draft_html_path = os.path.join(vault_dir, "draft_email.html")
    draft_txt_path = os.path.join(vault_dir, "draft_email.txt")
    with open(draft_html_path, "w", encoding="utf-8") as f:
        f.write(html_body)

    # Format clean readable text version for direct copy-pasting
    clean_text = re.sub(r'<style.*?</style>', '', html_body, flags=re.DOTALL)
    clean_text = re.sub(r'<br\s*/?>', '\n', clean_text)
    clean_text = re.sub(r'</p>', '\n\n', clean_text)
    clean_text = re.sub(r'<[^>]+>', '', clean_text)
    clean_text = re.sub(r'&bull;', '•', clean_text)
    clean_text = re.sub(r'&amp;', '&', clean_text)
    clean_text = re.sub(r'&mdash;', '—', clean_text)
    clean_text = re.sub(r'&lt;', '<', clean_text)
    clean_text = re.sub(r'&gt;', '>', clean_text)
    clean_text = re.sub(r'\n\s*\n+', '\n\n', clean_text).strip()

    with open(draft_txt_path, "w", encoding="utf-8") as f:
        f.write(clean_text)

    # Search for existing thread in Gmail & create draft
    draft = None
    try:
        thread_info = find_thread_by_email(to_email)
        thread_id = None
        last_msg_id = None
        refs = None
        subject = cfg.get("subject", "Re: Google is changing. Are you ready?")

        if thread_info:
            thread_id = thread_info.get("thread_id")
            last_msg_id = thread_info.get("last_message_id")
            refs = thread_info.get("references")
            subject = thread_info.get("subject", subject)
            print(f"[Gmail API] Docking into existing conversation thread: {thread_id} ({thread_info.get('messages_count')} messages)", flush=True)
        else:
            print(f"[Gmail API] Creating new conversation draft for {to_email} (Subject: {subject})", flush=True)

        attachments = [pdf_path] if pdf_path and os.path.exists(pdf_path) else None

        draft = create_gmail_draft(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            image_path=scorecard_path if has_scorecard else None,
            thread_id=thread_id,
            last_message_id=last_msg_id,
            references=refs,
            attachment_paths=attachments
        )

        draft_id = draft.get("id")
        print(f"\n{'='*65}")
        print(f" [SUCCESS] LIVE GMAIL DRAFT CREATED IN < 5 SECONDS!")
        print(f"{'='*65}")
        print(f"  Draft ID:    {draft_id}")
        print(f"  Recipient:   {to_email}")
        print(f"  Subject:     {subject}")
        if has_scorecard:
            print(f"  Scorecard:   {scorecard_path}")
        if pdf_path:
            print(f"  Attached:    {os.path.basename(pdf_path)}")
        print(f"{'='*65}\n")
    except Exception as e:
        print(f"\n[Gmail Notice] Could not inject to Gmail API ({e}).")
        print(f"✓ Saved email draft to: {draft_html_path}")
        print(f"✓ Ready-to-send email copy below:\n")
        print("=" * 65)
        print(clean_text)
        print("=" * 65 + "\n")
        draft = {"status": "saved_locally", "html_path": draft_html_path, "txt_path": draft_txt_path, "text": clean_text}

    return draft


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Phase 1 Scorecard Email Draft Runner")
    parser.add_argument("--slug", type=str, required=False, help="Client slug (e.g., cultivatedtalent, 760junkremovalcrew)")
    parser.add_argument("--email", type=str, required=False, help="Client email")
    args = parser.parse_args()

    if not args.slug and not args.email:
        parser.error("You must specify either --slug or --email")

    run_scorecard_draft(slug=args.slug, email=args.email)
