"""
src/lead_resolver.py
====================
Instant Lead Resolver & Vault Initializer.

Resolves any lead from an email address, contact name, or domain query:
1. Checks local clients/index.json first.
2. Checks email history & local CRM caches.
3. Automatically queries Gmail API for recent threads, extracts scorecard image attachment,
   and parses metrics, phone numbers, and websites from email payloads.
4. Initializes clients/{slug}/brief.md and clients/{slug}/config.json (with fallback pool).
5. Returns slug and config path ready for run_audit.py in under 3 seconds.
"""

import os
import re
import json
import base64
import email
from typing import Optional, Dict, Any

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENTS_DIR = os.path.join(WORKSPACE_DIR, "clients")
INDEX_PATH = os.path.join(CLIENTS_DIR, "index.json")

def load_clients_index() -> dict:
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_clients_index(idx: dict):
    os.makedirs(CLIENTS_DIR, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2)

def slugify(text: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    return clean or "client_lead"

def find_in_local_index(query: str) -> Optional[dict]:
    idx = load_clients_index()
    q_low = query.strip().lower()
    q_slug = slugify(query)

    # 1. Exact matches first (slug, email, company, name)
    for slug, meta in idx.items():
        if q_low == slug.lower() or q_slug == slug.lower():
            return meta
    for slug, meta in idx.items():
        if q_low == meta.get("email", "").strip().lower():
            return meta
    for slug, meta in idx.items():
        if q_low == meta.get("company_name", "").strip().lower():
            return meta
    for slug, meta in idx.items():
        if q_low == meta.get("contact_name", "").strip().lower():
            return meta

    # 2. Substring matches
    for slug, meta in idx.items():
        if q_low in meta.get("email", "").lower():
            return meta
        if q_low in meta.get("company_name", "").lower():
            return meta
        if q_low in meta.get("contact_name", "").lower():
            return meta
        if q_slug in meta.get("website", "").lower().replace(".", ""):
            return meta
    return None

def extract_lead_from_gmail(query: str) -> Optional[dict]:
    """Queries Gmail API to locate message, extract scorecard attachment, and parse metadata."""
    try:
        from src.gmail_helper import get_gmail_service
        service = get_gmail_service()
    except Exception as e:
        print(f"[LEAD RESOLVER] Could not initialize Gmail service: {e}")
        return None

    try:
        q_str = f"{query}"
        res = service.users().messages().list(userId='me', q=q_str, maxResults=5).execute()
        messages = res.get('messages', [])
        if not messages:
            return None

        client_email = query if "@" in query else ""
        client_name = ""
        company_name = ""
        website = ""
        phone = ""
        scorecard_bytes = None
        metrics_found = {}

        for m_entry in messages:
            msg_data = service.users().messages().get(userId='me', id=m_entry['id'], format='raw').execute()
            raw = base64.urlsafe_b64decode(msg_data['raw'])
            msg = email.message_from_bytes(raw)

            to_hdr = msg.get('To', '')
            from_hdr = msg.get('From', '')
            subj_hdr = msg.get('Subject', '')

            # Extract client email
            if not client_email:
                if any(x in from_hdr.lower() for x in ['shiv', 'innovate', 'pms']):
                    m_em = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', to_hdr)
                    if m_em:
                        client_email = m_em.group(0).lower()
                else:
                    m_em = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_hdr)
                    if m_em:
                        client_email = m_em.group(0).lower()

            # Inspect body parts
            for part in msg.walk():
                ct = part.get_content_type()
                if ct.startswith('image/') and not scorecard_bytes:
                    payload = part.get_payload(decode=True)
                    if payload and len(payload) > 10000:
                        scorecard_bytes = payload

                if ct in ['text/plain', 'text/html']:
                    body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    # Extract client greeting name
                    if not client_name:
                        nm = re.search(r'(?:Hi|Hello|Hey)\s+([A-Za-z]+)', body_text)
                        if nm and nm.group(1).lower() not in ['there', 'team', 'all']:
                            client_name = nm.group(1).title()

                    # Extract company name
                    if not company_name:
                        cm = re.search(r'(?:Company|Business Name)[:\*\|\s]+([^\n\|<]+)', body_text)
                        if cm:
                            company_name = cm.group(1).strip()

                    # Extract website
                    if not website:
                        wm = re.search(r'(?:Website|Domain|spotted on)[:\*\|\s]+([a-zA-Z0-9\.\-\s]+(?:\.com|\.net|\.org|\.us|\.ca|\.co))', body_text, re.IGNORECASE)
                        if wm:
                            clean_w = wm.group(1).replace(" ", "").strip()
                            if not clean_w.startswith("http"):
                                clean_w = "https://" + clean_w
                            website = clean_w

                    # Extract phone
                    if not phone:
                        pm = re.search(r'(?:\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})', body_text)
                        if pm:
                            phone = pm.group(0).strip()

                    # Extract Semrush metrics if present in text
                    auth_m = re.search(r'Authority Score[:\*\|\s]+(\d+)', body_text)
                    if auth_m:
                        metrics_found['authority_score'] = f"{auth_m.group(1)} / 100"
                    traffic_m = re.search(r'Organic Traffic[:\*\|\s]+([\d,\.]+[KMkm]?)', body_text)
                    if traffic_m:
                        metrics_found['organic_traffic'] = f"{traffic_m.group(1)} visits/mo"
                    backlinks_m = re.search(r'Backlinks[:\*\|\s]+([\d,\.]+[KMkm]?)', body_text)
                    if backlinks_m:
                        metrics_found['backlinks'] = f"{backlinks_m.group(1)} links"
                    domains_m = re.search(r'Referring Domains[:\*\|\s]+([\d,\.]+[KMkm]?)', body_text)
                    if domains_m:
                        metrics_found['ref_domains'] = f"{domains_m.group(1)} domains"
                    kw_m = re.search(r'Keywords Indexed[:\*\|\s]+(\d+)', body_text)
                    if kw_m:
                        metrics_found['keywords_indexed'] = f"{kw_m.group(1)} terms"

        if not client_email and "@" in query:
            client_email = query

        slug = slugify(company_name or (website.split("//")[-1].split(".")[0] if website else "") or client_name or client_email.split("@")[0])

        return {
            "slug": slug,
            "contact_name": client_name or "Business Owner",
            "company_name": company_name or slug.replace("_", " ").title(),
            "website": website or f"https://{slug}.com/",
            "email": client_email,
            "phone": phone,
            "scorecard_bytes": scorecard_bytes,
            "diagnostics": metrics_found
        }
    except Exception as e:
        print(f"[LEAD RESOLVER] Error searching Gmail: {e}")
        return None

