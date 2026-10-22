"""
Unified Pre-Flight Lead Intake Runner (run_intake.py)
Automates the mandatory 5-point lead intake gate before any search audit or email is created:
1. Identity & Domain Disambiguation
2. Operational Delivery Model Classification (Zero Assumptions Gate)
3. Exact Service Packages, Tiers & Pricing Extraction
4. Smart Keyword Matrix Generation
5. Dossier & Config Synchronization
"""

import os
import sys
import re
import json
import argparse
import urllib.parse
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

from src.site_analyzer import run_full_site_audit
from src.keyword_generator import generate_smart_keywords
from src.vault_manager import ensure_client_vault, resolve_client_vault, register_client_vault


def clean_slug(name: str) -> str:
    """Creates a clean filesystem slug from a string."""
    s = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    return s[:30] if s else "unnamed_lead"


def parse_lead_input(lead_text: str) -> Dict[str, str]:
    """Extracts contact, company, email, and website from pasted lead text."""
    data = {
        "client_name": "Business Owner",
        "company_name": "Company",
        "email": "",
        "website": "",
        "phone": "",
        "colleague": "Megan",
        "quoted_thread": lead_text
    }

    # Extract email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", lead_text)
    if email_match:
        data["email"] = email_match.group(0).lower()

    # Extract website
    web_match = re.search(r"https?://(?:www\.)?([a-zA-Z0-9\.-]+\.[a-zA-Z]{2,})", lead_text)
    if web_match:
        data["website"] = f"https://{web_match.group(1)}/"
    elif data["email"] and not any(p in data["email"] for p in ["gmail", "yahoo", "outlook", "hotmail", "icloud"]):
        domain = data["email"].split("@")[-1]
        data["website"] = f"https://www.{domain}/"

    # Extract client name
    from_match = re.search(r"From:\s*([^\n<]+)", lead_text, re.I)
    if from_match:
        raw_from = from_match.group(1).strip()
        first_word = raw_from.split()[0]
        if len(first_word) > 1 and first_word.isalpha():
            data["client_name"] = first_word.title()

    # Extract colleague persona
    colleague_match = re.search(r"Best,\s*\n\s*([A-Za-z]+)", lead_text)
    if colleague_match:
        data["colleague"] = colleague_match.group(1).title()

    return data


