"""
# ==============================================================================
# EMAIL TEMPLATE: OPEN LOOP REPORT-DELIVERY STANDARD
# ==============================================================================
#
# PURPOSE & PSYCHOLOGY:
# 1. Delivers on the promise: The client agreed to receive a "report" or "screenshot
#    of errors." We deliver a thorough, professional technical diagnostic.
# 2. Breaks the "Freeze at Reply" Barrier: Previous 480-word emails got opened 5+
#    times because clients found the data fascinating, but they never replied because
#    the email ended in a high-friction meeting pitch ("Would Wed or Thu work for a
#    10-minute Zoom?"). Prospects don't want to commit to a sales calendar.
# 3. The Open Loop: We reveal Findings 1 and 2 in clear business terms, then HOLD
#    Finding 3 behind a single business-specific question only they can answer.
# 4. Compels 1-Sentence Reply: They can answer the question in 5 seconds from their
#    phone. Once they reply, you are in a live two-way conversation.
# ==============================================================================

# --- SUBJECT LINE ---
# Keep in-thread subject: Re: [Original Subject]

# --- HTML TEMPLATE ---
OPEN_LOOP_HTML_TEMPLATE = \"\"\"<div style="font-family: Arial, Helvetica, sans-serif; font-size: 15px; color: #111827; line-height: 1.6; max-width: 680px;">

<p style="margin: 0 0 16px 0;">Hi {client_first_name},</p>

<p style="margin: 0 0 16px 0;">My colleague {colleague_name} forwarded me your reply asking us to send over the website report and errors we spotted on {website_spaced}:</p>

<!-- CLIENT'S QUOTED REPLY ONLY (NO MARKETING EMAIL, MONOSPACE, SPACED DOTS & @) -->
<div style="background-color: #fafafa; border: 1px solid #d1d5db; border-radius: 4px; padding: 12px; margin-bottom: 20px; font-family: monospace; font-size: 12px; color: #4b5563; line-height: 1.5;">
<strong>From:</strong> {client_name} &lt;{client_email_spaced}&gt;<br>
<strong>Sent:</strong> {reply_sent_date}<br>
<strong>To:</strong> {colleague_name} &lt;{colleague_email_spaced}&gt;<br>
<strong>Subject:</strong> {reply_subject}<br><br>
{client_reply_body}
</div>

<p style="margin: 0 0 16px 0;">I pulled your live Google search and domain diagnostic data today. Here is the high-level snapshot:</p>

<ul style="margin: 0 0 16px 20px; padding: 0; line-height: 1.6;">
  <li><strong>Domain Authority Score:</strong> {authority_score} / 100</li>
  <li><strong>Monthly Organic Traffic:</strong> {organic_traffic} visits/mo</li>
  <li><strong>Total Backlinks &amp; Referring Domains:</strong> {backlinks_count} links across {referring_domains_count} domains</li>
  <li><strong>Organic Keywords Indexed:</strong> {keywords_indexed} terms</li>
  <li><strong>AI Search Visibility:</strong> {ai_search_visibility}</li>
</ul>

<p style="margin: 0 0 16px 0;">Here is your live diagnostic scorecard pulled directly from our analytics system:</p>

<!-- WHITE-LABEL SCORECARD IMAGE -->
<div style="text-align: center; margin: 20px 0;">
  <img src="cid:semrush_screenshot" alt="{company_name} SEO Diagnostic Scorecard" style="max-width: 100%; height: auto; border: 1px solid #e5e7eb; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);" />
</div>

<!-- AUTHORITY VALIDATION + COMPETITOR PUNCH (2-3 SENTENCES MAX) -->
<p style="margin: 0 0 16px 0;">You have {backlinks_count} backlinks and {referring_domains_count} referring domains &mdash; that is a genuinely strong foundation. Most {industry_plural} in {city_or_region} don't come close to that.</p>

<p style="margin: 0 0 16px 0;">But despite that authority, Google is only sending you {organic_traffic} visitors a month. Meanwhile, <strong>{competitor_1}</strong> and <strong>{competitor_2}</strong> in your same {city_or_region} are sitting right at the top of Google, capturing those {ticket_size} {orders_or_clients}.</p>

<!-- THE OPEN LOOP: 2 FINDINGS REVEALED, 3RD HELD BEHIND A QUESTION -->
<p style="margin: 0 0 16px 0;">We identified 3 technical issues blocking your website from Google's first page:</p>

<ol style="margin: 0 0 20px 20px; padding: 0; line-height: 1.6;">
  <li style="margin-bottom: 12px;"><strong>{finding_1_title}:</strong> {finding_1_description}</li>
  <li style="margin-bottom: 12px;"><strong>{finding_2_title}:</strong> {finding_2_description}</li>
  <li style="margin-bottom: 12px;"><strong>{finding_3_title_held}:</strong> {finding_3_held_explanation}</li>
</ol>

<p style="margin: 0 0 16px 0; font-size: 16px; font-weight: bold; color: #111827;">{open_loop_question}</p>

<p style="margin: 0 0 20px 0;">Once I know that, I can confirm whether this third issue applies to your setup and send you the complete fix list.</p>

<!-- PROFESSIONAL SIGNATURE -->
<div style="margin-top: 24px; border-top: 1px solid #e5e7eb; padding-top: 16px; font-family: Arial, sans-serif; font-size: 13px; color: #374151; line-height: 1.5;">
Best,<br>
<strong>Shiv</strong><br>
<strong>SEO/AEO Consultant</strong><br>
<strong>Innovate Marketers LLC</strong><br>
Direct: +1(645) 220-1660<br>
Address: 382 NE 191st St PMB 171379, Miami, FL, 33179-3899, US
</div>

</div>\"\"\"

# ==============================================================================
# OPEN LOOP QUESTIONS BY NICHE / BUSINESS MODEL
# ==============================================================================
# The question MUST be something specific to their operations that only they know,
# and that can be answered in one sentence from a mobile phone:
#
# 1. B2B / Rental / Equipment:
#    "Quick question on your operations: Are most of your rentals handled locally
#    out of your [City/State] facility, or are you actively shipping equipment
#    nationwide?"
#
# 2. E-Commerce / Auto Parts / Retail:
#    "Quick question on your sales mix: Are most of your customers local walk-ins
#    at your [City/Street] location, or online orders shipping out across [Region]?"
#
# 3. Photography / Creative / Boudoir:
#    "Quick question on your client base: Are most of your portrait clients coming
#    from [City] itself, or are women driving in from [surrounding metro / counties]?"
#
# 4. Local Service / Contractors (Roofing, Paving, Tree Care):
#    "Quick question on your service radius: Are you focusing strictly on residential
#    jobs within [City], or do you take on commercial contracts across [County/Region]?"
#
# 5. Multi-Location / Franchise:
#    "Quick question: Are most of your inquiries coming through your [City A] hub,
#    or is [City B] pulling substantial booking volume independently?"
#
# ==============================================================================
# 48-HOUR IN-THREAD FOLLOW-UP STANDARD (Strictly under 40 words, no signature)
# ==============================================================================
#
# Target Subject: Keep exact existing thread
#
# Follow-Up Text:
# "Hi [Client Name],
#
# Did you get a chance to see the scorecard above?
#
# I still have that third finding on hold &mdash; just need your quick input on
# whether [repeat short 5-word version of the open loop question]?
#
# Once I know, I'll send over the complete fix list."
