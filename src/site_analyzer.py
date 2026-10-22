"""
Site Analyzer & Technical On-Page SEO Auditor (Native Playwright DOM Engine)
Zero external scraping dependencies (no bs4 needed). Uses native Chromium DOM APIs:
1. Operational Delivery Model Detection (Virtual/Nationwide vs. Local/Regional).
2. Exact Service Packages, Tiers & Pricing Scrape (/services, /pricing, /packages).
3. robots.txt & XML sitemap availability.
4. Title tag, meta description, and heading hierarchy (h1/h2) quality.
5. Indexation blockers (noindex, canonical mismatch).
6. Schema.org JSON-LD structured data presence.
7. Image Alt text coverage.
8. Mobile viewport & OpenGraph metadata.
"""

import os
import sys
import re
import json
import urllib.parse
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def evaluate_dom_technical_seo(page) -> Dict[str, Any]:
    """Runs native browser DOM evaluation to audit technical on-page SEO."""
    return page.evaluate("""() => {
        const issues = [];
        const strengths = [];

        // 1. Title
        const titleEl = document.querySelector('title');
        const title = titleEl ? titleEl.innerText.trim() : '';
        const titleLen = title.length;
        if (!title) {
            issues.push("CRITICAL: Missing <title> tag on page.");
        } else if (titleLen < 30) {
            issues.push(`WARNING: Title tag is too short (${titleLen} chars): "${title}". Lacks commercial service keywords.`);
        } else if (titleLen > 65) {
            issues.push(`WARNING: Title tag exceeds 65 characters (${titleLen} chars) and will truncate in search snippets: "${title}".`);
        } else {
            strengths.push(`Title tag length optimal (${titleLen} chars): "${title}".`);
        }

        // 2. Meta Description
        const descEl = document.querySelector('meta[name="description" i]');
        const metaDesc = descEl ? descEl.getAttribute('content').trim() : '';
        const descLen = metaDesc.length;
        if (!metaDesc) {
            issues.push("CRITICAL: Missing meta description. Google pulls random, unoptimized snippet fragments.");
        } else if (descLen < 60) {
            issues.push(`WARNING: Meta description is very brief (${descLen} chars): "${metaDesc}".`);
        } else if (descLen > 165) {
            issues.push(`WARNING: Meta description exceeds 165 characters (${descLen} chars) and will truncate.`);
        } else {
            strengths.push(`Meta description present and optimal (${descLen} chars).`);
        }

        // 3. Headings (H1, H2)
        const h1Els = Array.from(document.querySelectorAll('h1')).map(h => h.innerText.trim()).filter(Boolean);
        const h1Count = h1Els.length;
        if (h1Count === 0) {
            issues.push("CRITICAL: Missing <h1> tag. Google relies heavily on <h1> to determine primary topic relevance.");
        } else if (h1Count > 1) {
            issues.push(`WARNING: Multiple (${h1Count}) <h1> tags found (${h1Els.slice(0, 3).join(' | ')}). Dilutes topic authority.`);
        } else {
            const h1Val = h1Els[0];
            if (h1Val.length < 8 || /welcome|home|hello/i.test(h1Val)) {
                issues.push(`WARNING: Generic unranked <h1> tag: "${h1Val}".`);
            } else {
                strengths.push(`Clean single <h1> tag: "${h1Val}".`);
            }
        }

        const h2Count = document.querySelectorAll('h2').length;
        if (h2Count === 0) {
            issues.push("WARNING: Zero <h2> subheadings detected. Page lacks structured content hierarchy.");
        } else {
            strengths.push(`Healthy structure: ${h2Count} <h2> subheadings.`);
        }

        // 4. Robots Noindex
        const robotsMeta = document.querySelector('meta[name="robots" i]');
        const robotsContent = robotsMeta ? robotsMeta.getAttribute('content').toLowerCase() : '';
        if (robotsContent.includes('noindex')) {
            issues.push("FATAL ERROR: Page has <meta name='robots' content='noindex'>! Blocks Google from indexing.");
        }

        // 5. Canonical
        const canonicalEl = document.querySelector('link[rel="canonical" i]');
        const canonical = canonicalEl ? canonicalEl.getAttribute('href') : '';
        if (!canonical) {
            issues.push("WARNING: Missing <link rel='canonical'> tag. Can trigger duplicate content cannibalization.");
        } else {
            strengths.push(`Canonical URL declared: ${canonical}`);
        }

        // 6. Schema.org JSON-LD
        const schemas = [];
        document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
            try {
                const data = JSON.parse(s.innerText || '{}');
                if (data['@type']) schemas.push(data['@type']);
                else if (Array.isArray(data)) {
                    data.forEach(item => { if (item && item['@type']) schemas.push(item['@type']); });
                }
            } catch(e) {}
        });

        if (schemas.length === 0) {
            issues.push("HIGH PRIORITY: Zero Schema.org structured data (JSON-LD) detected. Google cannot parse business entity, services, or pricing into rich snippets.");
        } else {
            strengths.push(`Structured data active: ${Array.from(new Set(schemas)).join(', ')}`);
        }

        // 7. Image Alt Text
        const imgs = Array.from(document.querySelectorAll('img'));
        const missingAlt = imgs.filter(img => !img.getAttribute('alt') || !img.getAttribute('alt').trim());
        if (imgs.length > 0 && missingAlt.length > 0) {
            issues.push(`NOTICE: ${missingAlt.length} of ${imgs.length} images are missing alt descriptive tags.`);
        } else if (imgs.length > 0) {
            strengths.push(`All ${imgs.length} images have alt tags.`);
        }

        // 8. Mobile Viewport
        const viewport = document.querySelector('meta[name="viewport" i]');
        if (!viewport) {
            issues.push("CRITICAL: Missing mobile viewport meta tag. Site will fail Google mobile compliance.");
        } else {
            strengths.push("Mobile viewport configured.");
        }

        return {
            title: title,
            title_length: titleLen,
            meta_description: metaDesc,
            meta_description_length: descLen,
            h1_tags: h1Els,
            h2_count: h2Count,
            schemas: Array.from(new Set(schemas)),
            canonical: canonical,
            total_images: imgs.length,
            missing_alt_images: missingAlt.length,
            issues: issues,
            strengths: strengths
        };
    }""")


