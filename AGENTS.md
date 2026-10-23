# Client Lead Outreach & Audit SOP (Standard Operating Procedures)

These rules are strictly followed whenever the user provides client lead information (PMS screenshot, client name, email, website URL, or email thread).

================================================================================
🚨 MASTER RUNBOOK FOR EVERY LEAD IN EVERY NEW CHAT (ZERO AMNESIA STANDARD)
================================================================================
When a new lead arrives in ANY chat, the agent MUST NEVER guess, invent scratch scripts, or default to generic assumptions. Follow these two distinct, purpose-built tracks strictly:

--------------------------------------------------------------------------------
TRACK 1: FRESH LEAD INTAKE & SCORECARD DRAFT (< 45 SECONDS TOTAL TURNAROUND)
--------------------------------------------------------------------------------
Use this whenever a fresh prospect replies "Yes" or requests the report/errors:

### STEP 1: RUN PRE-FLIGHT INTAKE (Takes < 10 seconds)
```bash
python run_intake.py --lead "[paste lead text or email conversation]"
```
* **Auto-Checks Domain Disambiguation:** Distinguishes email host from operating site and secondary platforms.
* **Auto-Classifies Delivery Model:** `NATIONWIDE_VIRTUAL` (Zoom, coaching, digital) vs. `LOCAL_IN_PERSON` (trades, clinic, fleet).
* **Auto-Scrapes Real Packages & Pricing:** Extracts exact dollar tiers ($397, $1,191, $3,582) and Zoom formats directly from live site.
* **Auto-Generates 10 Smart Keywords:** 100% nationwide queries for virtual leads; regional economic hubs for local leads.

### STEP 2: SEMRUSH SCORECARD CAPTURE
* Save clean white-label scorecard to `clients/{slug}/screenshots/scorecard.png`.
* Retain top domain bar (`Domain Overview: domain.com`).

### STEP 3: AUTO-INJECT SCORECARD DRAFT TO GMAIL (< 5 seconds)
```bash
python run_scorecard_draft.py --slug [client_slug]
```
* **Performance Guarantee:** Auto-extracts exact metrics via OCR (Authority Score, Traffic, US %, Backlinks, Ref Domains, Keywords), validates 100% metric parity, verifies salutation consistency, docks into existing Gmail conversation thread with native quote block, embeds scorecard inline, and outputs live Gmail Draft ID in **under 5 seconds**!

--------------------------------------------------------------------------------
TRACK 2: 22-PAGE VISUAL SEARCH AUDIT PDF & PROOF SHEET (60 TO 75 SECONDS)
--------------------------------------------------------------------------------
Use this whenever the prospect challenges ranking, asks for visual proof, or when the user explicitly requests the 22-page PDF:

```bash
python run_audit.py --slug [client_slug]
```
* **Performance Guarantee:** Completes all 10 keyword Google captures via CDP port 9222, verifies absence, compiles the 22-page PDF, generates the 1-page visual proof sheet, formats both email tracks, and automatically creates the live Gmail draft with the PDF attached in **60 to 75 seconds**.
* **6 Permanent Technical Safeguards:**
  1. *Native DOM Pagination Coordinates:* Replaced pixel color heuristics with native CDP layout coords (`table[role="presentation"]`, `#pnnext`, `#botstuff`). Immune to Dark Mode.
  2. *Strict Entity Presence Gate:* Matches exact domain in URLs or full company name in map pack headings only. Zero false positives from generic words.
  3. *Pre-Scroll Hydration Buffer:* Forced page scroll-to-bottom and back ensures all dynamic search results and AI Overviews render completely before capture.
  4. *Multi-Word City Regex & Multi-Token Suffix Stripping:* Suffix token cleaning (`desert`, `hot`, `rancho`, `north`) guarantees zero grammar mangling like `desert hot redding ca`. SoCal/NorCal regional hub routing ensures local relevance.
  5. *Universal UTF-8 Output:* UTF-8 stdout reconfiguration prevents Windows `cp1252` encoding crashes.
  6. *Self-Healing Config & Keyword Synthesis:* `run_audit.py` automatically synthesizes 10 commercial keywords from `brief.md` if missing, completely eliminating upfront manual fumbling or JSON editing.
================================================================================

---

## 1. Semrush Capture Rules (Clean White-Label Only)
* **Target Elements:** Navigate to the client's Semrush Domain Overview.
* **Cropping Standard:**
  * Capture **ONLY** the data scorecards: the **AI Search** card and the **SEO** metrics card (Authority Score, Organic Traffic, Keywords, Referring Domains, Backlinks), or the **Organic Search Traffic Trend Graph**.
  * **STRICT PROHIBITION:** Never include the Semrush left sidebar, top browser URL/address bar, Semrush logos, or extra page clutter. The image must look clean, crisp, and neutral (white-label information card).
* **Save Location:** Save locally as `screenshots/{client_slug}_seo.png`.

---

## 1.1 Strict 100% Metric-Scorecard Parity Guardrail (Automated Programmatic Gate)
* **NEVER GUESS, ESTIMATE, OR MANUALLY WRITE METRIC NUMBERS:**
  * Every single number in the email text (Domain Authority, Organic Traffic, Backlinks, Referring Domains, Indexed Keywords, AI Visibility) MUST match the attached scorecard screenshot 1:1.
* **PROGRAMMATIC PRE-FLIGHT VALIDATION:**
  * Draft injection via `src/gmail_helper.py` strictly invokes `src/scorecard_validator.py` on the scorecard image before creating any Gmail draft.
  * If ANY number in the HTML text diverges from the OCR extraction of the image, the script raises a fatal `ValueError` and **refuses to touch the Gmail API**. Draft creation is completely blocked until the text is corrected.
  * **STRICT PROHIBITION ON BYPASSING THE GATE:** All draft injections must exclusively go through `create_gmail_draft()` in `src/gmail_helper.py`. Directly calling `service.users().drafts().create()` in ad-hoc scripts is strictly prohibited because it bypasses the validation gate.

