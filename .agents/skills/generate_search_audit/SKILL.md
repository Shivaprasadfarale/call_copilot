---
name: generate-search-audit
description: Generate visual Google Search Audit PDFs (22 or 23 pages), proof sheets, and delivery email copy in 60 to 90 seconds using the automated pipeline.
---

# Generate Search Audit Skill

## STRICT PERFORMANCE BENCHMARK & GUARANTEE
* **Vaulted Leads (Config & Scorecard already exist):** **60 to 75 SECONDS.**
* **Fresh Unvaulted Leads (Intake + Audit + PDF):** **< 90 SECONDS (under 2 minutes maximum).**
* **ZERO SCRATCH SCRIPTS:** Never write custom exploration or scrape scripts. All operations run through `run_intake.py` and `run_audit.py`.

## The 6 Permanent Technical Safeguards (Zero Heuristic Failures)
1. **Native DOM Pagination Coordinates:** Uses native CDP DOM elements (`table[role="presentation"]`, `#pnnext`, `#botstuff`) instead of fragile pixel RGB matching. Immune to Dark Mode, high-contrast themes, and Google color changes.
2. **Strict Entity Presence Gate:** Only matches exact client domain (`cite`, `href`) or exact full company name in Map Pack listing headings. Eliminates false positives from generic industry word collisions.
3. **Pre-Scroll Hydration Buffer:** Automatically scrolls to page bottom and back before taking full-page screenshots to force lazy-loaded search results and AI Overviews to render completely without gaps.
4. **Multi-Word City Regex & Multi-Token Suffix Stripping:** Suffix token cleaning (`desert`, `hot`, `rancho`, `north`) guarantees zero grammar mangling like `desert hot redding ca`. SoCal/NorCal regional hub routing ensures local relevance.
5. **Universal UTF-8 Terminal Configuration:** All scripts explicitly reconfigure `sys.stdout` to UTF-8 on launch to prevent Windows `cp1252` charmap crashes.
6. **Self-Healing Config & Keyword Synthesis:** `run_audit.py` automatically synthesizes 10 commercial keywords from `brief.md` if missing, completely eliminating upfront manual fumbling or JSON editing.

## The Standard Dual-Track Lead Workflow

### Track 1: Fresh Lead Intake & Scorecard Draft (< 45 Seconds)
Use this for every fresh prospect who replied "Yes" or asked for errors/scorecard:
1. **Intake Gate (< 10s):**
   ```bash
   python run_intake.py --lead "[paste lead text]"
   ```
2. **Semrush Capture:** Save clean white-label scorecard to `clients/{slug}/screenshots/scorecard.png`.
3. **Auto-Inject Scorecard Draft (< 5s):**
   ```bash
   python run_scorecard_draft.py --slug [slug]
   ```
   * Auto-extracts exact metrics via OCR, verifies 100% metric parity, docks into Gmail thread with native quote block, embeds scorecard inline, and returns live Draft ID.

### Track 2: 22-Page Visual Search Audit PDF & Proof Sheet (60 to 75 Seconds)
Use this when visual proof across 10 search queries is requested, or when prospect challenges ranking:
1. **Run Master Audit:**
   ```bash
   python run_audit.py --slug [slug]
   ```
   *(Add `--force` only if you need to re-capture screenshots from scratch via active Chrome CDP on port 9222).*
2. **Deliver Master PDF & Live Draft:**
   * Output: `clients/{slug}/[ClientName]_Google_Search_Audit.pdf` (22 pages, full-bleed A4, stacked headers).
   * 1-Page Proof Sheet: `clients/{slug}/proof_sheet.png`.
   * Automatically creates the live Gmail draft with the PDF attached and scorecard inline.