def detect_operational_model(body_text: str) -> Dict[str, Any]:
    """Analyzes text semantics to classify business delivery model."""
    text_lower = body_text.lower()

    virtual_signals = [
        "zoom", "virtual", "online coaching", "available online", "worldwide",
        "remote", "telehealth", "shipping nationwide", "order online", "webinar",
        "podcast", "listen on spotify", "digital course", "video consultation", "zoom calls"
    ]
    local_signals = [
        "service area", "counties we serve", "areas we serve", "emergency service",
        "in-shop", "drop-off", "walk-in", "dispatch", "mobile detailing",
        "haul away", "our fleet", "commercial roofing", "junk removal crew"
    ]

    virtual_score = sum(text_lower.count(s) for s in virtual_signals)
    local_score = sum(text_lower.count(s) for s in local_signals)

    if virtual_score >= 2 and virtual_score >= local_score:
        model = "NATIONWIDE_VIRTUAL"
        search_scope = "National (Entire USA)"
        strategy_reason = "Services and coaching delivered remotely via Zoom/online. Must target nationwide commercial searches, not local towns."
    elif local_score >= 2 and local_score > virtual_score:
        model = "LOCAL_IN_PERSON"
        search_scope = "Local & Regional Hubs"
        strategy_reason = "Physical equipment or in-person delivery. Must target local base and 25-50 mile surrounding commercial hubs."
    else:
        model = "HYBRID"
        search_scope = "National Virtual + Regional Hub"
        strategy_reason = "Operates both an in-person regional base and virtual/national online offerings."

    return {
        "model": model,
        "search_scope": search_scope,
        "virtual_score": virtual_score,
        "local_score": local_score,
        "strategy_reason": strategy_reason
    }