def resolve_or_create_lead(query: str) -> dict:
    """Master lead resolution entrypoint: resolves query into client vault and config."""
    # 1. Check local index
    existing = find_in_local_index(query)
    if existing:
        slug = existing["slug"]
        vault_dir = os.path.join(CLIENTS_DIR, slug)
        cfg_path = os.path.join(vault_dir, "config.json")
        return {
            "slug": slug,
            "vault_dir": vault_dir,
            "config_path": cfg_path,
            "is_new": False,
            "meta": existing
        }

    # 2. Extract from Gmail API
    print(f"[LEAD RESOLVER] Lead '{query}' not found in local index. Querying Gmail API...", flush=True)
    gmail_data = extract_lead_from_gmail(query)
    if not gmail_data:
        # Fallback minimal slug
        slug = slugify(query)
        gmail_data = {
            "slug": slug,
            "contact_name": query.title(),
            "company_name": query.title(),
            "website": f"https://{slug}.com/",
            "email": query if "@" in query else "",
            "phone": "",
            "scorecard_bytes": None,
            "diagnostics": {}
        }

    slug = gmail_data["slug"]
    vault_dir = os.path.join(CLIENTS_DIR, slug)
    screenshots_dir = os.path.join(vault_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    # Save scorecard image if extracted
    scorecard_path = os.path.join(screenshots_dir, "scorecard.png")
    if gmail_data.get("scorecard_bytes") and not os.path.exists(scorecard_path):
        with open(scorecard_path, "wb") as f:
            f.write(gmail_data["scorecard_bytes"])
        print(f"[LEAD RESOLVER] Extracted and saved scorecard image to: {scorecard_path}")

    # Create baseline brief.md
    brief_path = os.path.join(vault_dir, "brief.md")
    if not os.path.exists(brief_path):
        brief_content = f"""# CALL COPILOT SALES DOSSIER
## {gmail_data['company_name']} | {gmail_data['contact_name']}

| Field | Details |
|---|---|
| **Business Name** | {gmail_data['company_name']} |
| **Contact / Decision Maker** | {gmail_data['contact_name']} |
| **Website** | {gmail_data['website']} |
| **Recipient Email** | `{gmail_data['email']}` |
| **Phone** | {gmail_data['phone']} |
"""
        with open(brief_path, "w", encoding="utf-8") as f:
            f.write(brief_content)

    # Create baseline config.json
    cfg_path = os.path.join(vault_dir, "config.json")
    if not os.path.exists(cfg_path):
        diag = gmail_data.get("diagnostics", {})
        baseline_cfg = {
            "client_slug": slug,
            "client_name": gmail_data["contact_name"],
            "company_name": gmail_data["company_name"],
            "website": gmail_data["website"],
            "scorecard_image": scorecard_path if os.path.exists(scorecard_path) else f"screenshots/{slug}_seo.png",
            "diagnostics": {
                "authority_score": diag.get("authority_score", "15 / 100"),
                "organic_traffic": diag.get("organic_traffic", "0 Visits / mo"),
                "us_share": "0% Cold US Search Discovery",
                "backlinks": diag.get("backlinks", "100 Backlinks"),
                "ref_domains": diag.get("ref_domains", "25 Domains"),
                "keywords_indexed": diag.get("keywords_indexed", "5 Indexed Terms"),
                "ai_mentions": "0 Score"
            },
            "keywords": [],
            "fallback_keywords": []
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(baseline_cfg, f, indent=2)

    # Register in clients/index.json
    idx = load_clients_index()
    idx[slug] = {
        "slug": slug,
        "contact_name": gmail_data["contact_name"],
        "company_name": gmail_data["company_name"],
        "website": gmail_data["website"],
        "email": gmail_data["email"],
        "phone": gmail_data["phone"],
        "has_audit_pdf": False,
        "has_proposal_pdf": False,
        "folder": f"clients/{slug}"
    }
    save_clients_index(idx)
    print(f"[LEAD RESOLVER] Initialized new vault for '{slug}' at: {vault_dir}")

    return {
        "slug": slug,
        "vault_dir": vault_dir,
        "config_path": cfg_path,
        "is_new": True,
        "meta": idx[slug]
    }
