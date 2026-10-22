"""Master Executive Proposal Pipeline (SOP 9)
Generates 100% pixel-perfect, mistake-free, white-label client proposals in PDF format.
Streamlined, executive-ready 8-page architecture with modern typography, elevated visual design,
dynamic tech-collaboration support, and zero premature pricing on the cover page.

Usage:
    python run_proposal.py --slug blueoasis
    python run_proposal.py --slug ecosystemsnorthwest
    python run_proposal.py --config clients/blueoasisglobal/proposal_config.json
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def resolve_client_vault(slug_or_name: str) -> Path:
    if not slug_or_name:
        return None
    direct = WORKSPACE_ROOT / "clients" / slug_or_name
    if direct.exists() and direct.is_dir():
        return direct
    idx_path = WORKSPACE_ROOT / "clients" / "index.json"
    if idx_path.exists():
        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                idx = json.load(f)
            q = slug_or_name.lower().replace(" ", "").replace("_", "").replace("-", "")
            for s, d in idx.items():
                s_clean = s.replace("_", "").replace("-", "")
                if q == s_clean or q in s_clean or s_clean in q:
                    candidate = WORKSPACE_ROOT / d["folder"]
                    if candidate.exists() and candidate.is_dir():
                        return candidate
        except Exception:
            pass
    return None

def sanitize_client_vault(vault_dir: Path):
    """Strict vault hygiene guardrail: Purges any unauthorized temporary previews, renders, or HTML files
    while 100% protecting permanent client assets.
    """
    import shutil
    if not vault_dir or not vault_dir.exists():
        return

    for item in list(vault_dir.iterdir()):
        if item.is_dir():
            if item.name == "screenshots":
                for s_file in list(item.iterdir()):
                    if s_file.name.endswith("_full_raw.png") or s_file.name.endswith(".html") or s_file.name.startswith("temp"):
                        try:
                            s_file.unlink()
                            print(f"  [Vault Sanitizer] Purged temporary asset: {s_file.name}")
                        except Exception:
                            pass
            elif item.name.startswith("preview") or item.name.startswith("v2_") or item.name.startswith("temp") or "render" in item.name:
                try:
                    shutil.rmtree(item)
                    print(f"  [Vault Sanitizer] Purged unauthorized directory: {item.name}")
                except Exception:
                    pass
        elif item.is_file():
            if item.suffix.lower() == ".html" or item.name.startswith("page_") or item.name.startswith("temp") or item.name.startswith("scratch"):
                try:
                    item.unlink()
                    print(f"  [Vault Sanitizer] Purged unauthorized file: {item.name}")
                except Exception:
                    pass

def load_config(config_path_or_slug: str) -> dict:
    p = Path(config_path_or_slug)
    if not p.exists():
        vault = resolve_client_vault(config_path_or_slug)
        if vault and (vault / "proposal_config.json").exists():
            p = vault / "proposal_config.json"
        else:
            candidate = WORKSPACE_ROOT / "configs" / "proposals" / f"{config_path_or_slug}.json"
            if candidate.exists():
                p = candidate
            else:
                raise FileNotFoundError(f"Proposal config not found: {config_path_or_slug}")
    
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def validate_config_guardrails(cfg: dict):
    """Strict programmatic gate ensuring zero unverified guesses, correct roadmap phasing, and clean tables."""
    required_keys = ["client_name", "client_company", "client_website", "packages", "technical_audit", "keyword_clusters"]
    for k in required_keys:
        if k not in cfg:
            raise ValueError(f"Proposal config missing required field: {k}")

    raw_str = json.dumps(cfg)
    if "approximate 12" in raw_str.lower() or "12-person" in raw_str.lower():
        raise ValueError("Guardrail Violation: Detected hardcoded '12-person' / '12 guests'. Client cohort sizes must be dynamic or generalized to 'intimate executive cohorts'.")

    issues = cfg.get("technical_audit", {}).get("issues", [])
    if len(issues) < 4:
        raise ValueError("Proposal requires at least 4 technical audit issues to justify agency intervention.")

    pkg = cfg.get("packages", {})
    is_single_plan = cfg.get("single_plan_only", False) or "professional" not in pkg
    if is_single_plan:
        if "standard" not in pkg:
            raise ValueError("Proposal in single plan mode must specify 'standard' package.")
    else:
        if "standard" not in pkg or "professional" not in pkg:
            raise ValueError("Proposal must specify both 'standard' and 'professional' packages.")

    print("[SUCCESS] All pre-flight proposal guardrails passed.")

def build_proposal_html(cfg: dict) -> str:
    logo_path = WORKSPACE_ROOT / "assets" / "innovate_logo.png"
    if not logo_path.exists():
        raise FileNotFoundError(f"Innovate logo missing at {logo_path}")
    
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")
    logo_src = f"data:image/png;base64,{logo_b64}"

    curr = cfg.get("currency", "USD")
    curr_sym = cfg.get("currency_symbol", "$")
    is_single_plan = cfg.get("single_plan_only", False) or "professional" not in cfg.get("packages", {})
    is_onetime = cfg.get("is_onetime", False) or cfg.get("packages", {}).get("standard", {}).get("is_onetime", False)
    price_suffix = "One-Time Flat Investment" if is_onetime else "/ month"
    badge_default = "Fixed-Price • One-Time" if is_onetime else "Month-to-Month • No Contract"
    
    std = cfg["packages"]["standard"]
    pro = cfg["packages"].get("professional", {})
    strat = cfg.get("strategic_vision", {})
    tech = cfg.get("technical_audit", {})
    
    # In-House Dev vs Knowledge Transfer vs 100% Turnkey Execution
    dev = cfg.get("in_house_dev", {"has_dev": False, "savings_cad_month": 0})
    has_dev = dev.get("has_dev", False)
    is_kt = dev.get("is_knowledge_transfer", False)
    
    clusters = cfg.get("keyword_clusters", [])

    # Format Keyword Clusters
    cluster_cards_html = ""
    for c in clusters:
        bullets = "".join([f"<li>{k}</li>" for k in c.get("keywords", [])])
        cluster_cards_html += f"""
        <div class="card-tinted" style="border-left: 3.5px solid {c.get('color', '#0284c7')};">
          <div style="font-size: 11px; font-weight: 800; color: {c.get('color', '#0284c7')}; text-transform: uppercase; letter-spacing: 0.5px;">{c.get('title', c.get('name', 'Keyword Cluster'))}</div>
          <div style="font-size: 10px; color: #64748b; margin-bottom: 8px;">{c.get('subtitle', '')}</div>
          <ul class="check-list">
            {bullets}
          </ul>
        </div>
        """

    # Capability Pills
    if has_dev:
        collab_pill_title = "DEV SYNERGY"
        collab_pill_desc = "In-House Tech Credit"
    elif is_kt:
        collab_pill_title = "KNOWLEDGE TRANSFER"
        collab_pill_desc = "Hands-On DIY Training"
    else:
        collab_pill_title = "TURNKEY EXECUTION"
        collab_pill_desc = "100% Agency Deployment"

    pills = cfg.get("capability_pills", [
        {"title": "GOOGLE SEARCH", "desc": "High-Intent Discovery"},
        {"title": "AI & CHATGPT", "desc": "Answer Engine Recommendations"},
        {"title": "GOOGLE MAPS", "desc": "Local Search & Trust Profile"},
        {"title": collab_pill_title, "desc": collab_pill_desc}
    ])
    pills_html = "".join([f"""
    <div class="capability-item">
      <div class="capability-title">{p['title']}</div>
      <div class="capability-desc">{p['desc']}</div>
    </div>
    """ for p in pills])

    # Growth Pillar 4 on Page 2
    if has_dev:
        pillar4_title = "4. In-House Developer Synergy"
        pillar4_sub = "(Collaborative Workflow & Direct Savings)"
        pillar4_desc = f"We supply clear code instructions to your developer. They make internal updates; we handle marketing and off-page authority—saving you {curr_sym}{dev.get('savings_cad_month', 580)} {curr} every month."
    elif is_kt:
        pillar4_title = "4. Hands-On Knowledge Transfer"
        pillar4_sub = "(Collaborative DIY Guidance)"
        pillar4_desc = "We share screens and guide you through managing content, understanding analytics, and deploying AI workflows—empowering your practice with zero long-term contract lock-in."
    else:
        pillar4_title = "4. Turnkey Engineering Execution"
        pillar4_sub = "(100% Agency Deployment)"
        pillar4_desc = "Innovate Marketers handles 100% of server configurations, SSL security, robots directives, sitemaps, and Schema markup directly. Zero coding or technical burden required from your team."

    # Format Diagnostic Issues into High-Impact Cards for Page 3
    tech_cards_html = ""
    issues = tech.get("issues", [])
    badge_colors = ["badge-rose", "badge-amber", "badge-rose", "badge-teal", "badge-amber", "badge-teal"]
    badge_labels = ["CRITICAL LEAK", "INDEXATION FLAW", "SECURITY RISK", "TRACKING GAP", "AI BLINDSPOT", "STRUCTURE ISSUE"]
    
    for idx, item in enumerate(issues[:4]):
        b_color = badge_colors[idx % len(badge_colors)]
        b_label = badge_labels[idx % len(badge_labels)]
        tech_cards_html += f"""
        <div class="card-tinted" style="border-left: 3.5px solid {'#e11d48' if 'rose' in b_color else ('#d97706' if 'amber' in b_color else '#0284c7')};">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 12px; font-weight: 800; color: #0b2545;">{item['name']}</span>
            <span class="badge {b_color}">{b_label}</span>
          </div>
          <div style="font-size: 9.5px; font-weight: 600; color: #64748b; margin-bottom: 5px;">TECHNICAL RECTIFICATION: {item['tech']}</div>
          <div style="font-size: 11px; color: #334155; line-height: 1.45;">
            {item['impact']}
          </div>
        </div>
        """

    # Page 4: Dynamic Execution Architecture
    if has_dev:
        page4_tag = "03 / DEVELOPER COLLABORATION MATRIX"
        page4_title = "How We Work Together with Your In-House Web Developer"
        page4_subtitle = "A clear division of labor that saves you money by letting your developer handle direct code updates."
        page4_intro = f"You made it clear during our call that you have your own IT/developer and don't want to pay an agency for tasks already covered in-house. <strong>We completely support this.</strong> Below is the exact matrix showing how we divide tasks so your developer has zero guesswork, while Innovate Marketers handles strategy, content, authority, and AI search visibility:"
        
        collab = cfg.get("collaboration_matrix", {})
        collab_rows = collab.get("rows", [
            {"task": "1. 301 Redirection & URLs", "client": "Pastes our 301 redirect code into your server settings (.htaccess/Nginx). Takes 10 minutes.", "agency": "Writes the exact code snippet, tests URL combinations, and verifies in Search Console."},
            {"task": "2. Meta Titles & Snippets", "client": "Pastes pre-written page titles and descriptions into your CMS headers.", "agency": "Researches and authors high-converting, click-optimized preview copy for all core pages."},
            {"task": "3. Heading Hierarchy (H1-H3)", "client": "Adjusts heading tags in page templates to follow sequential order.", "agency": "Provides a page-by-page heading blueprint with exact wording and commercial keywords."},
            {"task": "4. Sitemaps & Robots.txt", "client": "Uploads the generated robots.txt file to your web root directory.", "agency": "Builds the XML sitemap, sets crawl priority rules, and submits to Google and Bing."},
            {"task": "5. Email Security & DNS", "client": "Adds a simple TXT line to your domain DNS settings and renews SSL certificate.", "agency": "Provides the exact DMARC text string to eliminate spoofing and improve deliverability."},
            {"task": "6. Google Analytics 4 Setup", "client": "Embeds the GA4 measurement tag inside the site <head> code.", "agency": "Configures conversion tracking (inquiry clicks, calls) and builds executive dashboard."},
            {"task": "7. AI Structured Data (Schema)", "client": "Pastes our custom JSON code blocks into the target service pages.", "agency": "Writes specialized Schema.org code feeding AI bots exact locations, pricing, and services."},
            {"task": "8. Off-Page Authority & PR", "client": "Zero developer time required. (100% off-site execution).", "agency": "Publishes 150–250 monthly authority backlinks, guest articles, and Google Maps optimization."}
        ])
        
        rows_html = "".join([f"""
        <tr>
          <td style="padding: 7px 11px;"><strong>{r['task']}</strong></td>
          <td style="padding: 7px 11px;">{r['client']}</td>
          <td style="padding: 7px 11px;">{r['agency']}</td>
        </tr>
        """ for r in collab_rows])
        
        page4_body = f"""
        <div style="font-size: 11.5px; color: #1e293b; line-height: 1.5; margin-bottom: 10px;">
          {page4_intro}
        </div>
        <table class="data-table" style="font-size: 10px; margin-bottom: 12px;">
          <thead>
            <tr>
              <th style="width: 24%; padding: 8px 10px;">TASK AREA</th>
              <th style="width: 38%; padding: 8px 10px;">WHAT YOUR IN-HOUSE DEVELOPER DOES<br><span style="font-weight: 400; text-transform: none; color: #93c5fd;">(Direct Server & Code Implementation)</span></th>
              <th style="width: 38%; padding: 8px 10px;">WHAT INNOVATE MARKETERS DELIVERS<br><span style="font-weight: 400; text-transform: none; color: #93c5fd;">(Strategy, Content, AI Optimization & Off-Page)</span></th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
        <div class="card-highlight" style="padding: 10px 15px;">
          <div style="font-size: 11px; font-weight: 800; color: #0b2545; margin-bottom: 2px;">WHY THIS SAVES YOU MONEY</div>
          <div style="font-size: 10.5px; color: #0369a1; line-height: 1.45;">
            These technical fixes take your developer roughly 3 to 4 hours total. By not having an agency charge you for coding hours, <strong>you save over {curr_sym}{dev.get('savings_cad_month', 580)} {curr} every single month</strong> while getting world-class SEO and AI visibility.
          </div>
        </div>
        """
    elif is_kt:
        page4_tag = "03 / KNOWLEDGE TRANSFER & WORKFLOW"
        page4_title = "Hands-On Knowledge Transfer & Collaborative Guidance"
        page4_subtitle = "A collaborative workflow empowering your DIY approach with direct training, technical guidance, and agency execution."
        page4_body = f"""
        <div style="font-size: 11.5px; color: #1e293b; line-height: 1.55; margin-bottom: 12px;">
          During our strategy session, you expressed a clear desire for <strong>hands-on knowledge transfer</strong> so you understand every lever being pulled. We believe in total empowerment: we do not hold your website hostage behind technical jargon.
        </div>
        <div class="grid-2" style="margin-bottom: 12px;">
          <div class="card" style="border-top: 3.5px solid #0284c7; padding: 12px 14px;">
            <div style="font-size: 12px; font-weight: 800; color: #0b2545; margin-bottom: 6px;">HANDS-ON WORKING SESSIONS</div>
            <div style="font-size: 11px; color: #334155; line-height: 1.45;">
              Whenever we meet, our project team provides direct screen-share working sessions. We walk through Google Search Console insights, blog and content architecture, and AI automation workflows so you gain complete mastery.
            </div>
          </div>
          <div class="card" style="border-top: 3.5px solid #059669; padding: 12px 14px;">
            <div style="font-size: 12px; font-weight: 800; color: #0b2545; margin-bottom: 6px;">AGENCY HEAVY LIFTING</div>
            <div style="font-size: 11px; color: #334155; line-height: 1.45;">
              While we guide you on content, our technical specialists execute the off-page authority: acquiring high-authority backlinks, securing third-party guest articles, and submitting structured schema to search algorithms.
            </div>
          </div>
        </div>
        <div class="card-highlight" style="padding: 11px 16px;">
          <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin-bottom: 3px;">100% COLLABORATIVE PARTNERSHIP WITH ZERO LOCK-IN</div>
          <div style="font-size: 11px; color: #0369a1; line-height: 1.45;">
            You are never locked into a binding contract. If you don't see results, you can cancel anytime. If you see results, we continue month-to-month with complete transparency.
          </div>
        </div>
        """
    exec_arch = cfg.get("execution_architecture", {})
    if exec_arch and "body_html" in exec_arch:
        page4_tag = exec_arch.get("tag", "03 / TURNKEY EXECUTION & CLIENT PEACE OF MIND")
        page4_title = exec_arch.get("title", "100% Done-For-You Marketing & Operational Freedom")
        page4_subtitle = exec_arch.get("subtitle", "Innovate Marketers handles all advertising and technical heavy lifting—zero technical burden on your team.")
        page4_body = exec_arch["body_html"]
    else:
        page4_tag = "03 / TECHNICAL DEPLOYMENT & EXECUTION"
        page4_title = "100% Turnkey Technical Execution & Engineering Deployment"
        page4_subtitle = "Innovate Marketers handles all server configuration, code injection, schema, and security—zero technical burden on your team."
        page4_body = f"""
        <div style="font-size: 11.5px; color: #1e293b; line-height: 1.55; margin-bottom: 12px;">
          Because your practice focuses on core client fulfillment and operations, <strong>Innovate Marketers handles 100% of the technical deployment directly</strong>. You will never need to write code, configure servers, or troubleshoot indexing errors.
        </div>
        <div class="grid-3" style="margin-bottom: 14px;">
          <div class="card" style="border-top: 3.5px solid #0284c7; padding: 12px 13px;">
            <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin-bottom: 4px;">1. Server & Security</div>
            <div style="font-size: 10.5px; color: #334155; line-height: 1.45;">
              Complete SSL encryption enforcement, 301 canonical redirects, DMARC email spoof protection, and custom robots.txt directives.
            </div>
          </div>
          <div class="card" style="border-top: 3.5px solid #059669; padding: 12px 13px;">
            <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin-bottom: 4px;">2. Schema & Entity Data</div>
            <div style="font-size: 10.5px; color: #334155; line-height: 1.45;">
              Custom JSON-LD schema injection feeding search engines and AI assistants verified credentials, locations, services, and pricing.
            </div>
          </div>
          <div class="card" style="border-top: 3.5px solid #7c3aed; padding: 12px 13px;">
            <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin-bottom: 4px;">3. Authority & Indexing</div>
            <div style="font-size: 10.5px; color: #334155; line-height: 1.45;">
              Google Search Console verification, XML sitemap indexing, monthly high-authority backlinks, and verified Map Pack signals.
            </div>
          </div>
        </div>
        <div class="card-highlight" style="padding: 11px 16px;">
          <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin-bottom: 3px;">TURNKEY PEACE OF MIND WITH ZERO CONTRACT RISK</div>
          <div style="font-size: 11px; color: #0369a1; line-height: 1.45;">
            All technical implementations are completed directly by our senior engineering team with zero downtime. You retain 100% permanent ownership of all code, assets, and setups.
          </div>
        </div>
        """

    # Page 6: Roadmap Data
    roadmap = cfg.get("roadmap", {})
    roadmap_h1 = roadmap.get("roadmap_title", "Step-by-Step Technical Execution & Handover Roadmap (5-Day Deployment)" if is_onetime else "Step-by-Step Growth Roadmap (30 to 90 Days & Ongoing)")
    roadmap_sub = roadmap.get("roadmap_subtitle", "A structured, rapid deployment: technical preparation, security enforcement, on-page optimization, and verification." if is_onetime else "A clear sequence of work: establish the foundation, improve relevance, develop authority, and measure visibility.")
    phase1_tag = roadmap.get("phase1_tag", "PREPARATION" if is_onetime else "FOUNDATION SETUP")
    phase2_tag = roadmap.get("phase2_tag", "SECURITY & CRAWL" if is_onetime else "ON-PAGE & AI DATA")
    phase3_tag = roadmap.get("phase3_tag", "ON-PAGE & SCHEMA" if is_onetime else "AUTHORITY & PR")
    phase4_tag = roadmap.get("phase4_tag", "VERIFICATION" if is_onetime else "AI REVIEW & SCALE")

    phase1_title = roadmap.get("phase1_title", "Foundation, Setup & Tracking Configuration")
    phase1_bullets = "".join([f"<li>{b}</li>" for b in roadmap.get("phase1_bullets", [
        "Deploy 301 redirect rules, DMARC email security records, and heading hierarchy blueprints.",
        "Configure Google Analytics 4 (GA4) and Google Search Console to track verified incoming domestic visitors.",
        f"Finalize the priority search phrases ({std['keywords_count']} for Standard / {pro.get('keywords_count', 50)} for Professional)." if not is_single_plan else f"Finalize the {std['keywords_count']} priority search phrases.",
        "Set up and verify your official Google Business Profile (Google Maps)."
    ])])
    
    phase2_title = roadmap.get("phase2_title", "Google Snippets, On-Page Content & AI Data Setup")
    phase2_bullets = "".join([f"<li>{b}</li>" for b in roadmap.get("phase2_bullets", [
        "Deploy fully rewritten, click-optimized page titles and Google preview summaries across core pages.",
        "Inject custom Schema.org code feeding AI bots your core service dates, locations, and pricing.",
        "Verify implementation of mobile legibility, canonical directives, and image descriptions."
    ])])
    
    phase3_title = roadmap.get("phase3_title", "Authority Endorsements, Guest Articles & PR")
    phase3_bullets = "".join([f"<li>{b}</li>" for b in roadmap.get("phase3_bullets", [
        f"Activate monthly authority backlinks: {std['backlinks_per_month']} links (Standard) or {pro.get('backlinks_per_month', 200)} links (Professional)." if not is_single_plan else f"Activate monthly authority backlinks: {std['backlinks_per_month']} high-authority links on DA 50+ sites.",
        f"Publish {std['guest_articles']} to {pro.get('guest_articles', 2)} high-authority guest articles on recognized industry publications." if not is_single_plan else f"Publish {std['guest_articles']} high-authority guest article on recognized publications.",
        "Publish 6 to 10 verified business directory listings to build regional and brand entity trust."
    ])])
    
    phase4_title = roadmap.get("phase4_title", "AI Recommendation Audit & Ongoing Review")
    phase4_bullets = "".join([f"<li>{b}</li>" for b in roadmap.get("phase4_bullets", [
        "Test how ChatGPT, Google AI Overviews, and Gemini recommend your business for target queries.",
        "Deploy competitor conquesting strategies to surpass rival market leaders on Page 1.",
        "Deliver comprehensive monthly ROI reports with data-driven recommendations for continuous scaling."
    ])])

    # Pricing Rate Cards Formatter for Page 7
    if not is_single_plan:
        if curr == "USD":
            orig_std_rate = f"${std.get('original_price_usd', 599)} USD/mo"
            orig_pro_rate = f"${pro.get('original_price_usd', 999)} USD/mo"
            savings_std_text = f"Save ${std.get('original_price_usd', 599) - std['price']} USD/mo ({std.get('discount_pct', 42)}% Partner Discount)"
            savings_pro_text = f"Save ${pro.get('original_price_usd', 999) - pro.get('price', 999)} USD/mo ({pro.get('discount_pct', 41)}% Partner Discount)"
        else:
            orig_std_rate = f"${std.get('original_price_usd', 999)} USD/mo (~${std.get('original_price_cad_approx', 1380)} {curr})"
            orig_pro_rate = f"${pro.get('original_price_usd', 1599)} USD/mo (~${pro.get('original_price_cad_approx', 2200)} {curr})"
            savings_std_text = f"Save {curr_sym}{std.get('original_price_cad_approx', 1380) - std['price']} {curr}/mo ({std.get('discount_pct', 42)}% Effective Discount)"
            savings_pro_text = f"Save {curr_sym}{pro.get('original_price_cad_approx', 2200) - pro.get('price', 1299)} {curr}/mo ({pro.get('discount_pct', 41)}% Effective Discount)"
    else:
        orig_std_rate = ""
        orig_pro_rate = ""
        savings_std_text = ""
        savings_pro_text = ""

    std_price = std.get("price", 300)
    pro_price = pro.get("price", 500)
    std_col_header = std.get("table_col_header", f"STARTER PLAN ({curr_sym}{std_price} {curr})")
    pro_col_header = pro.get("table_col_header", f"COMPREHENSIVE PLAN ({curr_sym}{pro_price} {curr})")

    # Scope Deliverables Table for Page 7
    scope_rows = cfg.get("scope_rows", [])
    if is_single_plan:
        if scope_rows:
            scope_rows_html = "".join([f"""
            <tr>
              <td style="padding: 6px 10px;"><strong>{r['area']}<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">({r.get('sub', '')})</span></strong></td>
              <td style="padding: 6px 10px;">{r['spec']}</td>
            </tr>
            """ for r in scope_rows])
        else:
            scope_rows_html = f"""
            <tr>
              <td style="padding: 6px 10px;"><strong>Target Search Phrases<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">(What clients type on Google)</span></strong></td>
              <td style="padding: 6px 10px;">{std['keywords_count']} High-Intent Commercial Phrases</td>
            </tr>
            <tr>
              <td style="padding: 6px 10px;"><strong>AI Recommendation Audit<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">(ChatGPT & Google AI Review)</span></strong></td>
              <td style="padding: 6px 10px;">{std['ai_pages']} Priority Service Pages Analyzed for AI Answer Engine Prominence</td>
            </tr>
            <tr>
              <td style="padding: 6px 10px;"><strong>Authority Endorsements<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">(Monthly Backlinks)</span></strong></td>
              <td style="padding: 6px 10px;">{std['backlinks_per_month']} Quality Authority Backlinks on DA 50+ Domain Assets</td>
            </tr>
            <tr>
              <td style="padding: 6px 10px;"><strong>Guest Articles on Authority Sites</strong></td>
              <td style="padding: 6px 10px;">{std['guest_articles']} High-Authority Technical Guest Article on Recognized Publications</td>
            </tr>
            <tr>
              <td style="padding: 6px 10px;"><strong>Google Maps & Regional Authority</strong></td>
              <td style="padding: 6px 10px;">Included (Regional Optimization for Target Search Markets)</td>
            </tr>
            <tr>
              <td style="padding: 6px 10px;"><strong>Contract Commitment</strong></td>
              <td style="padding: 6px 10px;"><strong>Zero Contract Lock-In (Month-to-Month Flexibility • Cancel Anytime)</strong></td>
            </tr>
            <tr>
              <td style="padding: 6px 10px;"><strong>Executive Reporting & Search Insights</strong></td>
              <td style="padding: 6px 10px;">Monthly Executive KPI Report & Search Position Tracking</td>
            </tr>
            """
    else:
        # Multi-Plan Comparison Table
        multi_scope = cfg.get("multi_scope_rows", [])
        if multi_scope:
            scope_rows_html = "".join([f"""
            <tr>
              <td style="padding: 6px 10px;"><strong>{r['area']}<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">({r.get('sub', '')})</span></strong></td>
              <td style="padding: 6px 10px;">{r['std']}</td>
              <td style="padding: 6px 10px;"><strong>{r['pro']}</strong></td>
            </tr>
            """ for r in multi_scope])
        else:
            scope_rows_html = f"""
            <tr>
              <td style="padding: 6px 10px;"><strong>Target Search Phrases<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">(What clients type on Google)</span></strong></td>
              <td style="padding: 6px 10px;">{std['keywords_count']} High-Intent Phrases</td>
              <td style="padding: 6px 10px;"><strong>{pro.get('keywords_count', 60)} Priority & Expansion Phrases</strong></td>
            </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>AI Recommendation Audit<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">(ChatGPT & Google AI Review)</span></strong></td>
          <td style="padding: 6px 10px;">{std['ai_pages']} Priority Service Pages</td>
          <td style="padding: 6px 10px;"><strong>{pro.get('ai_pages', 8)} Comprehensive Pages</strong></td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>Authority Endorsements<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">(Monthly Backlinks)</span></strong></td>
          <td style="padding: 6px 10px;">{std['backlinks_per_month']} Links / mo (DA 50+)</td>
          <td style="padding: 6px 10px;"><strong>{pro.get('backlinks_per_month', 250)} Links / mo (DA 50+)</strong></td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>Guest Articles on Authority Sites</strong></td>
          <td style="padding: 6px 10px;">{std['guest_articles']} Articles / month</td>
          <td style="padding: 6px 10px;"><strong>{pro.get('guest_articles', 4)} Articles / month</strong></td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>Google Maps & Regional Presence</strong></td>
          <td style="padding: 6px 10px;">Included (Regional Hub)</td>
          <td style="padding: 6px 10px;"><strong>Included (Multi-Region Hubs)</strong></td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>Content Syndication & Social Channels</strong></td>
          <td style="padding: 6px 10px;">{std['social_channels']} Channels ({std['social_posts']} posts/mo)</td>
          <td style="padding: 6px 10px;"><strong>{pro.get('social_channels', 4)} Channels ({pro.get('social_posts', 16)} posts/mo)</strong></td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>Developer Collaboration / Sync</strong></td>
          <td style="padding: 6px 10px;">Included (Code Handoff & Monthly Sync)</td>
          <td style="padding: 6px 10px;"><strong>Included (Bi-Weekly Working Sessions)</strong></td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>Contract Commitment</strong></td>
          <td style="padding: 6px 10px;"><strong>Zero Contract (Cancel Anytime)</strong></td>
          <td style="padding: 6px 10px;"><strong>Zero Contract (Cancel Anytime)</strong></td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>Executive Reporting & Search Insights</strong></td>
          <td style="padding: 6px 10px;">Monthly Executive KPI Report</td>
          <td style="padding: 6px 10px;"><strong>Bi-Weekly Live Strategy & KPI Sync</strong></td>
        </tr>
        """

    terms_text = cfg.get("pricing_terms", f"<strong>Terms & Partnership Flexibility:</strong> Month-to-month agreement with zero long-term lock-in or binding contract. If you don't see results, you can cancel anytime. If you see results, we continue month-to-month. Billed strictly in {curr} with zero international conversion surcharges. You retain 100% permanent ownership of all created content, backlinks, schemas, and analytics setups.")

    # Team Attribution
    lead_raw = cfg.get('lead_consultant', 'Shivaprasad Farale (Shiv) | Senior Client Lead • Direct: +1 (645) 220-1660')
    sme_raw = cfg.get('subject_matter_expert', 'Shubham Satyawali | Innovate Marketers LLC')
    lead_name = lead_raw.split('|')[0].strip()
    sme_name = sme_raw.split('|')[0].strip()
    lead_role_and_phone = lead_raw.split('|', 1)[1].strip() if '|' in lead_raw else 'Senior Client Lead & Consultant'
    sme_role = sme_raw.split('|', 1)[1].strip() if '|' in sme_raw else 'SEO & AEO Subject Matter Expert'

    # Next Steps Step 3 & 4
    if has_dev:
        step3_title = "15-Minute Technical Briefing with Your In-House Developer"
        step3_desc = "We hand off the exact code snippets (301 redirect syntax, DMARC TXT record, heading map) directly to your tech specialist for immediate implementation."
    elif is_kt:
        step3_title = "Technical Briefing & Knowledge Transfer Kickoff"
        step3_desc = "We walk through turnkey code snippets (robots.txt, schema, metadata) and demonstrate the tracking and publishing workflow."
    else:
        step3_title = "Provide Server & Webmaster Access"
        step3_desc = "Provide temporary hosting, CMS, or DNS access so our technical engineers can install SSL and configure server files directly."

    default_quote = f"We look forward to collaborating with {cfg['client_name']} and {cfg['client_company']} to establish your digital infrastructure on a secure, high-performing foundation."
    closing_quote_text = cfg.get("closing_quote", default_quote)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800;900&display=swap" rel="stylesheet">
<title>{cfg['client_company']} - SEO, AI Search & Brand Visibility Proposal</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800;900&display=swap');

  @page {{
    size: letter portrait;
    margin: 0;
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #1e293b;
    background-color: #f8fafc;
    font-size: 12px;
    line-height: 1.5;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }}

  h1, h2, h3, h4, .page-title, .section-tag, .card-title, .metric-val, .plan-name, .price-val {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    letter-spacing: -0.2px;
  }}

  code, pre, .mono, .badge {{
    font-family: 'JetBrains Mono', monospace;
  }}

  .page {{
    width: 8.5in;
    height: 11in;
    max-height: 11in;
    margin: 0 auto;
    padding: 38px 46px;
    background: #ffffff;
    position: relative;
    overflow: hidden;
    page-break-after: always;
    page-break-inside: avoid;
    display: flex;
    flex-direction: column;
  }}

  .page-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: #475569;
    text-transform: uppercase;
    padding-bottom: 8px;
    border-bottom: 1.5px solid #e2e8f0;
    margin-bottom: 12px;
  }}

  .page-header .brand-tag {{
    color: #0b2545;
  }}
  .page-header .brand-tag span {{
    color: #0284c7;
    margin: 0 4px;
  }}

  .page-footer {{
    position: absolute;
    bottom: 20px;
    left: 46px;
    right: 46px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 8.5px;
    font-weight: 700;
    letter-spacing: 0.6px;
    color: #64748b;
    text-transform: uppercase;
    padding-top: 8px;
    border-top: 1.5px solid #e2e8f0;
  }}

  .section-tag {{
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.2px;
    color: #0284c7;
    text-transform: uppercase;
    margin-bottom: 2px;
  }}

  h1.page-title {{
    font-size: 21px;
    font-weight: 800;
    color: #0b2545;
    line-height: 1.25;
    margin-bottom: 3px;
    letter-spacing: -0.3px;
  }}

  .page-subtitle {{
    font-size: 11px;
    color: #475569;
    font-style: italic;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #0284c7;
  }}

  .content-body {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}

  .card {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 14px;
    box-shadow: 0 2px 8px -2px rgba(15, 23, 42, 0.04);
  }}

  .card-tinted {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 11px 13px;
  }}

  .card-highlight {{
    background: #f0f9ff;
    border: 1.5px solid #bae6fd;
    border-radius: 8px;
    padding: 11px 15px;
  }}

  .card-navy {{
    background: #0b2545;
    color: #ffffff;
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: 0 4px 14px rgba(11, 37, 69, 0.12);
  }}

  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 11px;
  }}

  .grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }}

  .grid-4 {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 9px;
  }}

  table.data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 10.5px;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    overflow: hidden;
  }}

  table.data-table th {{
    background: #0b2545;
    color: #ffffff;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 9px;
    letter-spacing: 0.6px;
    padding: 7px 10px;
    border: 1px solid #0b2545;
  }}

  table.data-table td {{
    padding: 6px 10px;
    border: 1px solid #e2e8f0;
    vertical-align: middle;
    color: #1e293b;
    line-height: 1.35;
  }}

  table.data-table tr:nth-child(even) td {{
    background-color: #f8fafc;
  }}

  .badge {{
    display: inline-block;
    padding: 2.5px 7px;
    border-radius: 9999px;
    font-size: 8.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }}
  .badge-emerald {{ background: #d1fae5; color: #065f46; }}
  .badge-rose {{ background: #ffe4e6; color: #9f1239; }}
  .badge-amber {{ background: #fef3c7; color: #92400e; }}
  .badge-teal {{ background: #e0f2fe; color: #0369a1; }}
  .badge-navy {{ background: #0b2545; color: #ffffff; }}

  .cover-confidential {{
    text-align: center;
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: #475569;
    text-transform: uppercase;
    margin-bottom: 24px;
  }}

  .cover-logo-wrapper {{
    text-align: center;
    margin-bottom: 22px;
  }}

  .cover-logo-wrapper img {{
    height: 78px;
    object-fit: contain;
  }}

  .cover-title-block {{
    text-align: center;
    margin-bottom: 24px;
  }}

  .cover-main-title {{
    font-size: 26px;
    font-weight: 900;
    color: #0b2545;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
    line-height: 1.2;
  }}

  .cover-tagline {{
    font-size: 13.5px;
    color: #0284c7;
    font-weight: 600;
  }}

  .capability-pill-bar {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    background: #f0f9ff;
    border: 1.5px solid #bae6fd;
    border-radius: 8px;
    margin-bottom: 20px;
    text-align: center;
    overflow: hidden;
  }}

  .capability-item {{
    padding: 8px 6px;
    border-right: 1px solid #bae6fd;
  }}
  .capability-item:last-child {{
    border-right: none;
  }}
  .capability-title {{
    font-size: 9.5px;
    font-weight: 800;
    color: #0b2545;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
  }}
  .capability-desc {{
    font-size: 9px;
    color: #334155;
    font-weight: 500;
  }}

  .meta-grid-box {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 20px;
    font-size: 10.5px;
    box-shadow: 0 2px 8px -2px rgba(15, 23, 42, 0.04);
  }}

  .meta-cell {{
    padding: 8px 14px;
    border-bottom: 1px solid #e2e8f0;
    background: #ffffff;
  }}
  .meta-cell:nth-child(even) {{
    border-left: 1px solid #e2e8f0;
  }}
  .meta-cell:nth-last-child(-n+2) {{
    border-bottom: none;
  }}
  .meta-label {{
    font-size: 8.5px;
    font-weight: 800;
    color: #0284c7;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 2px;
  }}
  .meta-val {{
    font-weight: 700;
    color: #0f172a;
    font-size: 11px;
  }}

  .timeline-row {{
    display: flex;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
    background: #ffffff;
    margin-bottom: 9px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  }}
  .timeline-aside {{
    width: 140px;
    background: #0b2545;
    color: #ffffff;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }}
  .timeline-phase {{
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.5px;
  }}
  .timeline-weeks {{
    font-size: 8.5px;
    color: #93c5fd;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 2px;
    font-weight: 700;
  }}
  .timeline-body {{
    flex: 1;
    padding: 10px 14px;
    background: #f8fafc;
  }}
  .timeline-title {{
    font-size: 11.5px;
    font-weight: 800;
    color: #0b2545;
    margin-bottom: 4px;
  }}
  .timeline-bullets {{
    list-style: none;
    font-size: 10.5px;
    color: #334155;
  }}
  .timeline-bullets li {{
    position: relative;
    padding-left: 14px;
    margin-bottom: 2.5px;
    line-height: 1.35;
  }}
  .timeline-bullets li::before {{
    content: "•";
    position: absolute;
    left: 2px;
    color: #0284c7;
    font-weight: 800;
    font-size: 12px;
  }}

  ul.check-list {{
    list-style: none;
    font-size: 10.5px;
    color: #1e293b;
  }}
  ul.check-list li {{
    position: relative;
    padding-left: 16px;
    margin-bottom: 3.5px;
    line-height: 1.35;
  }}
  ul.check-list li::before {{
    content: "✓";
    position: absolute;
    left: 0;
    color: #059669;
    font-weight: 800;
  }}
</style>
</head>
<body>

<!-- PAGE 1: COVER (EXECUTIVE & PRESTIGIOUS - ZERO PRICING) -->
<div class="page">
  <div class="cover-confidential">
    CONFIDENTIAL STRATEGY PROPOSAL — PREPARED EXCLUSIVELY FOR {cfg['client_company'].upper()}
  </div>

  <div class="cover-logo-wrapper">
    <img src="{logo_src}" alt="Innovate Marketers LLC">
  </div>

  <div class="cover-title-block">
    <div class="cover-main-title">SEO, AI SEARCH & EXECUTIVE BRAND VISIBILITY</div>
    <div class="cover-tagline">A Strategic Growth Plan to Help High-Net-Worth Decision-Makers Discover {cfg.get('brand_short_name', cfg['client_company'])}</div>
  </div>

  <div class="capability-pill-bar">
    {pills_html}
  </div>

  <div class="meta-grid-box">
    <div class="meta-cell">
      <div class="meta-label">PREPARED FOR</div>
      <div class="meta-val">{cfg['client_name']}, {cfg['client_title']}</div>
    </div>
    <div class="meta-cell">
      <div class="meta-label">ORGANIZATION</div>
      <div class="meta-val">{cfg['client_company']}</div>
    </div>
    <div class="meta-cell">
      <div class="meta-label">WEBSITE AUDITED</div>
      <div class="meta-val">{cfg['client_website']}</div>
    </div>
    <div class="meta-cell">
      <div class="meta-label">PRIMARY LEAD CONSULTANT</div>
      <div class="meta-val">{lead_name} | Direct: +1 (645) 220-1660</div>
    </div>
    <div class="meta-cell">
      <div class="meta-label">TECHNICAL SUBJECT MATTER EXPERT</div>
      <div class="meta-val">{sme_name} | Innovate Marketers LLC</div>
    </div>
    <div class="meta-cell">
      <div class="meta-label">PROPOSAL PRESENTATION</div>
      <div class="meta-val">{cfg.get('proposal_date', 'October 2026')} | Scheduled: {cfg.get('scheduled_meeting', 'Google Meet')}</div>
    </div>
  </div>

  <!-- Executive Scope & Partnership Note (Replaces Premature Pricing) -->
  <div class="card" style="border-top: 3.5px solid #0284c7; padding: 16px 20px; background: #ffffff;">
    <div style="font-size: 11.5px; font-weight: 800; color: #0284c7; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;">
      EXECUTIVE MANDATE & PARTNERSHIP PHILOSOPHY
    </div>
    <div style="font-size: 11px; color: #334155; line-height: 1.55; margin-bottom: 12px;">
      This proposal establishes a scientific organic growth and Answer Engine Optimization (AEO) system for <strong>{cfg['client_company']}</strong>. Our engagement is engineered to capture high-intent commercial buyers, resolve crawl indexation bottlenecks, and position your brand as the definitive authority across Google Search, ChatGPT, Perplexity, and Google Maps.
    </div>
    <div class="grid-3" style="font-size: 10px;">
      <div style="background: #f8fafc; padding: 8px 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
        <strong style="color: #0b2545;">Zero Contract Lock-In:</strong> Month-to-month flexibility with complete performance transparency.
      </div>
      <div style="background: #f8fafc; padding: 8px 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
        <strong style="color: #0b2545;">Asset Ownership:</strong> You retain 100% permanent ownership of all created content, backlinks, schemas, and analytics.
      </div>
      <div style="background: #f8fafc; padding: 8px 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
        <strong style="color: #0b2545;">Collaborative Synergy:</strong> Zero technical friction, designed around your existing operational structure.
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>CONFIDENTIAL | {cfg['client_company'].upper()}</span>
    <span>PAGE 1 | 8</span>
  </div>
</div>

<!-- PAGE 2: STRATEGIC VISION & THE COMMERCIAL OPPORTUNITY -->
<div class="page">
  <div class="page-header">
    <div class="brand-tag">INNOVATE MARKETERS <span>/</span> SEO, AEO & DIGITAL VISIBILITY</div>
    <div>CONFIDENTIAL | {cfg['client_company'].upper()}</div>
  </div>

  <div class="section-tag">01 / STRATEGIC VISION & COMMERCIAL OPPORTUNITY</div>
  <h1 class="page-title">{strat.get('title', 'Elevating Your Brand to Premier Industry Authority')}</h1>
  <div class="page-subtitle">{strat.get('subtitle', 'Built specifically around your practice, deep expertise, and targeted regional expansion.')}</div>

  <div class="content-body">
    <div style="font-size: 11.5px; color: #1e293b; line-height: 1.55;">
      <strong>Dear {cfg['client_name'].split()[0]},</strong><br>
      {strat.get('intro_letter', '')}
    </div>

    <div class="card-highlight" style="padding: 12px 16px;">
      <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin-bottom: 4px;">THE CORE STRATEGIC OPPORTUNITY</div>
      <div style="font-size: 11px; color: #0369a1; line-height: 1.5;">
        {strat.get('core_opportunity', '')}
      </div>
    </div>

    <div style="font-size: 12.5px; font-weight: 800; color: #0b2545; margin-top: 2px;">The Four Pillars of Your Customized Growth Plan</div>

    <table class="data-table">
      <thead>
        <tr>
          <th style="width: 28%; padding: 7px 10px;">GROWTH PILLAR</th>
          <th style="width: 72%; padding: 7px 10px;">PLAIN-ENGLISH EXPLANATION & WHAT WE DELIVER</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="padding: 6px 10px;"><strong>1. High-Intent Search Phrases<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">(Commercial Keywords)</span></strong></td>
          <td style="padding: 6px 10px;">We target the exact terms high-value decision-makers type into Google, ensuring you appear on Page 1 ahead of regional competitors.</td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>2. AI Recommendations<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">(AEO / Answer Engines)</span></strong></td>
          <td style="padding: 6px 10px;">When prospects ask ChatGPT, Gemini, or Perplexity for vetted experts in your niche, we structure your site so AI assistants recommend you by name.</td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>3. Google Maps & Local Trust<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">(Google Business Profile)</span></strong></td>
          <td style="padding: 6px 10px;">We verify and optimize your Google Business Profile so local searchers see verified reviews, operating locations, and credibility badges directly on Google Maps.</td>
        </tr>
        <tr>
          <td style="padding: 6px 10px;"><strong>{pillar4_title}<br><span style="font-size: 8.5px; color: #64748b; font-weight: 400;">{pillar4_sub}</span></strong></td>
          <td style="padding: 6px 10px;">{pillar4_desc}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="page-footer">
    <span>CONFIDENTIAL | {cfg['client_company'].upper()}</span>
    <span>PAGE 2 | 8</span>
  </div>
</div>

<!-- PAGE 3: TECHNICAL HEALTH CHECK & COMMERCIAL IMPACT -->
<div class="page">
  <div class="page-header">
    <div class="brand-tag">INNOVATE MARKETERS <span>/</span> SEO, AEO & DIGITAL VISIBILITY</div>
    <div>CONFIDENTIAL | {cfg['client_company'].upper()}</div>
  </div>

  <div class="section-tag">02 / TECHNICAL HEALTH CHECK</div>
  <h1 class="page-title">Website Diagnostic: Bottlenecks Spotted on {cfg['client_website'].split('/')[0].strip()}</h1>
  <div class="page-subtitle">A clear breakdown of technical bottlenecks preventing Google and AI from recommending your site.</div>

  <div class="content-body" style="gap: 12px;">
    <!-- Top KPI Scorecards -->
    <div class="grid-4">
      <div class="card-tinted" style="text-align: center; border-top: 3.5px solid #e11d48; padding: 10px 8px;">
        <div style="font-size: 8.5px; font-weight: 800; color: #64748b; text-transform: uppercase;">SEO HEALTH SCORE</div>
        <div style="font-size: 22px; font-weight: 800; color: #e11d48; margin: 2px 0;">{tech.get('seo_health_score', '41 / 100')}</div>
        <div style="font-size: 8px; color: #475569; font-weight: 600;">{tech.get('seo_status', 'Needs Immediate Fixes')}</div>
      </div>
      <div class="card-tinted" style="text-align: center; border-top: 3.5px solid #d97706; padding: 10px 8px;">
        <div style="font-size: 8.5px; font-weight: 800; color: #64748b; text-transform: uppercase;">DOMESTIC TRAFFIC</div>
        <div style="font-size: 17px; font-weight: 800; color: #d97706; margin: 4px 0;">{tech.get('mobile_status', 'IMPAIRED')}</div>
        <div style="font-size: 8px; color: #475569; font-weight: 600;">{tech.get('mobile_desc', 'Foreign & Bot Visits')}</div>
      </div>
      <div class="card-tinted" style="text-align: center; border-top: 3.5px solid #e11d48; padding: 10px 8px;">
        <div style="font-size: 8.5px; font-weight: 800; color: #64748b; text-transform: uppercase;">AUTHORITY SCORE</div>
        <div style="font-size: 17px; font-weight: 800; color: #e11d48; margin: 4px 0;">{tech.get('security_status', 'VULNERABLE')}</div>
        <div style="font-size: 8px; color: #475569; font-weight: 600;">{tech.get('security_desc', 'Missing DMARC & SSL')}</div>
      </div>
      <div class="card-tinted" style="text-align: center; border-top: 3.5px solid #0284c7; padding: 10px 8px;">
        <div style="font-size: 8.5px; font-weight: 800; color: #64748b; text-transform: uppercase;">AI SEARCH SCORE</div>
        <div style="font-size: 17px; font-weight: 800; color: #0284c7; margin: 4px 0;">{tech.get('tracking_status', 'MISSING')}</div>
        <div style="font-size: 8px; color: #475569; font-weight: 600;">{tech.get('tracking_desc', 'Zero AI Recommendations')}</div>
      </div>
    </div>

    <div style="font-size: 12px; font-weight: 800; color: #0b2545;">Critical Rectification Plan: Stop the Traffic & Inquiry Leaks</div>

    <!-- Diagnostic Cards (Visual & High-Impact) -->
    <div class="grid-2">
      {tech_cards_html}
    </div>

    <div class="card-highlight" style="padding: 10px 14px;">
      <div style="font-size: 11px; font-weight: 800; color: #0b2545; margin-bottom: 2px;">THE BUSINESS IMPACT OF UNFIXED BUGS</div>
      <div style="font-size: 10.5px; color: #0369a1; line-height: 1.45;">
        When crawl-level errors exist, Google does not index your service offerings—it suppresses them to Page 2 and Page 3. Fixing these 4 infrastructure issues allows Google and AI search models to cleanly index and recommend your pages.
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>CONFIDENTIAL | {cfg['client_company'].upper()}</span>
    <span>PAGE 3 | 8</span>
  </div>
</div>

<!-- PAGE 4: EXECUTION ARCHITECTURE & WORKFLOW (DEV SYNERGY OR TURNKEY) -->
<div class="page">
  <div class="page-header">
    <div class="brand-tag">INNOVATE MARKETERS <span>/</span> SEO, AEO & DIGITAL VISIBILITY</div>
    <div>CONFIDENTIAL | {cfg['client_company'].upper()}</div>
  </div>

  <div class="section-tag">{page4_tag}</div>
  <h1 class="page-title">{page4_title}</h1>
  <div class="page-subtitle">{page4_subtitle}</div>

  <div class="content-body">
    {page4_body}
  </div>

  <div class="page-footer">
    <span>CONFIDENTIAL | {cfg['client_company'].upper()}</span>
    <span>PAGE 4 | 8</span>
  </div>
</div>

<!-- PAGE 5: SEARCH & AI DISCOVERY ARCHITECTURE -->
<div class="page">
  <div class="page-header">
    <div class="brand-tag">INNOVATE MARKETERS <span>/</span> SEO, AEO & DIGITAL VISIBILITY</div>
    <div>CONFIDENTIAL | {cfg['client_company'].upper()}</div>
  </div>

  <div class="section-tag">04 / SEARCH & AI DISCOVERY ARCHITECTURE</div>
  <h1 class="page-title">What Decision-Makers Search & How AI Recommends You</h1>
  <div class="page-subtitle">Targeting high-intent commercial keywords and securing prominent mentions inside ChatGPT and Google AI.</div>

  <div class="content-body">
    <div class="card-highlight" style="padding: 10px 14px;">
      <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin-bottom: 2px;">WHAT IS A "HIGH-INTENT KEYWORD"? (IN PLAIN ENGLISH)</div>
      <div style="font-size: 11px; color: #0369a1; line-height: 1.45;">
        A <strong>high-intent keyword</strong> is the exact phrase a serious, ready-to-book client types into Google when seeking specialized solutions. We identify high-dollar phrases typed by your target market and optimize your pages to rank #1.
      </div>
    </div>

    <div class="grid-2">
      {cluster_cards_html}
    </div>

    <!-- AI Search Section -->
    <div class="card-navy" style="padding: 12px 16px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
        <span style="font-size: 11.5px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.8px;">
          HOW WE GET CHATGPT & GOOGLE AI TO RECOMMEND YOUR BUSINESS
        </span>
        <span class="badge" style="background: #1e3a8a; color: #bfdbfe;">Next-Gen Search</span>
      </div>
      <div style="font-size: 10.5px; color: #cbd5e1; line-height: 1.45; margin-bottom: 8px;">
        High-net-worth clients frequently use AI assistants to research retreats and consultants. Here is how we ensure AI names your brand:
      </div>
      <div class="grid-3" style="font-size: 10px; color: #ffffff;">
        <div style="background: rgba(255,255,255,0.08); padding: 8px; border-radius: 6px;">
          <strong style="color: #38bdf8;">Entity Mapping:</strong> We feed AI algorithms structured entity tags establishing your brand as a verified authority in your sector.
        </div>
        <div style="background: rgba(255,255,255,0.08); padding: 8px; border-radius: 6px;">
          <strong style="color: #38bdf8;">Direct Q&A Blocks:</strong> We embed structured FAQ blocks that Google AI Overviews and Perplexity quote directly in top answers.
        </div>
        <div style="background: rgba(255,255,255,0.08); padding: 8px; border-radius: 6px;">
          <strong style="color: #38bdf8;">Third-Party Proof:</strong> We publish articles on trusted industry platforms so Large Language Models cite your verified expertise.
        </div>
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>CONFIDENTIAL | {cfg['client_company'].upper()}</span>
    <span>PAGE 5 | 8</span>
  </div>
</div>

<!-- PAGE 6: GROWTH ROADMAP & EXPECTED OUTCOMES -->
<div class="page">
  <div class="page-header">
    <div class="brand-tag">INNOVATE MARKETERS <span>/</span> SEO, AEO & DIGITAL VISIBILITY</div>
    <div>CONFIDENTIAL | {cfg['client_company'].upper()}</div>
  </div>

  <div class="section-tag">05 / GROWTH ROADMAP & EXPECTED MILESTONES</div>
  <h1 class="page-title">{roadmap_h1}</h1>
  <div class="page-subtitle">{roadmap_sub}</div>

  <div class="content-body">
    <!-- Phase 1 -->
    <div class="timeline-row">
      <div class="timeline-aside">
        <div class="timeline-phase">PHASE 1</div>
        <div class="timeline-weeks">{phase1_tag}</div>
      </div>
      <div class="timeline-body">
        <div class="timeline-title">{phase1_title}</div>
        <ul class="timeline-bullets">
          {phase1_bullets}
        </ul>
      </div>
    </div>

    <!-- Phase 2 -->
    <div class="timeline-row">
      <div class="timeline-aside">
        <div class="timeline-phase">PHASE 2</div>
        <div class="timeline-weeks">{phase2_tag}</div>
      </div>
      <div class="timeline-body">
        <div class="timeline-title">{phase2_title}</div>
        <ul class="timeline-bullets">
          {phase2_bullets}
        </ul>
      </div>
    </div>

    <!-- Phase 3 -->
    <div class="timeline-row">
      <div class="timeline-aside">
        <div class="timeline-phase">PHASE 3</div>
        <div class="timeline-weeks">{phase3_tag}</div>
      </div>
      <div class="timeline-body">
        <div class="timeline-title">{phase3_title}</div>
        <ul class="timeline-bullets">
          {phase3_bullets}
        </ul>
      </div>
    </div>

    <!-- Phase 4 -->
    <div class="timeline-row">
      <div class="timeline-aside">
        <div class="timeline-phase">PHASE 4</div>
        <div class="timeline-weeks">{phase4_tag}</div>
      </div>
      <div class="timeline-body">
        <div class="timeline-title">{phase4_title}</div>
        <ul class="timeline-bullets">
          {phase4_bullets}
        </ul>
      </div>
    </div>

    <!-- Expected Milestones Summary Grid -->
    <div class="grid-3" style="margin-top: 4px;">
      <div class="card-tinted" style="border-top: 3.5px solid #0284c7; padding: 10px 11px;">
        <div style="font-size: 8.5px; font-weight: 800; color: #0284c7; text-transform: uppercase;">MONTH 1</div>
        <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin: 2px 0;">Technical Health</div>
        <div style="font-size: 9.5px; color: #475569; line-height: 1.4;">All crawl bugs fixed, SSL secured, GA4 tracking active, and Google Maps verified.</div>
      </div>
      <div class="card-tinted" style="border-top: 3.5px solid #059669; padding: 10px 11px;">
        <div style="font-size: 8.5px; font-weight: 800; color: #059669; text-transform: uppercase;">MONTH 2</div>
        <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin: 2px 0;">Rankings Movement</div>
        <div style="font-size: 9.5px; color: #475569; line-height: 1.4;">Authority links indexed, preview snippets updated, and target phrases climbing Top 20.</div>
      </div>
      <div class="card-tinted" style="border-top: 3.5px solid #0b2545; padding: 10px 11px;">
        <div style="font-size: 8.5px; font-weight: 800; color: #0b2545; text-transform: uppercase;">MONTH 3+</div>
        <div style="font-size: 11.5px; font-weight: 800; color: #0b2545; margin: 2px 0;">Page 1 & Inquiries</div>
        <div style="font-size: 9.5px; color: #475569; line-height: 1.4;">Commercial keywords breaking Page 1, ChatGPT recommending brand, and direct client bookings.</div>
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>CONFIDENTIAL | {cfg['client_company'].upper()}</span>
    <span>PAGE 6 | 8</span>
  </div>
</div>

<!-- PAGE 7: INVESTMENT & PARTNERSHIP PACKAGES -->
<div class="page">
  <div class="page-header">
    <div class="brand-tag">INNOVATE MARKETERS <span>/</span> SEO, AEO & DIGITAL VISIBILITY</div>
    <div>CONFIDENTIAL | {cfg['client_company'].upper()}</div>
  </div>

  <div class="section-tag">06 / INVESTMENT & {curr.upper()} PARTNERSHIP PACKAGES</div>
  <h1 class="page-title">{'Simple, Flat-Rate Investment: ' + curr_sym + str(std['price']) + ' ' + curr + (' (One-Time)' if is_onetime else ' / Month') if is_single_plan else 'Simple, Transparent Investment in ' + curr}</h1>
  <div class="page-subtitle">Customized specifically for {cfg['client_name']} with {'zero recurring fees and 100% permanent asset ownership.' if is_onetime else 'month-to-month flexibility and zero binding contract.'}</div>

  <div class="content-body" style="gap: 5px;">
    <!-- Single Plan vs Multi-Plan Cards -->
    {f'''
    <div class="card" style="border-top: 4px solid #0284c7; padding: 14px 18px; background: #ffffff;">
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 8px;">
        <div>
          <div style="font-size: 13.5px; font-weight: 800; color: #0284c7; text-transform: uppercase; letter-spacing: 0.8px;">
            {std['name']}
          </div>
          <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">
            {std['subtitle']}
          </div>
        </div>
        <div style="text-align: right;">
          <div style="display: flex; align-items: baseline; gap: 4px; justify-content: flex-end;">
            <span style="font-size: 28px; font-weight: 900; color: #0b2545;">{curr_sym}{std['price']} {curr}</span>
            <span style="font-size: 11px; color: #64748b; font-weight: 600;">{price_suffix}</span>
          </div>
          <span class="badge badge-teal" style="font-size: 9px; padding: 3px 8px;">{std.get('tag_badge', badge_default)}</span>
        </div>
      </div>
      <div style="font-size: 11px; color: #334155; line-height: 1.45; background: #f8fafc; padding: 8px 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
        {std['summary_text']}
      </div>
    </div>
    <table class="data-table" style="font-size: 10px;">
      <thead>
        <tr>
          <th style="width: 36%; padding: 6px 10px;">DELIVERABLE / SERVICE AREA</th>
          <th style="width: 64%; padding: 6px 10px;">SPECIFICATION & WHAT INNOVATE MARKETERS DELIVERS</th>
        </tr>
      </thead>
      <tbody>
        {scope_rows_html}
      </tbody>
    </table>
    ''' if is_single_plan else f'''
    <!-- Side-by-Side Pricing Cards -->
    <div class="grid-2" style="margin-bottom: 3px;">
      <!-- Standard Card -->
      <div class="card" style="border: 1.5px solid #0284c7; padding: 7px 11px; background: #ffffff;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 9.5px; font-weight: 800; color: #0284c7; text-transform: uppercase;">{std['name']}</span>
          <span class="badge badge-teal" style="font-size: 7.5px; padding: 1.5px 5px;">{std.get('badge_tag', 'RECOMMENDED')}</span>
        </div>
        <div style="display: flex; align-items: baseline; gap: 4px; margin: 2px 0;">
          <span style="font-size: 20px; font-weight: 900; color: #0b2545;">{curr_sym}{std['price']} {curr}</span>
          <span style="font-size: 9px; color: #64748b; font-weight: 600;">/ month</span>
        </div>
        <div style="font-size: 8px; color: #64748b; margin-bottom: 2px;">
          Published Rate: <span style="text-decoration: line-through;">{orig_std_rate}</span> <span style="color: #059669; font-weight: 700; margin-left: 3px;">({savings_std_text})</span>
        </div>
        <div style="font-size: 8px; color: #334155; background: #f8fafc; padding: 3px 5px; border-radius: 4px; border: 1px solid #e2e8f0; line-height: 1.2;">
          {std['summary_text']}
        </div>
      </div>

      <!-- Professional Card -->
      <div class="card" style="border-top: 3px solid #0b2545; background: #f8fafc; padding: 7px 11px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 9.5px; font-weight: 800; color: #0b2545; text-transform: uppercase;">{pro.get('name', 'Professional')}</span>
          <span class="badge" style="background: #1e3a8a; color: #bfdbfe; font-size: 7.5px; padding: 1.5px 5px;">{pro.get('badge_tag', 'COMPETITOR CONQUEST')}</span>
        </div>
        <div style="display: flex; align-items: baseline; gap: 4px; margin: 2px 0;">
          <span style="font-size: 20px; font-weight: 900; color: #0b2545;">{curr_sym}{pro.get('price', 1299)} {curr}</span>
          <span style="font-size: 9px; color: #64748b; font-weight: 600;">/ month</span>
        </div>
        <div style="font-size: 8px; color: #64748b; margin-bottom: 2px;">
          Published Rate: <span style="text-decoration: line-through;">{orig_pro_rate}</span> <span style="color: #059669; font-weight: 700; margin-left: 3px;">({savings_pro_text})</span>
        </div>
        <div style="font-size: 8px; color: #334155; background: #ffffff; padding: 3px 5px; border-radius: 4px; border: 1px solid #e2e8f0; line-height: 1.2;">
          {pro.get('summary_text', '')}
        </div>
      </div>
    </div>

    <!-- Comparison Table -->
    <table class="data-table" style="font-size: 8px; margin-bottom: 3px;">
      <thead>
        <tr>
          <th style="width: 38%; padding: 3px 6px; font-size: 7.5px;">DELIVERABLE / SERVICE AREA</th>
          <th style="width: 31%; padding: 3px 6px; font-size: 7.5px;">{std_col_header}</th>
          <th style="width: 31%; padding: 3px 6px; font-size: 7.5px;">{pro_col_header}</th>
        </tr>
      </thead>
      <tbody>
        {scope_rows_html}
      </tbody>
    </table>
    '''}

    <div class="card-highlight" style="padding: 5px 9px; margin-top: 2px;">
      <div style="font-size: 9px; font-weight: 800; color: #0b2545; margin-bottom: 1px;">★ ZERO LONG-TERM CONTRACT GUARANTEE</div>
      <div style="font-size: 8px; color: #0369a1; line-height: 1.3;">
        {terms_text}
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>CONFIDENTIAL | {cfg['client_company'].upper()}</span>
    <span>PAGE 7 | 8</span>
  </div>
</div>

<!-- PAGE 8: NEXT STEPS & PARTNERSHIP ONBOARDING -->
<div class="page">
  <div class="page-header">
    <div class="brand-tag">INNOVATE MARKETERS <span>/</span> SEO, AEO & DIGITAL VISIBILITY</div>
    <div>CONFIDENTIAL | {cfg['client_company'].upper()}</div>
  </div>

  <div class="section-tag">07 / NEXT STEPS & PARTNERSHIP ONBOARDING</div>
  <h1 class="page-title">Getting Started: 4 Simple Steps to Launch</h1>
  <div class="page-subtitle">A smooth, straightforward launch designed to get your business growing immediately with zero contract risk.</div>

  <div class="content-body">
    <div style="font-size: 11.5px; color: #1e293b; line-height: 1.5;">
      {f'We have structured this entire proposal to deliver on everything discussed: a complete technical audit, a flat one-time investment of ${std["price"]} USD (zero recurring fees, zero contract lock-in), and complete turnkey execution by our technical team. Here is how we get started:' if is_onetime else (f'We have structured this entire proposal to deliver on everything discussed: a complete technical audit, flat monthly pricing of ${std["price"]} USD (no binding contract, cancel anytime), and dedicated hands-on knowledge transfer with our project team. Here is how we get started:' if is_single_plan else f'We have structured this entire proposal to deliver on everything discussed during our session: a complete technical audit, transparent partner pricing in {curr} (no binding contract, cancel anytime), and dedicated technical collaboration with our senior team. Here is how we get started:')}
    </div>

    <!-- 4 Action Steps -->
    <div class="card" style="padding: 14px 16px;">
      <div style="font-size: 12.5px; font-weight: 800; color: #0b2545; margin-bottom: 10px;">Immediate Onboarding Sequence</div>

      <div style="display: flex; gap: 12px; margin-bottom: 10px;">
        <div style="width: 24px; height: 24px; border-radius: 50%; background: #0284c7; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 11px; flex-shrink: 0;">1</div>
        <div>
          <div style="font-size: 11.5px; font-weight: 800; color: #0b2545;">Confirm Your Preferred Package</div>
          <div style="font-size: 10.5px; color: #475569; line-height: 1.4;">
            {f'Confirm the <strong>{std["name"]} ({curr_sym}{std["price"]} {curr} {price_suffix})</strong> to begin deployment.' if is_single_plan else f'Confirm either the <strong>{std["name"]} ({curr_sym}{std["price"]} {curr}/month, No Contract)</strong> or the Comprehensive Plan based on your expansion targets.'}
          </div>
        </div>
      </div>

      <div style="display: flex; gap: 12px; margin-bottom: 10px;">
        <div style="width: 24px; height: 24px; border-radius: 50%; background: #0284c7; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 11px; flex-shrink: 0;">2</div>
        <div>
          <div style="font-size: 11.5px; font-weight: 800; color: #0b2545;">Kickoff & Technical Alignment Session</div>
          <div style="font-size: 10.5px; color: #475569; line-height: 1.4;">
            Join {lead_name.split()[0]}, {sme_name.split()[0]}, and our technical specialists on Google Meet to review access prerequisites and initialize the technical roadmap.
          </div>
        </div>
      </div>

      <div style="display: flex; gap: 12px; margin-bottom: 10px;">
        <div style="width: 24px; height: 24px; border-radius: 50%; background: #0284c7; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 11px; flex-shrink: 0;">3</div>
        <div>
          <div style="font-size: 11.5px; font-weight: 800; color: #0b2545;">{step3_title}</div>
          <div style="font-size: 10.5px; color: #475569; line-height: 1.4;">
            {step3_desc}
          </div>
        </div>
      </div>

      <div style="display: flex; gap: 12px;">
        <div style="width: 24px; height: 24px; border-radius: 50%; background: #0b2545; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 11px; flex-shrink: 0;">4</div>
        <div>
          <div style="font-size: 11.5px; font-weight: 800; color: #0b2545;">Tracking Access & Launch Phase 1</div>
          <div style="font-size: 10.5px; color: #475569; line-height: 1.4;">
            Arrange Search Console and Analytics access so Innovate Marketers can deploy metadata, schema architecture, and authority campaigns immediately.
          </div>
        </div>
      </div>
    </div>

    <!-- Contact & Meeting Hero Box -->
    <div class="card-navy" style="padding: 16px 20px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div style="font-size: 10px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px;">
          PRIMARY POINTS OF CONTACT
        </div>
        <div style="font-size: 18px; font-weight: 800; color: #ffffff;">
          {lead_name}
        </div>
        <div style="font-size: 11.5px; color: #93c5fd; margin-top: 2px; font-weight: 600;">
          {lead_role_and_phone}
        </div>
        <div style="font-size: 10.5px; color: #cbd5e1; margin-top: 4px;">
          Technical Subject Matter Expert: <strong>{sme_name}</strong> | {sme_role}
        </div>
      </div>

      <div style="text-align: right; border-left: 1.5px solid rgba(255,255,255,0.25); padding-left: 20px;">
        <div style="font-size: 8.5px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 700;">PARTNERSHIP ARRANGEMENT</div>
        <div style="font-size: 14px; font-weight: 800; color: #ffffff; margin: 2px 0;">{curr_sym}{std['price']} {curr} {price_suffix}</div>
        <div style="font-size: 9.5px; color: #38bdf8; font-weight: 600;">{std.get('tag_badge', badge_default)}</div>
      </div>
    </div>

    <div style="font-size: 10.5px; color: #475569; font-style: italic; text-align: center; margin-top: 4px;">
      "{closing_quote_text}"
    </div>
  </div>

  <div class="page-footer">
    <span>CONFIDENTIAL | {cfg['client_company'].upper()}</span>
    <span>PAGE 8 | 8</span>
  </div>
</div>

</body>
</html>
"""
    return html