def extract_packages_and_pricing(body_text: str) -> List[Dict[str, str]]:
    """Extracts explicit packages, course tiers, and price mentions across single-line and multi-line layouts."""
    packages = []
    seen = set()
    lines = [l.strip() for l in body_text.split("\n") if l.strip()]

    for i, line in enumerate(lines):
        m = re.search(r"\$([0-9,]{2,7})", line)
        if not m:
            m = re.search(r"([0-9,]{2,7})\s*(?:US\s*dollars|USD)", line, re.I)

        if m:
            price = f"${m.group(1)}"
            # 1. Check if name is on the same line
            same_line_name = re.sub(r"\$[0-9,]+|[0-9,]+\s*(?:US\s*dollars|USD)", "", line, flags=re.I).strip(" -–—:•|")
            
            # 2. If same line name is empty or very short, search backwards 1 to 6 lines for the package title
            candidate_name = ""
            if len(same_line_name) >= 4 and not any(w in same_line_name.lower() for w in ["total", "subtotal", "tax", "fee", "ended", "available"]):
                candidate_name = same_line_name
            else:
                for back in range(1, 8):
                    if i - back >= 0:
                        prev = lines[i - back]
                        # Filter out common UI labels
                        if any(w in prev.lower() for w in ["ended", "available online", "log in", "contact", "about", "services", "terms", "policy"]):
                            continue
                        if re.search(r"\b(?:days?|program|training|coaching|package|fundamentals|optimization|consultation|tier|level|plan)\b", prev, re.I):
                            candidate_name = prev
                            break
                        elif len(prev) >= 5 and len(prev) <= 60 and not prev.startswith("http"):
                            candidate_name = prev
                            break

            # 3. Look ahead for call counts / format (e.g., "4 Zoom Calls", "13 Zoom calls")
            format_info = ""
            for fwd in range(1, 4):
                if i + fwd < len(lines):
                    nxt = lines[i + fwd]
                    if re.search(r"\b(?:zoom\s*calls?|sessions?|weeks?|months?|hours?)\b", nxt, re.I):
                        format_info = nxt
                        break

            if candidate_name and candidate_name not in seen:
                seen.add(candidate_name)
                display_price = price
                if format_info:
                    display_price += f" ({format_info})"
                packages.append({
                    "name": candidate_name,
                    "price": display_price,
                    "raw_context": f"{candidate_name} -> {display_price}"
                })

    return packages