---

## 2. Knowledge Base & Call Copilot Brief
* **Identity Rules (STRICT):**
  * **Outreach Persona & Email Identification (STRICT):**
    * ALWAYS identify the **actual outreach email account and persona** from which our cold email was sent to the client and which the client replied to (e.g., `Jessica <jessicafletcher1947@gmail.com>`, `Joan <joangill983@gmail.com>`, `Sandra <sandrawagner120@gmail.com>`).
    * **STRICT PROHIBITION ON PMS COORDINATOR NAMES:** The name in the PMS header (e.g., `Client Business | SEO | Yatendra` or `Arvind Rajput`, `Geeta`, `Sachin`, `Pawan`, `Ankit`, `Deepak`, `Prem`, `Abhishek`, `Amit`, `Rohit`, `Yogesh`) is strictly an internal account/coordinator uploader. **NEVER** use or mention these PMS coordinator names to the client, in email copy, in call scripts, in voicemails, or in Cockpit's Outreach Origin column. If you tell a client "you replied to Arvind / Yatendra", they will be confused because they never received an email from them. Always refer to the persona they actually received an email from (e.g., `Jessica`).
  * **Client Name:** Extract the actual decision maker/client who replied (e.g., `Gabriela` or `Ellen`). Address emails and call scripts to the client, referring to the outreach persona (e.g., `Jessica`) as your colleague.
* Automatically extract:
  * Client Contact Name, Company Name, Website, Contact Email, Phone, Location/Timezone, Domain Metrics.
* Identify high-ticket service opportunities for their specific niche and geography.
* Save the full briefing to: `knowledge_base/leads/{client_slug}.md` for immediate use in live calls.

---

## 2.0 Mandatory Forensic Intake & On-Page Technical Audit Standard (`src/site_analyzer.py`)
To prevent ever misdiagnosing a business model, service radius, or pricing structure, every single newly vaulted lead MUST be processed through `src/site_analyzer.py` before any search audit PDF is assembled or email copy is generated.

### The 5-Point Mandatory Forensic Intake Checklist:
1. **Identity & Domain Disambiguation:**
   * Verify if the domain in the PMS ticket is the client's actual operating platform, or merely an email-only host, subsidiary, or 3rd-party directory profile (e.g. Remake Learning, Crunchbase). Traces and audits ALL active sister platforms (e.g., main coaching site + podcast platform).
2. **Operational Delivery Model Classification (Zero Assumptions Gate):**
   * Programmatically classify fulfillment:
     * `NATIONWIDE_VIRTUAL` (Zoom calls, remote coaching, SaaS, national shipping, digital courses) -> **MANDATORY:** Target 100% NATIONWIDE commercial queries (`online mindset coach`, `virtual performance coach`). **STRICT PROHIBITION ON LOCAL CITY GEOFENCING.**
     * `LOCAL_IN_PERSON` (Contractor, mobile detailer, dentist, junk removal, clinic) -> Target local base + 25-50 mile surrounding economic hubs.
     * `HYBRID` (Local physical headquarters + national virtual Zoom coaching/keynotes).
3. **Exact Package, Cohort & Pricing Extraction:**
   * Deeply crawl `/services`, `/pricing`, `/packages`, `/booking-calendar`, and child `/service-page/` links.
   * Extract exact named tiers (e.g., "30 Days - Fundamentals", "90 Days Basic Training", "180 Days Performance Optimization") and exact price tags ($397, $1,191, $3,582) and delivery format (e.g., 4 Zoom Calls, 13 Zoom calls).
   * **STRICT PROHIBITION ON FABRICATING PRICING:** When real packages exist on the site, use them 1:1 in briefings, call scripts, and email copy.
4. **Semrush-Grade Technical On-Page Diagnostic:**
   * Check `robots.txt` & XML sitemap availability.
   * Check `<title>` length (<30 chars too short, >65 chars truncated) and keyword density.
   * Check `<meta name="description">` presence and length.
   * Check `<h1>` hierarchy (flags missing `<h1>`, multiple `<h1>`, or generic unranked text like "Home").
   * Check `Schema.org` JSON-LD structured data (`LocalBusiness`, `Organization`, `Service`, `Course`, `Person`).
   * Check image `alt` attributes and mobile viewport compliance.
5. **Dossier & Config Synchronization:**
   * Feed verified packages, operational model, and technical on-page bullets directly into `clients/{client_slug}/config.json` and `brief.md`.

---

## 2.1 Strict Thread-Salutation & Identity Guardrail (Automated Programmatic Gate)
* **NEVER SWITCH NAMES MID-THREAD OR RELY ON UNVERIFIED NAME CACHES:**
  * When following up inside an existing email thread, the recipient's greeting name MUST match the salutation previously used in that thread 1:1.
  * You cannot address someone as "Mr. Garcia" in one email and then switch to "Leticia" or any other name in a follow-up.
* **PROGRAMMATIC PRE-FLIGHT VALIDATION:**
  * `create_gmail_draft()` in `src/gmail_helper.py` strictly calls `validate_thread_salutation_consistency()` on the target thread before creating any draft.
  * The gate inspects the thread's previously sent messages, extracts the previous addressee name, and verifies it against the new draft's greeting.
  * If ANY contradiction is detected between the new draft greeting and the previous sent email greeting, the script raises a fatal `ValueError` and **refuses to touch the Gmail API**. Draft creation is completely halted until the name is corrected.
  * For fresh outreach, the client name is strictly cross-referenced against `knowledge_base/leads/{client_slug}.md` or the client's explicit signature block.

---

### 3. Email Copy Standard (Open Loop Report-Delivery Format)
Deliver a substantive technical audit answering the client's request to our outreach colleague. The report delivers the promised diagnostic data, scorecard, and competitor callout — but uses an **Open Loop** strategy: present 2 out of 3 findings clearly, then hold the 3rd finding behind a simple business-specific question only the prospect can answer. This creates an information gap that compels a reply.

