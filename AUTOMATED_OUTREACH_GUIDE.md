# 🚀 Automated Lead Outreach & SEO Audit System — User Guide
**Agency:** Innovate Marketers LLC  
**Owner / Closer:** Shiv (Shiv Prasad Farale)  
**Primary Engine:** AWS Bedrock (`moonshotai.kimi-k2.5`) + Playwright + Gmail API  

---

## 📌 1. What Is This System?

This system is an automated, high-converting outreach and follow-up pipeline designed for **Innovate Marketers**.

Instead of manually checking Semrush, taking screenshots, cropping images, writing customized audit emails, formatting yellow highlights, and drafting emails one by one, this system handles the complete workflow:

1. **Intake:** You paste a lead's PMS screenshot (`Win+Shift+S` & `Ctrl+V`) and email thread text into a single file ([`leads.md`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/leads.md)) or drop them in chat.
2. **Analysis:** AWS Bedrock Multimodal AI reads the PMS screenshot to extract client contact information and website details.
3. **Colleague Attribution:** It strictly identifies the colleague who actually sent the outreach email (e.g., Edward, Melissa, Vipin, Rada, James, William, Rain) from the email thread—never confusing them with internal account managers.
4. **Semrush Capture:** Automatically opens the client's Semrush Domain Overview, handles the free 10-search daily limit if triggered, and takes a clean white-label crop of the SEO scorecard (no sidebar, no URL bar).
5. **Mobile-First & Curiosity-Driven Email Drafting:**
   - 4-sided boxed previous conversation quoting only the client's reply with obfuscated links.
   - Clean inline white-label Semrush scorecard.
   - **Pro Diagnostic Block (Strictly under 40 words, max 2 sentences):** Highlights key metrics and exposes the fatal flaw in executive honey gold (`#f1c232`).
   - **Competitor Revenue Hook (Strictly under 40 words, max 2 sentences):** Highlights high-ticket services slipping to competitors and aggregators.
   - **Free Consultation CTA:** 10–15 minute Google Meet / Zoom walkthrough with zero charge or obligation.
   - Official signature block with title, direct phone (+1 645-220-1660), Miami address, and Mailtrack notice.
6. **Web Gmail Draft Injection:** Injects the un-sent draft directly into your live **Web Gmail Drafts** folder (`mail.google.com`).
7. **Call Copilot Briefing:** Saves a full sales dossier in `knowledge_base/leads/{client_slug}.md` with missed revenue tables, 30-second phone openers, and closing scripts.
8. **In-Thread 48-Hour Follow-Up (`run_followup.py`):** Automatically locates the sent thread in Gmail and injects an un-sent follow-up draft **directly inside the existing conversation thread** for 100% human review before hitting Send.

---

## 📂 2. Core File Directory Map