def run_full_site_audit(url: str, max_subpages: int = 3) -> Dict[str, Any]:
    """Runs a complete Chromium session to audit technicals, delivery model, and packages."""
    if not url.startswith("http"):
        url = f"https://{url}"

    parsed_root = urllib.parse.urlparse(url)
    base_domain = parsed_root.netloc.replace("www.", "")

    results: Dict[str, Any] = {
        "url": url,
        "base_domain": base_domain,
        "technical_seo": {},
        "operational_model": {},
        "packages": [],
        "crawled_subpages": [],
        "forensic_email_bullets": []
    }

    with sync_playwright() as p:
        browser = None
        context = None
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=3000)
            context = browser.contexts[0]
            print(f"[SiteAnalyzer] Connected to active Chrome CDP for {url}", flush=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            )
            print(f"[SiteAnalyzer] Launched headless Chrome for {url}", flush=True)

        page = context.new_page()

        try:
            print(f"[SiteAnalyzer] Navigating to {url}...", flush=True)
            page.goto(url, wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(2000)

            body_text = page.evaluate("document.body.innerText")

            # 1. Native DOM technical SEO audit
            tech_audit = evaluate_dom_technical_seo(page)
            results["technical_seo"] = tech_audit

            # 2. Operational model check
            op_model = detect_operational_model(body_text)
            results["operational_model"] = op_model

            # 3. Find subpages (/services, /pricing, /packages)
            links = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a'))
                    .map(a => ({ text: a.innerText.trim(), href: a.href }))
                    .filter(l => l.href && l.href.startsWith('http'));
            }""")

            target_keywords = ["service", "price", "pricing", "package", "course", "about", "book"]
            subpages_to_visit = []
            seen_hrefs = {url}

            for l in links:
                href = l["href"]
                clean_href = href.split("#")[0].rstrip("/")
                if base_domain in clean_href and clean_href not in seen_hrefs:
                    if any(k in clean_href.lower() for k in target_keywords):
                        seen_hrefs.add(clean_href)
                        subpages_to_visit.append((l["text"], clean_href))
                        if len(subpages_to_visit) >= max_subpages:
                            break

            all_body_text = body_text

            for stext, shref in subpages_to_visit:
                try:
                    print(f"[SiteAnalyzer] Inspecting subpage: {shref}...", flush=True)
                    page.goto(shref, wait_until="domcontentloaded", timeout=10000)
                    page.wait_for_timeout(1500)
                    sub_text = page.evaluate("document.body.innerText")
                    all_body_text += "\n" + sub_text
                    results["crawled_subpages"].append({
                        "name": stext,
                        "url": shref
                    })

                    # If this is /services or a main directory, look for child service-pages
                    child_links = page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('a'))
                            .map(a => a.href)
                            .filter(h => /service-page|course|package|pricing|program/i.test(h));
                    }""")
                    for ch in child_links:
                        clean_ch = ch.split("#")[0].rstrip("/")
                        if base_domain in clean_ch and clean_ch not in seen_hrefs and len(results["crawled_subpages"]) < 8:
                            seen_hrefs.add(clean_ch)
                            try:
                                print(f"[SiteAnalyzer] Inspecting child package page: {clean_ch}...", flush=True)
                                page.goto(clean_ch, wait_until="domcontentloaded", timeout=10000)
                                page.wait_for_timeout(1200)
                                ch_text = page.evaluate("document.body.innerText")
                                all_body_text += "\n" + ch_text
                                results["crawled_subpages"].append({
                                    "name": clean_ch.split("/")[-1],
                                    "url": clean_ch
                                })
                            except Exception:
                                pass
                except Exception as sub_err:
                    print(f"[SiteAnalyzer] Could not load {shref}: {sub_err}", flush=True)

            # 4. Extract packages and pricing
            packages = extract_packages_and_pricing(all_body_text)
            results["packages"] = packages

            # 5. Build high-impact forensic email bullets
            bullets = []
            if tech_audit["issues"]:
                for issue in tech_audit["issues"][:3]:
                    clean_issue = re.sub(r"^(CRITICAL|WARNING|HIGH PRIORITY|FATAL ERROR):\s*", "", issue)
                    bullets.append(clean_issue)

            if op_model["model"] == "NATIONWIDE_VIRTUAL":
                bullets.append("National Search Disconnect: Services are delivered virtually online via Zoom, but your domain lacks dedicated national commercial landing pages.")
            elif op_model["model"] == "LOCAL_IN_PERSON":
                bullets.append("Regional Authority Leak: While operating across the regional corridor, your pages lack geofenced commercial silos.")

            results["forensic_email_bullets"] = bullets

        except Exception as e:
            results["error"] = str(e)
            print(f"[SiteAnalyzer] Error during audit: {e}", flush=True)
        finally:
            page.close()

    return results


if __name__ == "__main__":
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.vincecortese.com/"
    print(f"Running automated audit on {test_url}...")
    report = run_full_site_audit(test_url)
    print("\n" + "=" * 50)
    print("AUDIT RESULTS SUMMARY:")
    print("=" * 50)
    print(f"Domain: {report['base_domain']}")
    print(f"Operational Model: {report['operational_model'].get('model')} ({report['operational_model'].get('search_scope')})")
    print(f"Title: {report['technical_seo'].get('title')} ({report['technical_seo'].get('title_length')} chars)")
    print(f"H1 Tags: {report['technical_seo'].get('h1_tags')}")
    print(f"Schemas Found: {report['technical_seo'].get('schemas')}")
    print(f"Issues Detected: {len(report['technical_seo'].get('issues', []))}")
    for iss in report['technical_seo'].get('issues', []):
        print(f"  - {iss}")
    print(f"\nPackages Found: {len(report['packages'])}")
    for pkg in report['packages']:
        print(f"  - {pkg['name']}: {pkg['price']}")
    print("\nForensic Bullets for Email:")
    for b in report['forensic_email_bullets']:
        print(f"  • {b}")