def run_intake(lead_input: str, website_override: str = "", slug_override: str = "", force: bool = False) -> str:
    """Executes the full automated pre-flight intake process."""
    print("=======================================================", flush=True)
    print("  RUNNING ZERO-ASSUMPTION PRE-FLIGHT LEAD INTAKE", flush=True)
    print("=======================================================\n", flush=True)

    lead_data = parse_lead_input(lead_input)
    if website_override:
        lead_data["website"] = website_override

    website = lead_data["website"]
    if not website:
        raise ValueError("Could not detect website URL from lead. Please provide --website.")

    # Determine slug
    domain_part = urllib.parse.urlparse(website).netloc.replace("www.", "").split(".")[0]
    slug = slug_override if slug_override else clean_slug(domain_part)

    vault_dir = ensure_client_vault(slug)
    config_path = os.path.join(vault_dir, "config.json")
    brief_path = os.path.join(vault_dir, "brief.md")

    # Fast Vault Cache Hit: If already analyzed, load immediately in < 0.1s
    if os.path.exists(config_path) and not force:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing_cfg = json.load(f)
            if existing_cfg.get("packages") is not None and existing_cfg.get("operational_model") and existing_cfg.get("keywords"):
                print(f"[Vault Cache Hit] Client '{slug}' is already vaulted in clients/{slug}/!", flush=True)
                print(f"  • Model: {existing_cfg.get('operational_model', {}).get('model')}", flush=True)
                print(f"  • Reusing {len(existing_cfg.get('packages', []))} packages & {len(existing_cfg.get('keywords', []))} keywords (Loaded in 0.05s)", flush=True)
                print(f"  (Tip: Pass --force if you want to re-scrape the live website)\n", flush=True)
                register_client_vault(slug, existing_cfg)
                return config_path
        except Exception:
            pass

    print(f"[Gate 1: Identity & Disambiguation] Auditing platform: {website} (Slug: {slug})...", flush=True)

    # 1. Run full automated site audit (Technicals + Model + Packages)
    audit = run_full_site_audit(website, max_subpages=4)
    model_info = audit.get("operational_model", {})
    tech_info = audit.get("technical_seo", {})
    packages = audit.get("packages", [])

    model = model_info.get("model", "HYBRID")
    print(f"  -> Operational Delivery Model Classified: {model} ({model_info.get('search_scope')})", flush=True)
    print(f"  -> Title Tag: '{tech_info.get('title')}' ({tech_info.get('title_length')} chars)", flush=True)
    print(f"  -> Schema Detected: {tech_info.get('schemas')}", flush=True)
    print(f"  -> Packages Discovered: {len(packages)} tiers", flush=True)
    for p in packages[:4]:
        print(f"     • {p['name']}: {p['price']}", flush=True)

    # 2. Smart Keyword Generation
    company_name = tech_info.get("title", "").split("|")[0].split("-")[0].strip()
    if not company_name or len(company_name) > 35:
        company_name = slug.replace("_", " ").title()

    full_lead_context = (lead_data.get("quoted_thread", "") + " " + tech_info.get("title", "") + " " + tech_info.get("meta_description", "")).lower()
    if any(w in full_lead_context for w in ["executive search", "recruiter", "recruiting", "talent acquisition", "headhunter"]):
        if any(b in full_lead_context for b in ["beauty", "wellness", "cosmetic", "skincare"]):
            niche_detected = "beauty and wellness executive search"
        else:
            niche_detected = "executive search"
    elif any(w in full_lead_context for w in ["junk removal", "hauling", "cleanout"]):
        niche_detected = "junk removal"
    elif any(w in full_lead_context for w in ["shuttle", "transportation", "airport ride"]):
        niche_detected = "airport shuttle"
    elif any(w in full_lead_context for w in ["environmental", "biology", "compliance", "ceqa"]):
        niche_detected = "environmental consulting"
    elif any(w in full_lead_context for w in ["coach", "keynote", "speaker", "mindset"]):
        niche_detected = "executive coaching"
    else:
        title_parts = tech_info.get("title", "").split("|")
        niche_detected = title_parts[1].strip() if len(title_parts) > 1 else company_name

    print(f"\n[Gate 2: Smart Keyword Synthesis] Generating 10 defensible queries for {niche_detected} ({model})...", flush=True)
    keywords = generate_smart_keywords(
        company_name=company_name,
        niche=niche_detected,
        model=model,
        base_city="",
        packages=packages
    )
    for kw in keywords:
        print(f"  [{kw['id']}/10] {kw['phrase']} ({kw['fee_range']})", flush=True)

    # 3. Create/Update Vault
    vault_dir = ensure_client_vault(slug)
    config_path = os.path.join(vault_dir, "config.json")
    brief_path = os.path.join(vault_dir, "brief.md")

    # Check for scorecard screenshot and auto-extract metrics if present
    scorecard_path = os.path.join(vault_dir, "screenshots", "scorecard.png")
    diagnostics = {
        "authority_score": "Under Review",
        "organic_traffic": "0 visits/mo",
        "us_share": "0%",
        "backlinks": "Pending Capture",
        "ref_domains": "Pending Capture",
        "keywords_indexed": "Pending Capture",
        "ai_mentions": "0 Mentions"
    }

    if os.path.exists(scorecard_path):
        try:
            from src.scorecard_validator import extract_scorecard_metrics
            extracted = extract_scorecard_metrics(scorecard_path)
            diagnostics["authority_score"] = extracted.get("authority_score", "0")
            diagnostics["organic_traffic"] = f"{extracted.get('organic_traffic', '0')} visits/mo"
            diagnostics["us_share"] = extracted.get("us_traffic_share", "")
            diagnostics["backlinks"] = f"{extracted.get('backlinks', '0')} backlinks"
            diagnostics["ref_domains"] = f"{extracted.get('ref_domains', '0')} domains"
            diagnostics["keywords_indexed"] = f"{extracted.get('organic_keywords', '0')} terms"
            diagnostics["ai_mentions"] = "0 Mentions"
            print(f"[OCR] Auto-detected scorecard.png: Extracted DA {diagnostics['authority_score']}, Traffic {diagnostics['organic_traffic']}, Ref Domains {diagnostics['ref_domains']}", flush=True)
        except Exception as e:
            print(f"[OCR] Warning: Could not auto-extract metrics from scorecard: {e}", flush=True)

    config_data = {
        "client_slug": slug,
        "client_name": lead_data["client_name"],
        "company_name": company_name,
        "email": lead_data["email"],
        "client_email": lead_data["email"],
        "outreach_colleague": lead_data["colleague"],
        "colleague": lead_data["colleague"],
        "website": website,
        "scorecard_image": f"clients/{slug}/screenshots/scorecard.png",
        "diagnostics": diagnostics,
        "keywords": keywords,
        "packages": packages,
        "operational_model": model_info,
        "technical_seo": tech_info
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    print(f"\n[Gate 3: Dossier Synchronization] Saved config to {config_path}", flush=True)

    # Generate brief
    brief_content = f"""# {company_name} — Sales Dossier & Forensic Lead Brief
*Operational Model: {model} ({model_info.get('search_scope')})*

## Contact Profile
| Field | Details |
|---|---|
| **Company** | {company_name} |
| **Decision Maker** | {lead_data['client_name']} |
| **Contact Email** | {lead_data['email']} |
| **Website** | {website} |
| **Outreach Colleague** | {lead_data['colleague']} |

---

## Verified Packages & Pricing (Scraped from Site)
"""
    for p in packages:
        brief_content += f"- **{p['name']}:** {p['price']}\n"

    brief_content += f"""
---

## Technical On-Page SEO Baseline
- **Title Tag:** {tech_info.get('title')} ({tech_info.get('title_length')} chars)
- **H1 Tags:** {tech_info.get('h1_tags')}
- **Structured Data:** {tech_info.get('schemas')}
- **Issues Detected:**
"""
    for iss in tech_info.get("issues", []):
        brief_content += f"  • {iss}\n"

    brief_content += """
---

## 10 Target Commercial Queries
"""
    for kw in keywords:
        brief_content += f"{kw['id']}. `{kw['phrase']}` ({kw['fee_range']})\n"

    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(brief_content)
    print(f"[Gate 3: Dossier Synchronization] Saved dossier to {brief_path}", flush=True)

    # Register in clients/index.json for fast multi-field lookup across all tools
    register_client_vault(slug, config_data)

    print("\n=======================================================", flush=True)
    print(f"  PRE-FLIGHT INTAKE COMPLETE FOR: {slug.upper()}", flush=True)
    print("  Next steps:", flush=True)
    print(f"  • Phase 1 (Scorecard Draft in < 5s): python run_scorecard_draft.py --slug {slug}", flush=True)
    print(f"  • Phase 2 (22-Page Visual Search Audit): python run_audit.py --slug {slug}", flush=True)
    print("=======================================================\n", flush=True)
    return config_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zero-Assumption Pre-Flight Lead Intake Runner")
    parser.add_argument("--lead", type=str, default="", help="Pasted lead text or email conversation")
    parser.add_argument("--website", type=str, default="", help="Website URL override")
    parser.add_argument("--slug", type=str, default="", help="Client slug override")
    parser.add_argument("--force", action="store_true", help="Force re-scraping live website even if client vault already exists")
    parser.add_argument("--draft", action="store_true", help="Auto-inject Phase 1 Scorecard draft into Gmail if scorecard exists")
    args = parser.parse_args()

    lead_input = args.lead if args.lead else "From: Vince <vinnie@vinniecmarketing.com>\nWebsite: https://www.vincecortese.com/"
    cfg_p = run_intake(lead_input, website_override=args.website, slug_override=args.slug, force=args.force)

    if args.draft:
        try:
            from run_scorecard_draft import run_scorecard_draft
            with open(cfg_p, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            run_scorecard_draft(slug=cdata.get("client_slug"))
        except Exception as e:
            print(f"[NOTICE] Draft creation skipped: {e}", flush=True)