| File Path | Description / Role |
| :--- | :--- |
| [`leads.md`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/leads.md) | **Intake Queue:** Paste new leads here (PMS screenshots + conversation text). |
| [`run_outreach.py`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/run_outreach.py) | **Master Initial Outreach Runner:** Processes all leads in `leads.md` and creates Gmail drafts. |
| [`run_followup.py`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/run_followup.py) | **In-Thread Follow-Up Runner:** Injects personalized 48-hour follow-up drafts directly inside existing Gmail threads. |
| [`src/lead_parser.py`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/src/lead_parser.py) | **Parser Module:** Extracts client data via Bedrock vision and formats the anti-spam boxed quote. |
| [`src/semrush_crawler.py`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/src/semrush_crawler.py) | **Crawler Module:** Opens Semrush, handles free limit prompts, crops white-label scorecards. |
| [`src/outreach_generator.py`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/src/outreach_generator.py) | **Initial Outreach Copywriting Engine:** Crafts the mobile-first email with `#f1c232` highlights and Call Copilot dossier. |
| [`src/followup_generator.py`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/src/followup_generator.py) | **Follow-Up Copywriting Engine:** Crafts ultra-concise (<40 words) in-thread follow-up notes. |
| [`src/gmail_helper.py`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/src/gmail_helper.py) | **Gmail API Module:** Injects drafts into Web Gmail (both standalone drafts and in-thread drafts). |
| [`config.yaml`](file:///c:/Users/shiva/OneDrive/Documents/call_copilot/config.yaml) | **Configuration:** AWS Bedrock keys, model selection (`moonshotai.kimi-k2.5`), and rep profile. |
| `screenshots/` | **Image Storage:** Holds cropped white-label scorecard images (`screenshots/{client_slug}_seo.png`). |
| `knowledge_base/leads/` | **Sales Dossiers:** Holds full Call Copilot briefings generated for every lead. |

---

## 🛠️ 3. How to Send Initial Outreach Emails

### Step 1: Add Leads to `leads.md`
```markdown
# Lead: Business Name

![PMS Record](paste_your_screenshot_here)

## Conversation
---------- Forwarded message ---------
From: Client Name <client@domain.com>
Date: Thu, Sep 3, 2026 at 5:40 AM
Subject: Re: Web screenshot ##
To: Colleague Name <colleague@gmail.com>

Client reply goes here

---
```

### Step 2: Run the Pipeline
```powershell
python run_outreach.py
```
*(Or simply paste the lead directly into Antigravity chat!)*

### Step 3: Review & Send in Web Gmail
1. Open **[mail.google.com](https://mail.google.com)** &rarr; **Drafts**.
2. Review the pre-filled email with inline scorecard and gold highlights.
3. Click **Send**!

---

## 🔁 4. How the In-Thread 48-Hour Follow-Up Works

If a prospect doesn't reply after 48 hours, you can create a follow-up draft attached to the **exact same email thread**:

```powershell
# Follow up using the client slug:
python run_followup.py --slug canyondavetours

# Or follow up directly using the recipient email:
python run_followup.py --email canyondavetours@gmail.com
```

### 🔒 100% Manual Send Control (Never Sends Automatically)
* The script **ONLY creates a DRAFT** inside the thread.
* It does **not** send the email.
* It does **not** notify the client.
* You open the thread in your browser &rarr; review the pre-filled draft &rarr; edit if desired &rarr; and click **Send** yourself.

### 📝 What the Follow-Up Looks Like (Inside the Existing Thread):
> **Hi [Client Name],**
>
> Following up on my note above — did you get a chance to review the website performance scorecard?
>
> We have a couple of slots open this Thursday afternoon and Friday morning to show you how to fix that [specific leak] and walk through the competitor keyword roadmap.
>
> Would either of those times work for a quick 10-minute Google Meet?
>
> --  
> **Shiv** | Sales Consultant | Innovate Marketers LLC | +1(645) 220-1660

---

## 📞 5. Phone & Voicemail Scripts (Follow-Up Script)

### When They Answer:
> *"Hi [Name], this is Shiv.*  
> *This is a follow-up call regarding your email reply to my colleague about your website and SEO problem.*  
> *I just sent you the details to your email.*  
> *Can we do a quick 5-minute call tomorrow to look at it together?"*

**If they ask "What is it about?":**
> *"Your website is not ranking on Google, and competitors are taking all the customers. I can show you what to fix in 5 minutes."*

### If Voicemail:
> *"Hi [Name], this is Shiv.*  
> *This is a follow-up call regarding your email reply to my colleague about your website and SEO problem.*  
> *I just sent the details to your email. Please check your inbox, or call me back at (645) 220-1660.*  
> *Thank you!"*

### Scenario C: Instant SMS (If No Answer)
> *"Hi [Client Name], Shiv here with Innovate Marketers following up on [Colleague]'s thread. Just sent your website audit to your inbox. What day this week works best for a quick 10-min Google Meet walkthrough? (Thursday or Friday?)"*

---

## 🔒 6. Permanent Quality Standards Locked In Code

1. **Gmail-Safe Executive Warm Gold (`#f1c232`):**  
   Highlights strictly use `<span style="background-color: #f1c232; color: #000000; font-weight: bold; padding: 2px 4px;">`. Never use HTML5 `<mark>` (which Gmail strips on send) or harsh neon yellow.
2. **Mobile-First Word Limits:**  
   Diagnostic and competitor gap paragraphs are strictly under 40 words each (maximum 2 sentences). Total email is under 170 words—reads effortlessly on an iPhone.
3. **Strict Colleague Attribution:**  
   Always identifies the colleague who actually sent the outreach email from the thread (e.g. Edward, Melissa, Vipin, Rada, James, William, Rain). Never confuses them with internal account managers.
4. **Anti-Spam Header Formatting:**  
   The previous email is quoted in a 4-sided `#fafafa` grey box with obfuscated spaces in links/emails (e.g. `client @ domain . com`) so spam filters never flag it.
5. **Scorecard Quality:**  
   Screenshots are strictly cropped to data scorecards (AI Search + SEO cards), completely removing sidebars, logos, and URL bars.