def generate_proposal_pdf(config_path_or_slug: str, output_pdf_name: str = None) -> str:
    cfg = load_config(config_path_or_slug)
    validate_config_guardrails(cfg)

    slug = cfg.get("client_slug", "client")
    client_clean_name = slug.replace("-", " ").replace("_", " ").title().replace(" ", "_")
    client_vault_dir = resolve_client_vault(slug)
    if output_pdf_name:
        pdf_out_path = Path(output_pdf_name)
    elif client_vault_dir and client_vault_dir.exists():
        pdf_out_path = client_vault_dir / f"{client_clean_name}_SEO_AI_Visibility_Proposal.pdf"
    else:
        pdf_out_path = WORKSPACE_ROOT / f"{client_clean_name}_SEO_AI_Visibility_Proposal.pdf"
    
    import tempfile

    # Generate proposal HTML
    html_content = build_proposal_html(cfg)

    # Use an ephemeral temporary HTML file that is strictly deleted in finally block
    temp_fd, temp_html_path = tempfile.mkstemp(suffix=".html", prefix=f"{slug}_proposal_")
    os.close(temp_fd)
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[*] Compiling modernized 8-page proposal PDF via Playwright -> {pdf_out_path.name}...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file:///{os.path.abspath(temp_html_path)}", wait_until="networkidle")
            page.pdf(
                path=str(pdf_out_path),
                format="Letter",
                print_background=True,
                margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"}
            )
            browser.close()
    finally:
        # Strictly delete temporary HTML
        if os.path.exists(temp_html_path):
            try:
                os.remove(temp_html_path)
            except Exception:
                pass

    # Programmatic Post-Flight Vault Sanitizer
    if client_vault_dir and client_vault_dir.exists():
        sanitize_client_vault(client_vault_dir)

    print(f"[SUCCESS] Modernized proposal PDF generated successfully: {pdf_out_path}")
    return str(pdf_out_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Executive Proposal Generator")
    parser.add_argument("--config", help="Path to proposal JSON config")
    parser.add_argument("--slug", help="Client slug (e.g. blueoasis)")
    parser.add_argument("--out", help="Output PDF filename")
    args = parser.parse_args()

    target = args.config if args.config else (args.slug if args.slug else "blueoasis")
    generate_proposal_pdf(target, args.out)