**CORE PRINCIPLE:** The email's ONLY job is to get a reply. NOT to close a deal. NOT to book a meeting. Just get them to reply with 1 sentence. Everything else (pricing, calls, pitching) happens AFTER they reply.

1. **The Direct Colleague Handoff Opener:**
   * Open directly connecting the handoff from your outreach colleague:
     > *"Hi [Client Name],*  
     > *My colleague [Colleague Name] forwarded me your reply asking us to send over the website report and errors we spotted on [website . com]:"*

2. **Anti-Spam Quoted Header & Strict Anti-Autolink Rules:**
   * Include the **client's reply email ONLY** in a 4-sided grey box (`#fafafa` bg, `#d1d5db` border, monospace font).
   * **CRITICAL: The quoted box must contain ONLY the client's reply** — their From/Sent/To/Subject headers, their message body, and their signature/contact info. NEVER include the original cold email that our marketing team sent to them.
   * **STRICT PROHIBITION — NO CONTIGUOUS LINKS OR PROTOCOLS EVER:**
     * **NEVER** write `https://`, `http://`, `mailto:`, or trailing slashes (`/`) in the quoted header or anywhere in the email body. ALWAYS completely strip `https://` and `http://`.
     * **MANDATORY SPACES AROUND ALL DOTS AND `@` SYMBOLS:**
       * URLs/domains must ALWAYS have spaces around EVERY dot (e.g., `www . domain . com` or `domain . com`). NEVER write `www.domain.com` and NEVER write `https://www . domain . com` or `https://www`.
       * Email addresses must ALWAYS have spaces around `@` and around EVERY dot (e.g., `client @ domain . com` and `karam @ gmail . com`). NEVER write `client@domain.com` or `<client@domain.com>`.

3. **Executive Diagnostic Summary:**
   * Present the live Google search and domain diagnostic data cleanly:
     > *"I pulled your live Google search and domain diagnostic data today. Here is the high-level snapshot:*  
     > *• **Domain Authority Score:** [X] / 100*  
     > *• **Monthly Organic Traffic:** [X] visits/mo*  
     > *• **Total Backlinks & Referring Domains:** [X] links across [X] domains*  
     > *• **Organic Keywords Indexed:** [X] terms*  
     > *• **AI Search Visibility:** [X] (ChatGPT & Google AI mentions)"*

4. **Centered White-Label Scorecard:**
   * Embed the cropped Semrush scorecard image (and bounce rate card if applicable) inline immediately after the summary. Use `cid:semrush_screenshot` (and `cid:bounce_screenshot` if both images are used).

5. **Authority Validation + Competitor Punch (2-3 sentences max):**
   * **MANDATORY RESEARCH REQUIREMENT:** You must look up the client's **exact town, city, or county**, and identify **1 to 2 REAL local competitors** operating right in their immediate service area.
   * First validate their backlink strength (so they feel good), then immediately contrast it with the competitor reality:
     > *"You have [X] backlinks and [X] referring domains — that is a genuinely strong foundation. Most [industry type] in [City] don't come close to that.*  
     > *But despite that authority, Google is only sending you [X] visitors a month. Meanwhile, [Real Competitor 1] and [Real Competitor 2] in your same [City / Region] are sitting right at the top of Google, capturing those $[X,000]+ [orders/clients/projects]."*

6. **The Open Loop — 2 Findings Revealed, 3rd Held Behind a Question (THE KEY SECTION):**
   * Present this as "We identified 3 technical issues blocking your [business] from Google's first page."
   * **Finding 1 (Revealed):** The indexation / keyword gap — explain in plain English that Google is indexing them for wrong/generic terms instead of the high-intent commercial searches buyers actually use. Give 2-3 specific keyword examples relevant to their niche and city.
   * **Finding 2 (Revealed):** The backlink authority waste — explain that their [X] backlinks are being wasted due to crawl-level errors preventing Google from connecting their domain authority to their service/product pages.
   * **Finding 3 (HELD — The Open Loop):** Frame the 3rd issue as something that depends on a specific aspect of their business that only they know. Then ask a **simple, business-relevant question they can answer in 1 sentence from their phone.**
   * **Close with:** *"Once I know that, I can confirm whether this third issue applies to your setup and send you the complete fix list."*
   * **MANDATORY: The question must be specific to their business model, geography, or operations.** Examples:
     * Multi-location business: *"Are most of your inquiries coming through [Location A], or is [Location B] pulling significant volume on its own?"*
     * Retail / e-commerce: *"Are most of your customers local walk-ins at your [Street] store, or online orders shipping out?"*
     * Service business: *"Are most of your clients coming from [City A] itself, or are they driving in from [surrounding area]?"*
     * Photography / creative: *"Are most of your clients from [City] itself, or are they coming from [nearby metro area]?"*

7. **Full Professional Signature (Strict Standard):**
   * Best,  
     **Shiv**  
     **SEO/AEO Consultant**  
     **Innovate Marketers LLC**  
     Direct: +1(645) 220-1660  
     Address: 382 NE 191st St PMB 171379, Miami, FL, 33179-3899, US  
   * *(Note: NEVER add "Sender notified with Mailtrack")*

8. **Thread-Lock & Recipient Integrity (Strict Anti-Break Rule):**
   * Target recipient `To:` MUST be the external prospect's email address (NEVER our own address).
   * For in-thread replies, include the exact parent `threadId`, parent `Subject`, `In-Reply-To` matching the previous `<Message-ID>`, and full cumulative `References` chain.

---

## 4. Automated Delivery to Web Gmail Drafts & Direct Chat Output
* Automatically run `src/gmail_helper.py` using the authorized local token if present.
* **Dual-Delivery Standard (Live Draft or Instant Chat Output):**
  * When Gmail API credentials (`credentials.json` or `token.json`) exist, the script automatically injects the completed draft directly into the user's **web Gmail Drafts folder** with the inline scorecard and attachments in place, notifying the user with the Draft ID so they can open `mail.google.com` &rarr; Drafts &rarr; Click **Send**.
  * If Gmail API credentials are not yet configured on the local laptop, the system automatically saves the draft to the client's vault (`clients/{client_slug}/draft_email.html` and `.txt`) and prints the clean text. Anti Gravity MUST present this validated email copy directly in the chat window so the user can copy-paste it into their email client immediately. NEVER attempt to modify or hack scripts when credentials are not configured.

