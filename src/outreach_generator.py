import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import boto3
import yaml

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(WORKSPACE_DIR, "config.yaml")
LEADS_KB_DIR = os.path.join(WORKSPACE_DIR, "knowledge_base", "leads")

os.makedirs(LEADS_KB_DIR, exist_ok=True)

OFFICIAL_SIGNATURE_HTML = """
<div style="margin-top: 30px; font-family: Arial, sans-serif; font-size: 13px; color: #333333; line-height: 1.5; border-top: 1px solid #eeeeee; padding-top: 15px;">
Best,<br>
<b>Shiv</b><br>
SEO/AEO Consultant<br>
<b>Innovate Marketers LLC</b><br>
<a href="tel:+16452201660" style="color: #1a73e8; text-decoration: none;">+1(645) 220-1660</a><br>
382 NE 191st St PMB 171379, Miami, FL, 33179-3899, US<br>
</div>
"""

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def get_bedrock_client(cfg: dict = None):
    if not cfg:
        cfg = load_config()
    return boto3.client(
        "bedrock-runtime",
        region_name=cfg.get("aws_region", "us-east-1"),
        aws_access_key_id=cfg.get("aws_access_key_id"),
        aws_secret_access_key=cfg.get("aws_secret_access_key")
    )

def sanitize_anti_spam_header(header_html: str) -> str:
    """Strictly sanitizes and obfuscates emails, URLs, and protocols.
    Completely strips http://, https://, and mailto: to prevent Gmail/Outlook from
    autolinking text into blue clickable hyperlinks that trip spam/phishing filters.
    Guarantees spaces around all dots and @ symbols.
    """
    if not header_html:
        return ""
    # 1. Strip mailto:
    text = re.sub(r'mailto:\s*', '', header_html, flags=re.IGNORECASE)
    # 2. Strip http:// and https:// entirely
    text = re.sub(r'https?://', '', text, flags=re.IGNORECASE)
    # 3. Strip trailing slashes from domain endings
    text = re.sub(r'(?<=\w)/(?=\s|$|<|\b)', '', text)
    # 4. Obfuscate emails: name@domain.com -> name @ domain . com
    def replace_email(match):
        user, domain = match.groups()
        domain_obf = re.sub(r'\.', ' . ', domain)
        return f"{user} @ {domain_obf}"
    text = re.sub(r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', replace_email, text)
    # 5. Obfuscate www URLs: www.domain.com -> www . domain . com
    def replace_www(match):
        parts = match.group(0).split('.')
        return ' . '.join(p.strip() for p in parts if p.strip())
    text = re.sub(r'\bwww\.[a-zA-Z0-9.-]+\b', replace_www, text, flags=re.IGNORECASE)
    # 6. Obfuscate naked domains: domain.com -> domain . com
    tlds = '(?:com|org|net|edu|gov|io|co|ai|ca|us|uk|info|biz|dev|app|xyz)'
    text = re.sub(r'(?<!\s\.\s)\b([a-zA-Z0-9-]+)\.(' + tlds + r')\b', r'\1 . \2', text, flags=re.IGNORECASE)
    # 7. Strip any leftover broken protocol chunks like 'https: / /' or 'http: / /'
    text = re.sub(r'https?:\s*/+\s*', '', text, flags=re.IGNORECASE)
    # Clean up double spaces if any
    text = re.sub(r' +', ' ', text)
    return text

def get_dynamic_days() -> str:
    """Calculate the next two business days from today for the email CTA.
    e.g. Sunday -> 'Tuesday or Wednesday', Wednesday -> 'Thursday or Friday'
    """
    today = datetime.now()
    days_found = []
    check = today
    while len(days_found) < 2:
        check += timedelta(days=1)
        # 0=Mon, 5=Sat, 6=Sun
        if check.weekday() < 5:
            days_found.append(check.strftime('%A'))
    return f"{days_found[0]} or {days_found[1]}"


def generate_outreach_email_and_brief(lead_info: Dict[str, Any], metrics: Dict[str, Any]) -> Tuple[str, str, str]:
    """Generates:
    1. Report-style HTML Audit Email with client-only quoted box,
       inline scorecard screenshot, 3 bold-header diagnostic paragraphs with #f1c232 highlights,
       dynamic-day Zoom CTA, and official signature.
    2. Email Subject line.
    3. Markdown Call Copilot Briefing saved to knowledge_base/leads/{client_slug}.md.
    """
    cfg = load_config()
    model_id = cfg.get("bedrock_model", "moonshotai.kimi-k2.5")
    bedrock_client = get_bedrock_client(cfg)

    company_name = lead_info.get("company_name", "Your Business")
    client_name = lead_info.get("client_name", "there")
    first_name = lead_info.get("first_name", "there")
    client_slug = lead_info.get("client_slug", "lead")
    website = lead_info.get("website", "")
    domain = lead_info.get("domain", "")
    email = lead_info.get("email", "")
    phone = lead_info.get("phone", "")
    location = lead_info.get("location", "USA")
    niche = lead_info.get("niche", "Local Services")
    colleague_name = lead_info.get("colleague_name", "My colleague")
    client_reply_text = lead_info.get("client_reply_text", "")
    subject = lead_info.get("subject", "Re: Quick question")
    quoted_header_html = lead_info.get("quoted_header_html") or lead_info.get("quoted_box_html", "")
    quoted_header_html = sanitize_anti_spam_header(quoted_header_html)

    as_score = str(metrics.get("authority_score", "0"))
    traffic = str(metrics.get("organic_traffic", "0"))
    kws = str(metrics.get("keywords", "0"))
    backlinks = str(metrics.get("backlinks", "0"))
    ref_domains = str(metrics.get("referring_domains", "0"))
    traffic_share_us = str(metrics.get("traffic_share_us", "N/A"))
    ai_vis = str(metrics.get("ai_visibility", "0"))
    traffic_trend = str(metrics.get("traffic_trend", "Flatline at 0"))

    print(f"\n[Generator] Synthesizing email & brief for {company_name} using {model_id}...")

    prompt = f"""You are an elite SEO/AEO Consultant at Innovate Marketers LLC writing a high-converting Open Loop Technical Audit email for a prospect who replied to our colleague.

CORE PRINCIPLE:
The email's ONLY job is to get a reply. NOT to book a call. NOT to close a deal. Deliver the promised technical data and competitor reality, then create an Open Loop by presenting 2 findings clearly and holding the 3rd finding behind a simple, business-specific question they can answer in 1 sentence from their mobile phone.

STRICT ANTI-SPAM & ANTI-AUTOLINK RULES:
- NEVER write http://, https://, or contiguous email addresses anywhere.
- Every domain MUST have spaces around EVERY dot (e.g. www . domain . com or domain . com).
- Every email MUST have spaces around @ and EVERY dot (e.g. name @ domain . com).

PROSPECT PROFILE:
- Company Name: {company_name}
- Decision Maker: {client_name} (First Name: {first_name})
- Website: {website} (Domain: {domain})
- Geographic Market: {location}
- Niche & Industry: {niche}
- Colleague who forwarded reply: {colleague_name}
- Client's Reply: "{client_reply_text}"

DIAGNOSTIC METRICS:
- Authority Score: {as_score} / 100
- Monthly Organic Traffic: {traffic} visits/mo
- Keywords Indexed: {kws} terms
- Backlinks & Referring Domains: {backlinks} links across {ref_domains} domains
- AI Search Visibility: {ai_vis}

TASK 1: AUTHORITY VALIDATION + COMPETITOR PUNCH (<COMPETITOR_PUNCH>)
Write 2-3 sentences:
Validate their backlink strength first ({backlinks} backlinks across {ref_domains} referring domains).
Then contrast it with reality: Google is only sending them {traffic} visits/mo, while 1 to 2 REAL local competitors in {location} are dominating Google page 1 and capturing high-ticket {niche} business. Name 1-2 real local competitors in {location}.

TASK 2: THREE TECHNICAL FINDINGS (<TECHNICAL_FINDINGS>)
Provide 3 numbered points:
1. <strong>The Indexation Gap:</strong> Google is indexing them for generic/few keywords ({kws} terms) while high-intent commercial buyer searches in {location} are completely missing.
2. <strong>The Authority Disconnect:</strong> Their {backlinks} backlinks are bottled up at root due to crawl-level errors/unoptimized assets, preventing ranking power from flowing into service/product pages.
3. <strong>Operational / Service Alignment (HELD):</strong> Frame the 3rd finding as an issue that depends on their specific business setup and client flow.

TASK 3: OPEN LOOP QUESTION (<OPEN_LOOP_QUESTION>)
Ask a single, highly relevant, business-specific question about their operations/geography/client acquisition that they can answer in 1 sentence from their phone (e.g., local walk-in vs shipping, city-center vs surrounding metro, residential vs commercial).

TASK 4: CALL COPILOT SALES DOSSIER (<CALL_BRIEFING>)
Generate a concise markdown sales dossier with contact info, metrics, local competitors, and simple phone/voicemail scripts.

OUTPUT FORMAT (strictly inside these XML tags):
<COMPETITOR_PUNCH>
(2-3 sentences contrasting backlink authority with local competitor dominance)
</COMPETITOR_PUNCH>

<TECHNICAL_FINDINGS>
<li style="margin-bottom: 12px;"><strong>Finding 1 Title:</strong> Description</li>
<li style="margin-bottom: 12px;"><strong>Finding 2 Title:</strong> Description</li>
<li style="margin-bottom: 12px;"><strong>Finding 3 Title (Held):</strong> Description</li>
</TECHNICAL_FINDINGS>

<OPEN_LOOP_QUESTION>
(1-sentence business-specific question)
</OPEN_LOOP_QUESTION>

<CALL_BRIEFING>
(complete markdown dossier)
</CALL_BRIEFING>"""

    competitor_punch = f"You have {backlinks} backlinks and {ref_domains} referring domains &mdash; that is a genuinely strong foundation. Most businesses in {location} don't come close to that. But despite that authority, Google is only sending you {traffic} visits a month, while local competitors are sitting right at the top of Google capturing high-ticket {niche} clients."
    technical_findings = f"""<li style="margin-bottom: 12px;"><strong>The Indexation Gap:</strong> Google is currently indexing your website for only {kws} keywords, missing high-intent commercial searches in {location}.</li>
<li style="margin-bottom: 12px;"><strong>The Authority Disconnect:</strong> Your {backlinks} backlinks are disconnected from your primary service pages due to crawl-level errors and metadata blocks.</li>
<li style="margin-bottom: 12px;"><strong>Service Radius &amp; Local Entity Anchoring:</strong> Google's algorithm treats your website as unanchored rather than connecting your operations directly to regional search demand. But whether this is actively hurting inquiries depends on your actual customer distribution.</li>"""
    open_loop_question = f"Quick question: Are most of your clients coming directly from {location} itself, or are you pulling substantial volume from surrounding areas?"
    call_briefing_md = ""

    try:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}]
        )
        raw_text = response['output']['message']['content'][0]['text'].strip()

        # Parse tags
        cp_match = re.search(r'<COMPETITOR_PUNCH>([\s\S]*?)</COMPETITOR_PUNCH>', raw_text, re.IGNORECASE)
        tf_match = re.search(r'<TECHNICAL_FINDINGS>([\s\S]*?)</TECHNICAL_FINDINGS>', raw_text, re.IGNORECASE)
        ol_match = re.search(r'<OPEN_LOOP_QUESTION>([\s\S]*?)</OPEN_LOOP_QUESTION>', raw_text, re.IGNORECASE)
        cb_match = re.search(r'<CALL_BRIEFING>([\s\S]*?)</CALL_BRIEFING>', raw_text, re.IGNORECASE)

        if cp_match and cp_match.group(1).strip():
            competitor_punch = cp_match.group(1).strip()
        if tf_match and tf_match.group(1).strip():
            technical_findings = tf_match.group(1).strip()
        if ol_match and ol_match.group(1).strip():
            open_loop_question = ol_match.group(1).strip()
        if cb_match and cb_match.group(1).strip():
            call_briefing_md = cb_match.group(1).strip()
    except Exception as e:
        print(f"Warning in Bedrock call: {e}")

    def clean_text(t: str) -> str:
        if not t:
            return ""
        return t.replace('—', ' &mdash; ').replace('–', ' &mdash; ').replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')

    competitor_punch = clean_text(competitor_punch)
    open_loop_question = clean_text(open_loop_question)

    website_spaced = re.sub(r'https?://', '', website).rstrip('/')
    website_spaced = re.sub(r'\.', ' . ', website_spaced)

    # Assemble Open Loop Report-Delivery Email HTML
    email_html = f"""<div style="font-family: Arial, Helvetica, sans-serif; font-size: 15px; color: #111827; line-height: 1.6; max-width: 680px;">

<p style="margin: 0 0 16px 0;">Hi {first_name},</p>

<p style="margin: 0 0 16px 0;">My colleague {colleague_name} forwarded me your reply asking us to send over the website report and errors we spotted on {website_spaced}:</p>

{quoted_header_html}

<p style="margin: 0 0 16px 0;">I pulled your live Google search and domain diagnostic data today. Here is the high-level snapshot:</p>

<ul style="margin: 0 0 16px 20px; padding: 0; line-height: 1.6;">
  <li><strong>Domain Authority Score:</strong> {as_score} / 100</li>
  <li><strong>Monthly Organic Traffic:</strong> {traffic} visits/mo</li>
  <li><strong>Total Backlinks &amp; Referring Domains:</strong> {backlinks} links across {ref_domains} domains</li>
  <li><strong>Organic Keywords Indexed:</strong> {kws} terms</li>
  <li><strong>AI Search Visibility:</strong> {ai_vis}</li>
</ul>

<p style="margin: 0 0 16px 0;">Here is your live diagnostic scorecard pulled directly from our analytics system:</p>

<div style="text-align: center; margin: 20px 0;">
  <img src="cid:semrush_screenshot" alt="{company_name} SEO Diagnostic Scorecard" style="max-width: 100%; height: auto; border: 1px solid #e5e7eb; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);" />
</div>

<p style="margin: 0 0 16px 0;">{competitor_punch}</p>

<p style="margin: 0 0 16px 0;">We identified 3 technical issues blocking your website from Google's first page:</p>

<ol style="margin: 0 0 20px 20px; padding: 0; line-height: 1.6;">
  {technical_findings}
</ol>

<p style="margin: 0 0 16px 0; font-size: 16px; font-weight: bold; color: #111827;">{open_loop_question}</p>

<p style="margin: 0 0 20px 0;">Once I know that, I can confirm whether this third issue applies to your setup and send you the complete fix list.</p>

{OFFICIAL_SIGNATURE_HTML}

</div>"""

    # Save Call Copilot Brief
    brief_path = os.path.join(LEADS_KB_DIR, f"{client_slug}.md")
    if not call_briefing_md:
        call_briefing_md = f"""# Client Briefing: {company_name}

**Lead Profile for Call Copilot & Live Sales Support**

---

## 1. Contact & Lead Information
* **Client Contact Name:** {client_name}
* **Company Name:** {company_name}
* **Website:** {website}
* **Email:** `{email}`
* **Phone:** {phone}
* **Location & Timezone:** {location}
* **Assigned Closer/Rep:** Shiv (Innovate Marketers)
* **Outreach Colleague:** {colleague_name}
* **Lead Origin:** {client_reply_text}

---

## 2. Semrush SEO Diagnostic (Live Audit)
* **Authority Score:** **{as_score} / 100**
* **Organic Search Traffic:** **{traffic} monthly visits**
* **Organic Keywords:** **{kws} keywords**
* **Backlinks:** **{backlinks} backlinks** across **{ref_domains} referring domains**

---

## 3. Recommended Services & Packages (Innovate Marketers)
* **Primary Recommendation:** Local SEO & Google Maps Optimization ($450 - $650/mo)

---

## 4. Live Call Script / Call Copilot Cheat Sheet
```text
Client: {client_name} ({company_name} - {location})
Colleague: {colleague_name}
SEO Stats: AS {as_score}, {traffic} visits, {kws} keywords
```
"""
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(call_briefing_md)
    print(f"[Generator] Saved Call Copilot briefing to: {brief_path}")

    return email_html, subject, brief_path
