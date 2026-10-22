import os
import sys
import json
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

from src.keyword_audit_pipeline import KeywordAuditPipeline
from src.vault_manager import resolve_client_vault, ensure_client_vault
from src.lead_resolver import resolve_or_create_lead
from src.keyword_generator import generate_smart_keywords

ARCHIVE_CONFIGS_DIR = os.path.join(WORKSPACE_DIR, "archive", "legacy_configs")
ARCHIVE_KB_DIR = os.path.join(WORKSPACE_DIR, "archive", "legacy_kb_leads")
ARCHIVE_SCREENSHOTS_DIR = os.path.join(WORKSPACE_DIR, "archive", "legacy_screenshots")


def find_or_create_config(slug: str, force_recreate: bool = False) -> str:
    """Finds existing config or generates a standardized config JSON for the lead inside their vault."""
    # 1. Primary: check clients/{slug}/config.json via vault manager
    vault_dir = resolve_client_vault(slug)
    if vault_dir:
        client_vault_cfg = os.path.join(vault_dir, "config.json")
        if os.path.exists(client_vault_cfg) and not force_recreate:
            try:
                with open(client_vault_cfg, "r", encoding="utf-8") as f:
                    cfg_check = json.load(f)
                if cfg_check.get("keywords") and len(cfg_check["keywords"]) >= 10:
                    return client_vault_cfg
            except Exception:
                pass

    # 2. Fallback: check archive/legacy_configs/{slug}.json
    legacy_config = os.path.join(ARCHIVE_CONFIGS_DIR, f"{slug}.json")
    if os.path.exists(legacy_config) and not force_recreate:
        try:
            with open(legacy_config, "r", encoding="utf-8") as f:
                cfg_check = json.load(f)
            if cfg_check.get("keywords") and len(cfg_check["keywords"]) >= 10:
                return legacy_config
        except Exception:
            pass

    # Ensure vault exists
    target_vault = ensure_client_vault(slug)
    config_path = os.path.join(target_vault, "config.json")

    # Look for brief/knowledge base file
    kb_file = os.path.join(target_vault, "brief.md")
    if not os.path.exists(kb_file):
        legacy_kb = os.path.join(ARCHIVE_KB_DIR, f"{slug}.md")
        if os.path.exists(legacy_kb):
            kb_file = legacy_kb

    client_name = "Business Owner"
    company_name = slug.replace("_", " ").title()
    website = f"https://{slug}.com/"
    niche_text = ""
    location_text = ""

    if os.path.exists(kb_file):
        with open(kb_file, "r", encoding="utf-8") as f:
            content = f.read()
            name_m = re.search(r'(?:Client Contact Name|Decision Maker|First Name)[:\*\|\s]+([^\n\|(]+)', content)
            if name_m:
                client_name = name_m.group(1).strip()
            comp_m = re.search(r'(?:Company Name|Business Name)[:\*\|\s]+([^\n\|]+)', content)
            if comp_m:
                company_name = comp_m.group(1).strip()
            web_m = re.search(r'(?:Website|Domain)[:\*\|\s]+([^\n\|]+)', content)
            if web_m:
                raw_w = web_m.group(1).strip().replace(" ", "")
                if not raw_w.startswith("http"):
                    raw_w = "https://" + raw_w
                website = raw_w
            niche_m = re.search(r'(?:Niche|Industry|Services?)[:\*\|\s]+([^\n\|]+)', content)
            if niche_m:
                niche_text = niche_m.group(1).strip()
            loc_m = re.search(r'(?:Location|Service Market|Market|City|State)[:\*\|\s]+([^\n\|]+)', content)
            if loc_m:
                location_text = loc_m.group(1).strip()

    # Determine delivery model & clean niche
    is_virtual = any(w in (niche_text + " " + company_name).lower() for w in ["coach", "keynote", "speaker", "podcast", "author", "consultant", "virtual", "online", "advisory", "software", "saas"])
    model = "NATIONWIDE_VIRTUAL" if is_virtual else "LOCAL_IN_PERSON"

    clean_niche = ""
    if niche_text:
        first_clause = re.split(r'[,/|]', niche_text)[0].strip()
        first_clause = re.sub(r'^(Residential & Commercial|Commercial & Residential|Commercial|Residential)\s*', '', first_clause, flags=re.I).strip()
        clean_niche = first_clause
    if not clean_niche:
        clean_niche = company_name.lower().replace("crew", "").replace("services", "").replace("company", "").strip()

    base_city = ""
    regional_hubs = []
    if location_text:
        hubs_found = re.findall(r'([A-Z][a-zA-Z\s]+?)(?:,|\(|$)', location_text)
        cleaned_hubs = [h.strip().lower() for h in hubs_found if len(h.strip()) > 2 and h.strip().lower() not in ["valley", "county", "ca", "tx", "fl", "sc", "nc", "tn", "co"]]
        if cleaned_hubs:
            base_city = cleaned_hubs[0]
            regional_hubs = cleaned_hubs[1:]

    smart_keywords = generate_smart_keywords(
        company_name=company_name,
        niche=clean_niche,
        model=model,
        base_city=base_city,
        regional_hubs=regional_hubs
    )

    scorecard_img = os.path.join(target_vault, "screenshots", "scorecard.png")
    if not os.path.exists(scorecard_img):
        legacy_sc = os.path.join(ARCHIVE_SCREENSHOTS_DIR, f"{slug}_seo.png")
        if os.path.exists(legacy_sc):
            scorecard_img = legacy_sc
        else:
            scorecard_img = "assets/placeholder_scorecard.png"

    template_config = {
        "client_slug": slug,
        "client_name": client_name,
        "company_name": company_name,
        "website": website,
        "scorecard_image": scorecard_img,
        "diagnostics": {
            "authority_score": "15 / 100",
            "organic_traffic": "10 visits/mo",
            "us_share": "10 Visits / mo (5% US)",
            "backlinks": "250 Backlinks",
            "ref_domains": "45 Domains",
            "keywords_indexed": "15 Terms",
            "ai_mentions": "0 Mentions"
        },
        "keywords": smart_keywords
    }

    print(f"[CONFIG GENERATION] Synthesized 10 smart commercial keywords for {slug} at {config_path}", flush=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(template_config, f, indent=2)

    return config_path


def generate_phase5_email_copy(cfg: dict, pdf_path: str) -> str:
    """Generates the standardized Phase 5 email draft copy matching Section 5 of audit_pipeline_implementation_plan.md."""
    client_name = cfg.get("client_name", "there").strip().split()[0]
    company_name = cfg.get("company_name", "your business")
    keywords = cfg.get("keywords", [])
    
    # Competitor & Cities
    top_comp = "your primary local competitors"
    first_kw_comps = keywords[0].get("competitors", []) if keywords else []
    if first_kw_comps and first_kw_comps[0].get("title"):
        top_comp = first_kw_comps[0]["title"]

    # Extract distinct cities/corridors from keywords
    cities = []
    for k in keywords:
        words = k["phrase"].split()
        if len(words) >= 2:
            potential_city = words[-2].title() if words[-1].lower() in ["tx", "fl", "ca", "nc", "tn", "co", "ny", "ga", "oh", "qc"] else words[-1].title()
            if potential_city not in cities and len(potential_city) > 2:
                cities.append(potential_city)
    cities_str = ", ".join(cities[:3]) if cities else "your primary regional markets"

    # Primary technical flaw
    has_forensic = bool(cfg.get("forensic_page"))
    total_pages = 23 if has_forensic else 22
    
    fp_conf = cfg.get("forensic_page", {})
    if fp_conf.get("flaw_summary"):
        flaw_text = fp_conf["flaw_summary"]
    elif has_forensic:
        flaw_text = "almost all your pages are static HTML, and your entire blog is just 5 articles dumped onto a single page without unique URLs or schema markup. Google cannot index individual articles or service pages from a single page, so nobody searching Google will ever see what you offer"
    else:
        flaw_text = "your website lacks dedicated, crawlable commercial landing pages and structured entity schema markup. Because Google cannot connect your domain authority to individual high-intent buyer searches, your site remains suppressed on Page 2 and Page 3"

from src.email_generator import generate_track_a_diagnostic, generate_track_b_executive, format_anti_autolink


def generate_phase5_email_copy(cfg: dict, pdf_path: str) -> str:
    """Generates both Track A (Technical Diagnostic) and Track B (Executive Pitch)."""
    client_name = cfg.get("client_name", "Business Owner")
    company_name = cfg.get("company_name", "Company")
    website = cfg.get("website", "")
    diagnostics = cfg.get("diagnostics", {})
    keywords = cfg.get("keywords", [])
    packages = cfg.get("packages", [])
    op_model = cfg.get("operational_model", {}).get("model", "HYBRID")

    # Find top competitors from pipeline or keywords
    comps = []
    for k in keywords:
        tag = k.get("tag", "")
        if "vs" in tag.lower():
            comps.append(tag.split("vs")[-1].strip(" .()"))
    if not comps:
        comps = ["top competitors"]

    # Dynamically resolve outreach colleague
    colleague = cfg.get("outreach_colleague") or cfg.get("colleague")
    if not colleague:
        vault_dir = resolve_client_vault(cfg.get("client_slug", ""))
        if vault_dir:
            b_path = os.path.join(vault_dir, "brief.md")
            if os.path.exists(b_path):
                with open(b_path, "r", encoding="utf-8") as bf:
                    b_text = bf.read()
                cm = re.search(r'(?:Outreach Colleague|Colleague)[:\*\|\s]+([^\n\|]+)', b_text)
                if cm:
                    colleague = cm.group(1).split()[0].strip(" `()\"'")
    if not colleague:
        colleague = "Nancy"

    # Tailor open loop question
    niche_lower = (company_name + " " + " ".join([k.get("phrase", "") for k in keywords[:3]])).lower()
    if any(w in niche_lower for w in ["recruit", "search", "talent", "headhunt"]):
        open_q = "Are most of your retained searches coming from independent/indie brands, or are you primarily placing C-suite leaders into established corporate conglomerates?"
        service_label = "retained search"
    elif any(w in niche_lower for w in ["junk", "haul", "cleanout", "roof", "plumb", "contractor", "shuttle"]):
        open_q = "Are most of your projects coming directly from residential homeowners, or are you pulling significant volume from commercial property accounts?"
        service_label = "commercial contract"
    else:
    quoted_headers = cfg.get("quoted_headers") or f"----- Original Message -----\nFrom: {client_name}\nTo: {colleague}"
    quoted_body = cfg.get("quoted_body") or "Sure, send over the report."

    track_a = generate_track_a_diagnostic(
        client_name=client_name,
        colleague_name=colleague,
        quoted_headers=quoted_headers,
        quoted_body=quoted_body,
        website=website,
        diagnostics=diagnostics,
        real_competitors=comps,
        open_loop_question=open_q,
        service_type=service_label
    )

    track_b = generate_track_b_executive(
        client_name=client_name,
        colleague_name=colleague,
        quoted_headers=quoted_headers,
        quoted_body=quoted_body,
        company_name=company_name,
        packages=packages,
        competitors=comps,
        delivery_scope="nationwide across the United States" if op_model in ["NATIONWIDE_VIRTUAL", "HYBRID"] else "across your regional market",
        service_label=service_label
    )

    output = f"""
================================================================================
TRACK A: TECHNICAL DIAGNOSTIC / OPEN LOOP FORMAT (Best for Contractors/Trade Leads)
================================================================================
{track_a}

================================================================================
TRACK B: EXECUTIVE & HIGH-TICKET PITCH (Best for Coaches/Founders/CEOs)
================================================================================
{track_b}
"""
    return output


def main():
    parser = argparse.ArgumentParser(description="Master Single-Command Search Audit Runner")
    parser.add_argument("--slug", type=str, required=False, help="Client slug (e.g., fenceinvestments, smrrental)")
    parser.add_argument("--email", type=str, required=False, help="Client email (e.g., justaskkevintoo@gmail.com)")
    parser.add_argument("--query", type=str, required=False, help="Search query (contact name, company, or domain)")
    parser.add_argument("--force", action="store_true", help="Force re-capture of all screenshots from scratch")
    parser.add_argument("--no-draft", action="store_true", help="Skip automatic Gmail draft creation")
    args = parser.parse_args()

    slug = args.slug
    config_path = None

    if not slug:
        lookup = args.email or args.query
        if not lookup:
            parser.error("You must specify either --slug, --email, or --query.")
        lead_info = resolve_or_create_lead(lookup)
        slug = lead_info["slug"]
        config_path = lead_info["config_path"]
    else:
        config_path = find_or_create_config(slug)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    if not cfg.get("keywords") or len(cfg["keywords"]) < 10:
        print(f"[NOTICE] Config lacks 10 commercial keywords. Auto-generating smart matrix for {slug}...", flush=True)
        config_path = find_or_create_config(slug, force_recreate=True)
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

    print(f"\n=======================================================")
    print(f"  RUNNING UNIFIED SEARCH AUDIT PIPELINE: {slug.upper()}")
    print(f"=======================================================\n")

    pipeline = KeywordAuditPipeline(cfg, force_capture=args.force)
    pipeline.run_pipeline()

    pdf_path = pipeline.output_pdf
    print(f"\n[SUCCESS] Master PDF Ready: {pdf_path}")
    print(f"File Size: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB")

    try:
        from src.proof_sheet_generator import generate_proof_sheet
        proof_path = generate_proof_sheet(pdf_path, cfg)
        print(f"[SUCCESS] 1-Page Visual Proof Sheet Ready: {proof_path}")
    except Exception as e:
        print(f"[NOTICE] Proof sheet generation skipped: {e}")

    email_copy = generate_phase5_email_copy(cfg, pdf_path)
    print("\n" + "="*50)
    print("PHASE 5 EMAIL DRAFT COPY (READY TO SEND):")
    print("="*50)
    print(email_copy)
    print("="*50 + "\n")

    if not args.no_draft:
        try:
            from run_scorecard_draft import run_scorecard_draft
            print(f"[AUTO-DRAFT] Injecting live draft with PDF attachment into Gmail...", flush=True)
            run_scorecard_draft(slug=slug)
        except Exception as e:
            print(f"[NOTICE] Auto-draft creation skipped or encountered warning: {e}", flush=True)


if __name__ == "__main__":
    main()
