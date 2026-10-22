"""
Client Vault Manager
Centralized resolution, indexing, and management for client vaults in clients/{client_slug}/.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENTS_DIR = os.path.join(WORKSPACE_DIR, "clients")
INDEX_PATH = os.path.join(CLIENTS_DIR, "index.json")

def load_index() -> Dict[str, Any]:
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def resolve_client_vault(slug_or_query: str) -> Optional[str]:
    """
    Smart vault resolver. Resolves slug, company name, contact, domain, or email
    to the absolute directory path of the client's vault in clients/{client_slug}/.
    """
    if not slug_or_query:
        return None
    
    clean_query = str(slug_or_query).strip()
    
    # 1. Direct directory check in clients/{slug}
    direct = os.path.join(CLIENTS_DIR, clean_query)
    if os.path.isdir(direct):
        return direct
    
    # 2. Check slug normalized (lower, underscores, no special chars)
    slug_norm = re.sub(r'[^a-zA-Z0-9]', '', clean_query.lower())
    for entry in os.listdir(CLIENTS_DIR):
        entry_path = os.path.join(CLIENTS_DIR, entry)
        if os.path.isdir(entry_path):
            entry_norm = re.sub(r'[^a-zA-Z0-9]', '', entry.lower())
            if slug_norm == entry_norm:
                return entry_path

    # 3. Search index.json
    idx = load_index()
    if not idx:
        return None

    # Exact key match
    if clean_query.lower() in idx:
        cand = os.path.join(WORKSPACE_DIR, idx[clean_query.lower()]["folder"])
        if os.path.isdir(cand):
            return cand

    # Match by email, domain, company, or contact name
    q_low = clean_query.lower()
    for slug, meta in idx.items():
        if q_low == slug.lower():
            cand = os.path.join(WORKSPACE_DIR, meta["folder"])
            if os.path.isdir(cand):
                return cand
        
        email = meta.get("email", "").lower()
        if email and (q_low in email or email in q_low):
            cand = os.path.join(WORKSPACE_DIR, meta["folder"])
            if os.path.isdir(cand):
                return cand
                
        domain = meta.get("domain", "").lower()
        if domain and (slug_norm in domain.replace(".", "") or domain.replace(".", "") in slug_norm):
            cand = os.path.join(WORKSPACE_DIR, meta["folder"])
            if os.path.isdir(cand):
                return cand

        company = meta.get("company_name", "").lower()
        comp_norm = re.sub(r'[^a-zA-Z0-9]', '', company)
        if comp_norm and (slug_norm in comp_norm or comp_norm in slug_norm):
            cand = os.path.join(WORKSPACE_DIR, meta["folder"])
            if os.path.isdir(cand):
                return cand

    return None

def ensure_client_vault(slug: str) -> str:
    """Ensures that a client vault exists and has screenshots directory."""
    vault_dir = os.path.join(CLIENTS_DIR, slug)
    screenshots_dir = os.path.join(vault_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    return vault_dir

def get_client_paths(slug_or_query: str) -> Dict[str, str]:
    """Returns absolute paths to all standard assets for a client, prioritizing client-branded filenames."""
    vault = resolve_client_vault(slug_or_query)
    if not vault:
        vault = os.path.join(CLIENTS_DIR, slug_or_query)
    
    screenshots_dir = os.path.join(vault, "screenshots")
    clean_name = slug_or_query.replace("-", " ").replace("_", " ").title().replace(" ", "_")

    # Dynamic resolution for Audit PDF
    audit_pdf = os.path.join(vault, f"{clean_name}_Google_Search_Audit.pdf")
    if os.path.exists(vault):
        for f in os.listdir(vault):
            if f.endswith(".pdf") and ("audit" in f.lower() or "search_audit" in f.lower()):
                audit_pdf = os.path.join(vault, f)
                break

    # Dynamic resolution for Proposal PDF
    proposal_pdf = os.path.join(vault, f"{clean_name}_SEO_AI_Visibility_Proposal.pdf")
    if os.path.exists(vault):
        for f in os.listdir(vault):
            if f.endswith(".pdf") and ("proposal" in f.lower() or "visibility" in f.lower()) and "old" not in f.lower():
                proposal_pdf = os.path.join(vault, f)
                break

    # Dynamic resolution for Scorecard
    scorecard_png = os.path.join(screenshots_dir, f"{clean_name}_Semrush_Scorecard.png")
    if os.path.exists(screenshots_dir):
        for f in os.listdir(screenshots_dir):
            if f.endswith(".png") and ("scorecard" in f.lower() or "seo" in f.lower()):
                scorecard_png = os.path.join(screenshots_dir, f)
                break

    return {
        "vault_dir": vault,
        "config_json": os.path.join(vault, "config.json"),
        "proposal_config_json": os.path.join(vault, "proposal_config.json"),
        "brief_md": os.path.join(vault, "brief.md"),
        "screenshots_dir": screenshots_dir,
        "scorecard_png": scorecard_png,
        "audit_pdf": audit_pdf,
        "proposal_pdf": proposal_pdf
    }

def search_clients(query: str) -> List[Dict[str, Any]]:
    """Fast search across all indexed clients."""
    idx = load_index()
    results = []
    q = query.lower().strip()
    q_norm = re.sub(r'[^a-zA-Z0-9]', '', q)
    
    for slug, meta in idx.items():
        score = 0
        slug_norm = re.sub(r'[^a-zA-Z0-9]', '', slug.lower())
        if q_norm and q_norm == slug_norm:
            score += 100
        elif q_norm and (q_norm in slug_norm or slug_norm in q_norm):
            score += 60
        elif q in slug.lower():
            score += 50
            
        company = meta.get("company_name", "").lower()
        if q in company:
            score += 60
        elif q_norm and q_norm in re.sub(r'[^a-zA-Z0-9]', '', company):
            score += 45
            
        contact = (meta.get("contact_name", "") or meta.get("client_name", "")).lower()
        if q in contact:
            score += 50
        elif q_norm and q_norm in re.sub(r'[^a-zA-Z0-9]', '', contact):
            score += 40
            
        email = meta.get("email", "").lower()
        if q in email or (q_norm and q_norm in re.sub(r'[^a-zA-Z0-9]', '', email)):
            score += 70
            
        domain = meta.get("domain", "").lower()
        if q in domain or (q_norm and q_norm in re.sub(r'[^a-zA-Z0-9]', '', domain)):
            score += 60
            
        if score > 0:
            res = meta.copy()
            res["match_score"] = score
            res["vault_path"] = os.path.join(WORKSPACE_DIR, meta["folder"])
            results.append(res)
            
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Searching vaults for '{query}'...")
        matches = search_clients(query)
        if matches:
            print(f"Found {len(matches)} match(es):")
            for m in matches[:10]:
                contact = m.get('contact_name') or m.get('client_name') or 'N/A'
                print(f"  • [{m['slug']}] {m['company_name']} ({contact}) -> {m['vault_path']}")
        else:
            print("No matching clients found.")
    else:
        print("Usage: python -m src.vault_manager <query>")