---

## 5. In-Thread 48-Hour Follow-Up Standard (`run_followup.py`)
* If a client does not reply after 48 hours, run: `python run_followup.py --slug [client_slug]` (or `--email [email]`).
* **Threading Standard:** The draft is injected **directly inside the existing Gmail conversation thread** via Google API (`threadId` + `In-Reply-To`), so the previous audit email and scorecard sit directly above it.
* **100% Manual Send Control:** The script strictly creates an **un-sent draft**. It never sends automatically. The user reviews and clicks **Send** in Gmail.
* **Copywriting Rules:** Under 40 words, no duplicate images or metric lists, polite bump, references the unanswered open loop question from the original email (e.g., "Did you get a chance to see the scorecard? I still have that third finding on hold — just need your quick input on [the question].").
* **STRICT SIGNATURE RULE:** NEVER add "Best, Shiv", "Regards, Shiv", or any manual signoff/signature to email drafts or chat box copies. The user has an automatic signature configured directly in their email client. Always end the copy cleanly right after the call-to-action question.

---

## 6. Live Call & Voicemail Scripts (Super Simple Follow-Up)
* **Live Call (When they pick up):**
  > *"Hi [Name], this is Shiv.*  
  > *This is a follow-up call regarding your email reply to my colleague about your website and SEO problem.*  
  > *I just sent you the details to your email.*  
  > *Can we do a quick 5-minute call tomorrow to look at it together?"*

* **If they ask "What is it about?":**
  > *"Your website is not ranking on Google, and competitors are taking all the customers. I can show you what to fix in 5 minutes."*

* **Voicemail (Under 15 seconds):**
  > *"Hi [Name], this is Shiv.*  
  > *This is a follow-up call regarding your email reply to my colleague about your website and SEO problem.*  
  > *I just sent the details to your email. Please check your inbox, or call me back at (645) 220-1660.*  
  > *Thank you!"*

---

## 7. Visual Google Search Audit SOP (`run_audit.py` & `src/keyword_audit_pipeline.py`)

This protocol is strictly followed whenever a prospect challenges an initial email (e.g., claiming they rank on Page 1 on mobile or for vanity terms), or when a prospect requires undeniable visual proof of lost commercial traffic across target services or retail markets.

### STRICT OPERATIONAL MANDATE: ZERO SCRATCH SCRIPTS & UNDER 3-MINUTE RUN TIME
* **NEVER WRITE OR RUN AD-HOC SCRATCH SCRIPTS (`scratch/run_*.py`, `scratch/audit_*.py`, etc.):**
  * Writing custom scratch scripts for every client wastes 30–45 minutes, introduces layout bugs, and violates user SOPs.
* **MANDATORY SINGLE-COMMAND MASTER ENTRYPOINT:**
  * Every search audit MUST be executed via the master CLI script in the workspace root:
    ```bash
    python run_audit.py --slug [client_slug]
    # OR directly by email or search query for unvaulted leads:
    python run_audit.py --email [client_email]
    python run_audit.py --query "[client_name or domain]"
    ```
  * `run_audit.py` loads `clients/{client_slug}/config.json` (or auto-resolves unvaulted leads via `src/lead_resolver.py` from Gmail/CRM in <3s), verifies inputs, captures unranked searches via CDP port 9222, assembles the full-bleed PDF (22 or 23 pages with stacked headers and educational primer), verifies page count, and outputs the Phase 5 email draft—**all in under 3 minutes**.
* **STRICT PROHIBITION ON RAW HTTP SCRAPING (NETWORK HANG PREVENTION):**
  * **NEVER execute raw HTTP page fetches (`read_url_content`) on prospect websites:** CMS platforms (Duda, Wix, Squarespace, WordPress) and CDN bot-defenses cause 5–6 minute blocking network timeouts.
  * Always inspect prospect services via Google Search snippets, Semrush data, or by viewing the page directly inside the active Chromium CDP session (`http://127.0.0.1:9222`).

