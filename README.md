# Call Copilot & Automated Outreach Intelligence Engine

An autonomous client intelligence, forensic site analysis, high-converting email outreach, and sales closing copilot built for high-ticket agency operations.

---

## What This System Does

### 1. Forensic Site Analysis & Commercial Intake (`src/site_analyzer.py` & `run_intake.py`)
- **Operational Delivery Model Classification:** Automatically detects whether a business is `NATIONWIDE_VIRTUAL` (Zoom coaching, digital courses, national SaaS) or `LOCAL_IN_PERSON` (trades, clinics, contractors, retail), preventing local geo-fencing errors.
- **Package & Pricing Scraper:** Crawls `/services`, `/pricing`, and booking calendars to extract real price tiers ($397, $1,191, $3,582) and Zoom formats directly from live websites.
- **Technical SEO Diagnostics:** Performs automated on-page audits: title tag lengths, meta descriptions, `<h1>` hierarchy, Schema.org JSON-LD structured data, sitemaps, and mobile viewport compliance.
- **Smart 10-Keyword Synthesis:** Generates high-intent commercial keywords (nationwide queries for virtual businesses, regional economic engine corridors for local businesses).

### 2. High-Converting Email Generation & In-Thread Follow-Ups
- **Open-Loop Strategy:** Presents 2 out of 3 technical findings clearly, holding the 3rd finding behind a single business-specific question that compels the client to reply.
- **Metric Parity & WinRT OCR Validation (`src/scorecard_validator.py`):** Automatically validates that all numbers quoted in the email match Semrush scorecard screenshots 1:1 using Windows native OCR before draft creation.
- **48-Hour In-Thread Bumps (`run_followup.py`):** Docks directly into existing Gmail conversation threads with under-40-word polite bumps that reference the unanswered question.
- **Anti-Spam Formatting:** Zero contiguous URLs/protocols (`https://` stripped, spaces around dots), protecting inbox deliverability.

### 3. Visual Search Audits & Client Closing Proposals
- **22-Page Visual Search Audit (`run_audit.py`):** Captures Google search rankings, verifies client absence on Page 1, generates educational SEO primers, and compiles a comprehensive PDF audit report.
- **13-Page Closing Proposal & Service Agreement (`run_proposal.py` & `generate_agreement.py`):** Generates bespoke, high-converting proposals and service agreements with specific package scopes, deliverables, timelines, and payment terms.

### 4. Real-Time Live Sales Call Copilot Overlay (`main.py` / `Call_Copilot.bat`)
- Real-time audio capture via Windows loopback.
- Live speech-to-text transcription via Deepgram Nova-3.
- Fast objection handling and situational response generation powered by Claude/Groq LLM engines.
- Semi-transparent, always-on-top PyQt6 desktop overlay.

---

## Quick Setup Guide

### 1. Prerequisites
- **Python 3.10+** (64-bit recommended)
- **Git**
- **Google Chrome** or Chromium

### 2. Installation
Clone the repository and install the dependencies:

```bash
git clone https://github.com/Shivaprasadfarale/call_copilot.git
cd call_copilot

# Optional: Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser engine for site analysis & audit captures
playwright install chromium
```

### 3. Configuration (Optional for Voice Overlay)
If you want to use the live sales call overlay UI:
1. Copy `config.example.yaml` to `config.yaml`.
2. Add your Groq API key (free tier available at [console.groq.com](https://console.groq.com)) or AWS Bedrock / Deepgram credentials.
3. Launch via `Call_Copilot.bat` or `python main.py`.

---

## Working with Anti Gravity (Zero Technical Setup Needed!)

If you are using Anti Gravity, you do not need to memorize terminal commands! Anti Gravity reads `AGENTS.md` and executes all workflows automatically under the hood:

- **When a client replies "Yes, send the report":**
  Simply paste their reply or email thread into the Anti Gravity chat. Anti Gravity automatically runs `run_intake.py`, triggers the site analyzer, validates metrics, and writes the high-converting email directly for you or injects it into your Gmail drafts!
- **When you need a 13-page proposal or service agreement:**
  Tell Anti Gravity: *"Generate a proposal for [Client Name]"*, and it will research their packages, generate the deliverables, and compile the contract.
- **When a client doesn't reply after 48 hours:**
  Tell Anti Gravity: *"Follow up with [Client Name]"*, and it will prepare the 35-word in-thread bump.

---

## Architecture & Directory Layout

```
call_copilot/
├── AGENTS.md                   # Master Standard Operating Procedures (SOP)
├── AUTOMATED_OUTREACH_GUIDE.md # Operational guide for email outreach
├── Call_Copilot.bat            # Portable one-click launcher for call overlay
├── main.py                     # Entry point for real-time call copilot
├── requirements.txt            # Python dependencies
├── config.example.yaml         # Configuration template
├── credentials.example.json    # Google OAuth credentials template
├── leads.example.md            # Intake formatting template
│
├── run_intake.py               # Pre-flight lead intake & site classification
├── run_scorecard_draft.py      # Scorecard draft generator with OCR validation
├── run_followup.py             # 48-hour in-thread follow-up generator
├── run_proposal.py             # 13-page closing proposal compiler
├── run_audit.py                # 22-page visual search audit pipeline
├── generate_agreement.py       # Client service agreement generator
│
├── src/                        # Core engines
│   ├── site_analyzer.py        # Forensic site crawler & package scraper
│   ├── proposal_pipeline.py    # Proposal generation engine
│   ├── keyword_audit_pipeline.py # Search audit engine
│   ├── scorecard_validator.py  # OCR parity verification gate
│   ├── gmail_helper.py         # Gmail draft & thread integration
│   ├── followup_generator.py   # Follow-up email copy engine
│   ├── outreach_generator.py   # Email copy generation engine
│   ├── overlay.py              # PyQt6 live call overlay
│   ├── run_ocr_clean.ps1       # Native Windows WinRT OCR script
│   └── audio/, llm/, stt/      # Voice and transcription modules
│
├── assets/                     # Branding logos and visual assets
├── templates/                  # Email and document templates
├── tests/                      # Automated test suite
└── .agents/skills/             # Anti Gravity skill definitions
```

---

## License & Privacy
Proprietary & Confidential. Built for internal agency operations. All client vaults, credentials, and API secrets are strictly excluded from version control.