### Phase 1: Keyword & Query Research Gate
* **Automated Client Absence Guardrail & Resilient Auto-Swap:**
  * **NEVER include any search query where the client appears anywhere on Page 1** (neither in Google Business Profile Map Pack, nor in Local 3-Pack, nor in Organic Results #1 through #10).
  * If a client ranks in their small hometown (e.g., Longmont, CO, or Chico, CA), the audit MUST target the surrounding regional commercial economic engines (e.g., Denver, Boulder, Redding, Sacramento) where the true high-ticket client volume searches and where the client is 100% absent.
  * **Resilient Dynamic Auto-Swap (Zero Pipeline Crashes):** When `src/keyword_audit_pipeline.py` programmatically detects the client's domain or business name on Page 1, it logs a notice, pulls a replacement candidate from `fallback_keywords` (or dynamically synthesizes an adjacent regional economic hub), swaps it in-memory, re-verifies absence, and auto-saves the updated 10 keywords back to `config.json` without crashing the pipeline.
* **Service Area vs. Office Location Rule (Crucial Anti-Local-Trap Standard):**
  * **STRICT PROHIBITION ON OFFICE-ONLY TARGETING:** Never restrict keywords solely to the client's physical office address, shop, or hometown (e.g., targeting only Corinth or small town Denton). Contractors, service providers, and B2B businesses travel and operate across an entire 25- to 50-mile regional corridor.
  * **MANDATORY SERVICE RADIUS MAPPING:** Always inspect the client's website for their official "Areas We Serve" page, service dropdown, footer city list, or service radius map.
  * **REGIONAL ECONOMIC HUB STRATEGY (90–100% OF KEYWORDS):** Distribute commercial keywords across their immediate base AND the surrounding major commercial economic engines within their verified service territory (e.g., Denton, Dallas, Fort Worth, Plano, Frisco, McKinney, Arlington, Grapevine). This proves where the true high-dollar commercial bids ($15k–$45k+) originate, eliminating the objection: *"I already rank in my tiny hometown, I don't need SEO."*
* **Zero Guesswork Rule:** Extract keywords exclusively from the prospect's verified credentials, licenses, and specific service pages (e.g., CARB Lead Verifier, CWA Sec 404, CEQA Biology, CDFW stream surveys) or specific high-intent retail market queries (e.g., `brand dispensary [City]`). Never use generic hazmat or broad national terms.
* **Target Commercial Queries:** Formulate multi-word, high-intent phrases that actual commercial buyers, landowners, or consumers type into Google.
* **Realistic, Non-Exaggerated Fee Ranges:** Use broad, defensible pricing brackets (e.g., `$1,000 – $5,000 USD` for routine parcel surveys, `$3,000 – $10,000 USD` for specialized audits). Never quote inflated $50k+ corporate numbers for solo consultants.

### Phase 2: Automated Full-Page Search Capture Gate (CDP)
* **Active Session Rule:** Connect directly to the active Chromium instance via CDP (`http://127.0.0.1:9222`) to bypass bot detection.
* **Full-Page DOM Capture Standard:**
  * Take a complete un-truncated full-page screenshot (`page.screenshot(path=raw_full, full_page=True)`).
  * This captures 100% of Google Page 1 in a single high-resolution image: from the query box at the top, through AI Overview and Map Pack, through every organic position (#1 through #10), down to the official Google pagination footer (`Goooooooooogle 1 2 3 ... 10 Next`).
  * **ZERO MISSING MIDDLE MANDATE:** Never jump from top fold to bottom footer with independent viewport scrolls. Capturing the entire DOM in one shot ensures no middle results (#4 to #7) are skipped or hidden.

### Phase 3: Universal Clean White-Label Cropping & Continuity Split
* **Clean Margin Rule (Zero Left Cutoff & Complete Map Pack):**
  * Horizontal crop: `x_min <= 95` (dynamic `minX - 35px`), `x_max >= 1280` (dynamic `maxX + 35px`).
  * In desktop Google Search, text, form inputs, and the Google logo begin at `x ≈ 130–142`. Setting `x_min = 95` guarantees 35–45px of clean whitespace margin to the left of all text, logos, bullets, icons, and titles.
  * **STRICT PROHIBITION on setting `x_min >= 130`:** Never set `x_min` to 130, 140, 180, or any number that cuts off word-beginnings ("Google" -> "ogle", "Businesses" -> "sinesses", "Erick's" -> "ck's").
  * **Map Pack Integrity:** The Google Map Pack extends to `x ≈ 1242–1260`. Setting `x_max >= 1280` captures the full map without cutting through pins or buttons.
* **Dynamic Multi-Color Pagination Detection:**
  * Detect the colorful Google logo (`Goooooooooogle`) across rows in the lower 40% of the page using simultaneous red (`R > 200, G < 100, B < 100`) and blue (`B > 200, R < 100`) pixel density.
  * Crop cleanly at `logo_y + 42px` right below the pagination page numbers and `Next` link.
  * **Strict Location Stripping:** This completely strips the personal/overseas IP footer (e.g., "India / From your IP address") and "Results are personalised", leaving a 100% clean, neutral desktop Google Search view.
* **Continuous Overlap Split (Page A & Page B):**
  * Page A (Top Fold): `y = 10` to `split_y` (`10 + int(content_h * 0.55)`), capturing Query Box, AI Overview, Map Pack, and Positions #1 to #3.
  * Page B (Bottom Fold): `overlap_start` (`split_y - int(content_h * 0.12)`) down to `pag_bot`, capturing Positions #3 to #10, People Also Search For, and the official Google Pagination Footer.
  * The 250–300px overlap ensures that the result closing Page A is prominently visible at the top of Page B as the visual continuity anchor, proving beyond doubt that 100% of Page 1 is accounted for.
* **Integrity Gate:** Pre-flight validation confirms all cropped image files (`_top_cropped.png` and `_bot_cropped.png`) exist and exceed 25 KB.

### Phase 4: Master PDF Assembly & Strict 2-Page-Per-Query Rule
* **STRICT 2-PAGE ALLOCATION PER SEARCH TERM:**
  * **EVERY search term/city/keyword MUST occupy exactly TWO dedicated pages in the PDF report:**
    * **Page A (Top Fold):** Query box, top competitors (#1 to #3/Map Pack), and live competitor capture analysis.
    * **Page B (Bottom Fold & Pagination):** Seamless continuation from lower results (#4 to #10), related searches, and the official Google pagination footer proving the client does not appear anywhere on Page 1.
  * **STRICT PROHIBITION ON SINGLE-SCREENSHOT KEYWORD PAGES:** NEVER put only 1 screenshot per keyword or compress a search term into a single page. If a client does not see the bottom fold with Google's pagination footer, they will immediately object: *"You only took a screenshot of the top, I might be ranked lower down on the page."* Showing the bottom fold with the pagination footer is the indisputable proof that completely eliminates that objection.
* **Strict Email-Preview Typography Standard (Page 1 Legibility & Tech Aesthetic):** To ensure prospects viewing the PDF inside Gmail's in-browser previewer or on mobile can read everything effortlessly with modern executive authority:
  * **Typography Stack:**
    * **Headings, Metric Values & Titles:** **Plus Jakarta Sans** (weights 700, 800, 900) — clean geometric cuts, modern Silicon Valley authority (Stripe/Linear aesthetic).
    * **Body Copy & Notes:** **Inter** (weights 450, 500, 600) — maximum micro-legibility and razor-sharp contrast on mobile/desktop screens.
    * **Search Queries, URLs & Technical Badges:** **JetBrains Mono** (weights 600, 700) — diagnostic high-tech terminal look.
    * **Tabular Figures:** Always apply `font-feature-settings: 'tnum' 1; font-variant-numeric: tabular-nums;` to metric cards so numbers align with precision.
  * Executive Insight headers MUST be >= 11.5pt bold with vibrant accent color (`#38bdf8`).
  * Insight body text MUST be >= 10.2pt in crisp, high-contrast white (`#f8fafc`) with generous line-height (`1.45`).
  * KPI metric card labels MUST be >= 8pt bold (`#cbd5e1`), values >= 13.5pt bold, and descriptions >= 7.5pt (`#94a3b8`).
  * **STRICT PROHIBITION ON GENERIC SYSTEM FONTS & DIM/TINY TEXT:** NEVER fallback to unstyled Arial or Segoe UI; always load Google Fonts and never use <9pt body text on the cover page.
* **Maximized Screenshot Presentation & Head-to-Head Competitor Punch Standard:**
  * **Head-to-Head Callout Punch Bar:** Every keyword page MUST feature a high-contrast dark comparison bar directly above the screenshot:
    * Left side (`#4ade80` / `#38bdf8`): **GOOGLE PAGE 1 WINNER** highlighting real competitors (`[Competitor 1] • [Competitor 2]`), reviews, and captured inquiries.
    * Middle: High-contrast **VS** pill.
    * Right side (`#ef4444`): **[CLIENT] PLACEMENT: NOT RANKING ON PAGE 1** (0% First-Page Buyer Discovery • Complete Traffic Leak).
  * **Clean Viewport Layout (Zero Half-Torn Images):**
    * `.img-wrapper-top` and `.img-wrapper-bot` are sized to `height: 495px; max-height: 495px; overflow: hidden; display: flex; align-items: flex-start; justify-content: center; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);` (on Keyword #1 with primer, `height: 450px`).
    * Image scaling: `width: 100%; height: 100%; object-fit: contain; object-position: top center;` ensuring full 860px crop is visible with generous margins and no arbitrary CSS clipping or stretching.

* **Strict Stacked Keyword Header Architecture (Zero Wrapping Rule):**
  * **STRICT PROHIBITION ON SIDE-BY-SIDE FLEX BOXES FOR HEADERS:** NEVER place category pills, order value pills, and the search query on conflicting flex lines that cause pills to wrap awkwardly (e.g. "TARGET KEYWORD 1 OF 10 • COMMERCIAL PERIMETER" / "FENCING" on line 2).
  * **MANDATORY TWO-ROW STACKED HIERARCHY:**
    * **Row 1 (Metadata Bar - Full Width):** Space-between row with `white-space: nowrap; flex-shrink: 0;` pills. Left: `TARGET KEYWORD #XX OF 10` (purple pill) + `CATEGORY TAG` (grey pill). Right: `EST. ORDER VALUE: $XXK – $XXK*` (green pill).
    * **Row 2 (Query Headline - Full Width):** Sits cleanly below Row 1 with dedicated prefix: `LIVE SEARCH QUERY: "[exact multi-word search phrase]"`.

* **Kickoff Educational Primer Standard ("What is a Commercial Keyword?"):**
  * On **Keyword #1 Top Fold (Page 3)**, ALWAYS include an educational primer card right above the screenshot explaining to non-technical prospects what a commercial search keyword actually is:
    * Define what a commercial keyword is (the exact phrase typed by business owners, facility managers, or commercial buyers with approved budgets ready to award contracts).
    * Contrast commercial high-intent searches against consumer DIY/vanity searches.
    * Reiterate the 90%+ Google Page 1 click capture reality.
    * Follow immediately with the specific Commercial Buyer Scenario for that keyword.

* **Dedicated Page 2 Forensic Architecture & Code Health Standard:**
  * When a prospect has technical anomalies discovered during the initial code or Semrush inspection (e.g. static HTML sites, dumped single-page blogs, toxic PBN/spam links, rogue foreign URLs, or hardcoded fake reviews), include a dedicated **Page 2: Forensic Architecture & Code Health Deep-Dive**:
    1. **Industry-Specific Native Metaphor:** Compare their website's technical foundation to their actual craft (e.g., setting fence posts in shifting North Texas clay soil without depth or concrete vs. cedar pickets).
    2. **4-Row Side-by-Side Punch Table:** Clear 3-column comparison table:
       * Column 1: *What a Real Modern Business Site Has* (Green accent)
       * Column 2: *What Your Developer Actually Built* (Red accent)
       * Column 3: *Why It Costs You High-Dollar Commercial Bids* (Dark/Slate accent)
    3. **Commercial vs. Consumer Revenue Gap:** Explicit contrast between small consumer jobs and large commercial contracts (e.g. $4k–$8k residential vs. $20k–$45k commercial).
    4. **Zero-Pitch 15-Minute Google Meet Agenda:** Provide an explicit 3-bullet technical agenda for the screen-share (Disavow list, Blog architecture fix, Competitor ranking blueprint) eliminating sales pitch fear.

* **Overflow & Blank-Box Prevention:** To prevent Chromium's nested-flex print-overflow bug:
  * Strictly size `.page` containers to `padding: 8mm 11mm 7mm 11mm; overflow: hidden; page-break-inside: avoid; page-break-after: always;`.
  * Add `page-break-inside: avoid;` to all note cards, punch bars, and CTR callout boxes.
* **Standard Page Count Architecture:**
  * **Standard 10-Keyword Service Audit:** Exactly 22 pages (Cover Dashboard + 10 Keywords × 2 pages + Technical Fix Summary).
  * **Forensic 10-Keyword Service Audit:** Exactly 23 pages (Cover Dashboard + Page 2 Forensic Deep-Dive + 10 Keywords × 2 pages + Technical Fix Summary).
  * **5-City Retail / Brand Audit:** Exactly 13 pages (Cover Dashboard + Technical Root Cause / Store Locator Page + 5 Cities × 2 pages + Solution Roadmap).
* **Automated Visual Verification:** Capture preview screenshots of sample pages to verify all text boxes and images render cleanly with zero overflow before delivering to the user.

### Phase 5: Short-Form Human Email Delivery Gate
* **Short 1–2 Sentence Paragraphs:** Maximize line spacing so the email takes under 15 seconds to scan on a phone.
* **MANDATORY "3 HOURS OF DEDICATED EFFORT" RECIPROCITY HOOK:** Whenever attaching any visual audit report, ALWAYS include the dedicated personal effort phrasing:
  > *"I am also attaching the visual report. I spent over 3 hours specifically for you preparing it, hope you will read it so my efforts won't go in vain."*
* **MANDATORY CUSTOMER-PERSPECTIVE KEYWORD FRAMING (STRICT STANDARD):**
  * NEVER write generic high-level fluff. Always frame the email directly from the shoes of their actual target customers (e.g. parents, homeowners, young athletes, local buyers) in their specific city:
  * Quote **2 to 3 real target commercial keywords** from the audit:
    > *"When a [parent / homeowner / young adult / buyer] from [City] searches Google for '[Keyword 1]', '[Keyword 2]', or '[Keyword 3]'—they see competitors like [Competitor 1] and [Competitor 2], but [Company Name] doesn't appear on Page 1."*
  * Connect the 22-page visual report directly to these high-value revenue streams:
    > *"This 22-page report is built around the 10 high-value searches that directly drive [memberships / clients / orders] to your business, showing screenshot-by-screenshot exactly where your website currently stands on Google and where those [students / customers / inquiries] are going instead."*
* **Google Meet Call-to-Action:**
  * Ask for their preferred **day and time** for a 10-minute Google Meet to screen-share and show the exact problems and solutions.
* **STRICT SIGNATURE RULE (Rule 5):** NEVER add "Best, Shiv", "Regards, Shiv", or any manual signoff/signature to the copy box. End cleanly after the meeting CTA.
* **Delivery Standard:** Output inside a copyable markdown box (` ``` `) ready for Gmail.

---

## 8. Meeting Invitation Standard (STRICT: "Google Meet" ONLY & Always Ask Day & Time)
* **STRICT PROHIBITION ON SAYING "CALL":** NEVER write "quick call", "10-minute call", or "phone call" when inviting prospects to review technical audits. Prospects get confused thinking it is an audio-only phone call.
* **MANDATORY GOOGLE MEET & SCREEN-SHARE SPECIFICATION:** ALWAYS specify **Google Meet** and explicitly mention screen-sharing.
* **MANDATORY DAY & TIME INQUIRY:** ALWAYS ask the prospect for their preferred **day and time** to schedule the meeting, giving them an explicit call-to-action to reply with their availability.
* **MANDATORY PHRASING:**
  > *"What day and time works best for you for a quick 10-minute Google Meet so I can share my screen and show you the exact problems and solutions?"*

---

## 8.1 Scheduled Meeting Confirmation & Calendar Invite Standard
Whenever the user schedules a meeting with a client and asks for a confirmation email or meeting mail, ALWAYS use this exact high-converting template:
* **Time Confirmation:** Confirm the agreed day, time, and timezone immediately.
* **Calendar Acceptance Request:** State that the Google calendar invitation was sent and politely request they accept it.
* **Technical Backup Link Hook:** Include the direct fallback join line: *"If you face any technical issues with the calendar invite, you can join directly through the link below:"* followed by `Google Meet Link: [Paste Google Meet Link Here]`.
* **Zero Manual Signatures:** Never add "Best, Shiv", "Regards, Shiv", or any manual signoff (client's email auto-signature applies).
* **Delivery:** Always output inside a copyable markdown box (` ``` `) ready for Gmail.

**Standard Template:**
```text
Hi [Client Name],

[Today / Tomorrow / Day] at [Time] [Timezone] works perfectly.

I have sent over the Google calendar invitation to your email — please accept it so it gets confirmed on your schedule.

If you face any technical issues with the calendar invite, you can join directly through the link below:

Google Meet Link: [Paste Google Meet Link Here]

Looking forward to connecting with you [today / tomorrow]!
```

---

## 9. Master Executive Proposal SOP (`run_proposal.py` & `src/proposal_pipeline.py`)

This protocol is strictly followed whenever creating a formal SEO, AEO & Brand Visibility Proposal for a prospect after an initial meeting or discovery call.

### Architecture Standard: 8-Page Audit-Inspired Executive Standard (Type 3)
* **STRICT PROHIBITION ON PREMATURE COVER PRICING:** Never place package prices on Page 1 (Cover Page). Prices belong exclusively on **Page 7** after the client reviews the commercial opportunity, technical diagnostics, execution matrix, and keyword architecture.
* **8-Page Executive Flow:**
  * **Page 1: Executive Cover Page:** Title, client organization, executive mandate, partnership philosophy (month-to-month, 100% asset ownership, zero friction).
  * **Page 2: 01 / Strategic Vision & Commercial Opportunity:** Niche positioning, high-ticket revenue modeling, 4 growth pillars.
  * **Page 3: 02 / Technical Health Check:** 4+ diagnostic issues with high-contrast status badges (`CRITICAL LEAK`, `INDEXATION FLAW`, `AI BLINDSPOT`).
  * **Page 4: 03 / Technical Execution Architecture:** Dynamic 3-mode handling:
    1. *In-House Developer Synergy:* Division of labor table + developer credit savings.
    2. *Hands-On Knowledge Transfer:* Screen-share coaching & DIY empowerment.
    3. *100% Turnkey Deployment:* Full agency code injection, schema, and server management.
  * **Page 5: 04 / Search & AI Discovery Architecture:** Priority keyword clusters + AI Answer Engine optimization (ChatGPT, Perplexity, Gemini).
  * **Page 6: 05 / Step-by-Step Growth Roadmap:** 4 sequential phases (`PHASE 1` through `PHASE 4`, zero week numbers).
  * **Page 7: 06 / Investment & Partnership Packages:** Transparent rate cards, published agency rate comparison, partner discount badges, scope deliverable comparison table.
  * **Page 8: 07 / Next Steps & Partnership Onboarding:** 4 simple onboarding steps, sign-off blocks for client and agency.
* **Audit-Grade Typography Stack:**
  * Headings, Metrics & Plan Names: **Plus Jakarta Sans** (weights 700, 800, 900)
  * Body & Descriptions: **Inter** (weights 450, 500, 600)
  * Badges, Tags & Technical Fixes: **JetBrains Mono** (weights 600, 700)
* **Single-Command Execution:**
  ```bash
  python run_proposal.py --slug [client_slug]
  ```
  Generates `clients/{client_slug}/proposal.pdf` in under 20 seconds.

---

## 10. Global Lead Suppression & Blacklist Guardrail (`data/suppression_list.json`)
* **STRICT PROHIBITION ON CONTACTING SUPPRESSED LEADS:**
  * When a prospect indicates they are not interested, asks to stop emailing, or unsubscribes (e.g. Chris Elliott / `nuggetglass@gmail.com` / `nuggetglass.com`, Jana Cooley / `cooleyjana.rsu@outlook.com` / `goldendoodledandies.com`, Ark Dome / `autopartsbling@gmail.com` / `pccautoparts.com`, `sales@testequipmentusa.com`, `marc@vehicleinspectors.com`), they are PERMANENTLY blacklisted in `data/suppression_list.json`.
  * `create_gmail_draft()` in `src/gmail_helper.py` strictly verifies against `validate_not_suppressed()`, programmatically raising a fatal `ValueError` and refusing to touch the Gmail API if any suppressed email or domain is targeted.
  * All candidate generation and batch follow-up scripts MUST cross-reference `data/suppression_list.json` and immediately filter out suppressed emails and domains before drafting.

---

## 11. Strict Ephemeral Hygiene & Client-Branded Filename Standard
* **MANDATORY CLIENT-BRANDED FILENAMES (NO GENERIC NAMES EVER):**
  * To ensure instant clarity in Windows File Explorer, Adobe Acrobat, and email attachments, **NEVER name files generically** (e.g. `audit_report.pdf`, `proposal.pdf`, `scorecard.png`).
  * Every generated asset MUST carry the client's explicit name in Title Case:
    * **Audit PDF:** `clients/{slug}/{Client_Name}_Google_Search_Audit.pdf` (e.g., `Asphaltexps_Google_Search_Audit.pdf`, `Blue_Oasis_Google_Search_Audit.pdf`)
    * **Proposal PDF:** `clients/{slug}/{Client_Name}_SEO_AI_Visibility_Proposal.pdf` (e.g., `Asphaltexps_SEO_AI_Visibility_Proposal.pdf`, `Blue_Oasis_SEO_AI_Visibility_Proposal.pdf`)
    * **Scorecard Image:** `clients/{slug}/screenshots/{Client_Name}_Semrush_Scorecard.png` (e.g., `Asphaltexps_Semrush_Scorecard.png`)
* **STRICT WHITELIST PER CLIENT VAULT (`clients/{client_slug}/`):**
  Only approved permanent asset types are EVER permitted to live inside a client vault:
  1. `brief.md` *(Client briefing, contact dossier & call scripts)*
  2. `config.json` / `proposal_config.json` *(Audited parameters)*
  3. `*_Google_Search_Audit.pdf` *(Official 22/23-page visual Google Search Audit)*
  4. `*_SEO_AI_Visibility_Proposal.pdf` *(Official 8-page Executive Strategy Proposal)*
  5. `screenshots/*_Semrush_Scorecard.png` & `screenshots/kw*_cropped.png` *(Verified proof images)*
* **STRICT BLACKLIST OF EPHEMERAL FILES:**
  * **Zero Loose Preview Renders:** Never create or leave `preview_*`, `v2_renders`, `page_*.png`, or `scratch/` folders inside client vaults or root.
  * **Zero Ad-Hoc Scripts:** Never create scratch Python scripts (`scratch_*.py`, `inject_*.py`, `test_*.py`) in the root directory.
  * **Zero Loose HTML Files:** Temporary HTML files used by Playwright must strictly use `tempfile.mkstemp` and be deleted in a `try...finally` block.
* **PROGRAMMATIC POST-FLIGHT SANITIZER GATE:**
  * Every runner (`run_audit.py` and `run_proposal.py`) automatically invokes `sanitize_client_vault()` upon completion.
  * Any unapproved ephemeral directory or file is purged immediately, leaving the vault 100% clean and pristine.
  * Whitelist assets are 100% protected and never touched.

## 12. Mandatory Live Site Extraction & Zero-Hallucination Gate
* **MANDATORY LIVE SITE EXTRACTION BEFORE CONFIG CREATION:**
  * Before generating `config.json` (for a search audit) or `proposal_config.json` (for an executive proposal), the agent or system MUST inspect the prospect's live rendered website content.
  * Never rely solely on the domain name or generic industry assumptions.
* **EXACT VERIFIED SERVICE EXTRACTION (ZERO GENERIC TERMS):**
  * All target search queries and proposal deliverables must be pulled strictly from the client's verified service pages, official licenses (e.g. RBQ, contractor certifications), and explicit niche capabilities (e.g., Tony Pesce's *catch basin & manhole drain repair / têtes d'égouts*, *asphalt resurfacing*, *crack routing & sealcoating*—not generic national terms).
* **STRICT PROHIBITION ON OPERATIONAL SPECULATION:**
  * **Zero Hallucinated Numbers:** NEVER invent, estimate, or state specific client headcounts, customer numbers, cohort sizes (e.g. "12 clients"), monthly job volume, or internal revenues unless explicitly published on their website or confirmed in the meeting transcript.
  * If specific client volume is unknown, always use flexible, defensible executive framing (e.g. *"intimate executive cohorts"*, *"commercial and residential property managers"*).
