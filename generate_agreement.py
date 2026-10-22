"""Agreement Generator for Dayna Hale (Blue Oasis Global)
Generates the exact 5-page Search Engine Optimization Services Agreement
with side-by-side comparison tables for BOTH plans (Standard $799 CAD vs Professional $1,299 CAD)
so the client can clearly see the differences and choose the best plan.
"""

import os
import sys
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

WORKSPACE_ROOT = Path(__file__).resolve().parent

def get_logo_b64():
    logo_path = WORKSPACE_ROOT / "assets" / "innovate_logo.png"
    if not logo_path.exists():
        raise FileNotFoundError(f"Missing logo at {logo_path}")
    with open(logo_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_agreement_html():
    logo_b64 = get_logo_b64()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SEO Services Agreement - Dayna Hale</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

  @page {{
    size: 8.5in 11in;
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
    background: #ffffff;
    font-size: 12.5px;
    line-height: 1.5;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  .page {{
    width: 8.5in;
    height: 11in;
    position: relative;
    page-break-after: always;
    page-break-inside: avoid;
    overflow: hidden;
    background: #ffffff;
  }}

  /* Fixed Header Banner */
  .header-banner {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 125px;
    overflow: hidden;
    z-index: 10;
  }}

  .header-svg {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 125px;
    z-index: 1;
  }}

  .header-content {{
    position: relative;
    z-index: 2;
    padding: 16px 42px 0 42px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }}

  .header-logo {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}

  .header-logo img {{
    height: 42px;
    object-fit: contain;
    filter: brightness(0) invert(1);
  }}

  .header-contact {{
    text-align: right;
    color: #ffffff;
    font-size: 10.5px;
    line-height: 1.45;
    font-weight: 500;
  }}

  .header-contact-item {{
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
  }}

  .header-contact-item svg {{
    width: 12px;
    height: 12px;
    fill: #ffffff;
    opacity: 0.95;
  }}

  /* Fixed Footer Banner */
  .footer-banner {{
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 95px;
    overflow: hidden;
    z-index: 10;
  }}

  .footer-svg {{
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 95px;
    z-index: 1;
  }}

  .footer-content {{
    position: absolute;
    bottom: 16px;
    left: 42px;
    right: 42px;
    z-index: 2;
    color: #ffffff;
    font-size: 8.5px;
    line-height: 1.35;
  }}

  .footer-content strong {{
    font-weight: 700;
    letter-spacing: 0.5px;
  }}

  /* Page Content Container strictly bounded between header and footer */
  .content {{
    position: absolute;
    top: 130px;
    bottom: 95px;
    left: 0;
    right: 0;
    padding: 12px 46px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}

  .doc-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 15.5px;
    font-weight: 800;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #0b1e3b;
    margin-bottom: 20px;
    text-decoration: underline;
    text-underline-offset: 4px;
  }}

  .lead-para {{
    font-size: 12.5px;
    line-height: 1.6;
    color: #1e293b;
    margin-bottom: 18px;
  }}

  .section-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 700;
    color: #0b1e3b;
    margin-top: 12px;
    margin-bottom: 4px;
  }}

  .section-content {{
    font-size: 12px;
    line-height: 1.5;
    color: #334155;
    margin-bottom: 8px;
  }}

  ul.bullet-list {{
    list-style: none;
    padding-left: 18px;
    margin-bottom: 10px;
  }}

  ul.bullet-list li {{
    position: relative;
    margin-bottom: 4.5px;
    font-size: 12px;
    line-height: 1.5;
    color: #334155;
  }}

  ul.bullet-list li::before {{
    content: "•";
    position: absolute;
    left: -14px;
    top: 0;
    color: #1e293b;
    font-weight: bold;
    font-size: 13px;
  }}

  /* Signatures on Page 3 */
  .sig-section {{
    margin-top: 15px;
    font-size: 12.5px;
    line-height: 1.6;
  }}

  .sig-block {{
    margin-top: 22px;
    display: flex;
    flex-direction: column;
    gap: 3.5px;
    font-size: 12px;
  }}

  .sig-row {{
    display: flex;
    align-items: center;
    margin-top: 9px;
    font-size: 12px;
  }}

  .sig-row span.label {{
    width: 65px;
    font-weight: 600;
  }}

  .sig-row span.underline {{
    border-bottom: 1px solid #64748b;
    width: 250px;
    height: 18px;
    display: inline-block;
  }}

  .plan-select-box {{
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 16px;
    font-size: 11.5px;
  }}

  /* Comparison Table Styling for Pages 4 & 5 */
  .annexure-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12.5px;
    font-weight: 800;
    color: #0b1e3b;
    margin-bottom: 6px;
  }}

  table.compare-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 8.8px;
    border: 1px solid #000000;
    background: #ffffff;
  }}

  table.compare-table th {{
    padding: 4px 6px;
    font-size: 8.8px;
    font-weight: 700;
    border: 1px solid #000000;
    vertical-align: middle;
  }}

  table.compare-table td {{
    padding: 2.2px 6px;
    border: 1px solid #d1d5db;
    vertical-align: middle;
    color: #1e293b;
    line-height: 1.25;
  }}

  table.compare-table tr.cat-header td {{
    background: #f1f5f9;
    font-weight: 800;
    text-transform: uppercase;
    font-size: 8.2px;
    letter-spacing: 0.4px;
    color: #0b2545;
    border-top: 1px solid #000000;
    border-bottom: 1px solid #000000;
    padding: 3px 6px;
  }}

  table.compare-table td.col-act {{
    width: 52%;
    color: #0f172a;
  }}

  table.compare-table td.col-std {{
    width: 24%;
    text-align: center;
    border-left: 1px solid #cbd5e1;
    background: #ffffff;
  }}

  table.compare-table td.col-pro {{
    width: 24%;
    text-align: center;
    border-left: 1px solid #cbd5e1;
    background: #f8fafc;
    font-weight: 600;
  }}

  table.compare-table td.check {{
    color: #059669;
    font-weight: 800;
  }}

  table.compare-table td.cross {{
    color: #dc2626;
    font-weight: 800;
  }}

  .addon-summary-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 6px;
  }}

  .addon-box-green {{
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 8.2px;
    line-height: 1.35;
    color: #166534;
  }}

  .partnership-note-card {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 8.2px;
    line-height: 1.35;
    color: #334155;
  }}

</style>
</head>
<body>

<!-- ========================================== -->
<!-- PAGE 1: Scope, Timeline, Payment, Terms    -->
<!-- ========================================== -->
<div class="page">
  <!-- Header Banner -->
  <div class="header-banner">
    <svg class="header-svg" viewBox="0 0 816 125" preserveAspectRatio="none">
      <defs>
        <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0b1e3b"/>
          <stop offset="100%" stop-color="#112952"/>
        </linearGradient>
      </defs>
      <path d="M0,0 L816,0 L816,95 C620,135 420,70 0,115 Z" fill="#1d63ed" />
      <path d="M0,0 L816,0 L816,80 C600,125 380,55 0,98 Z" fill="url(#headerGrad)" />
    </svg>
    <div class="header-content">
      <div class="header-logo">
        <img src="data:image/png;base64,{logo_b64}" alt="Innovate Marketers">
      </div>
      <div class="header-contact">
        <div class="header-contact-item">
          <span>+1 (645) 220-1660</span>
          <svg viewBox="0 0 24 24"><path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.57a1 1 0 01-.25 1.02l-2.2 2.2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>shiv.f@innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>www.innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>30 N Gould St Ste R Sheridan, WY 82801 USA</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
        </div>
      </div>
    </div>
  </div>

  <!-- Content -->
  <div class="content">
    <div class="doc-title">SEARCH ENGINE OPTIMIZATION SERVICES AGREEMENT</div>
    
    <div class="lead-para">
      This Search Engine Optimization Services Agreement (“Agreement”) is made and generated as of <strong>October 23rd, 2026</strong> by and between <strong>Innovate Marketers LLC</strong> (“Service Provider”) and <strong>Dayna Hale, Blue Oasis Life Programs / Goldfields Global Canada, blueoasisglobal.com / blueoasis.life</strong> (“Customer”).
    </div>

    <div class="section-title">1. Scope of Services</div>
    <div class="section-content">
      The Service Provider agrees to provide Search Engine Optimization (SEO) services, Voice Search Optimization, A.I Optimization including but not limited to optimization for Social media and other activities as detailed in Annexure 1 for Customer's elected plan tier.
    </div>

    <div class="section-title">2. Timeline</div>
    <ul class="bullet-list">
      <li>The timeline for observing optimal organic and AI visibility results is estimated to be <strong>3-6 months</strong>.</li>
      <li>There is <strong>no fixed contract term</strong>, and the Customer may terminate this Agreement at any time without prior notice.</li>
    </ul>

    <div class="section-title">3. Payment Terms & Plan Options</div>
    <ul class="bullet-list">
      <li>The Customer agrees to pay the monthly service fee for the elected plan tier as detailed in Annexure 1:
        <ul style="list-style: none; padding-left: 14px; margin-top: 4px;">
          <li>• <strong>Standard Plan: $799 CAD per month</strong> (Promotional discount off standard $999 USD / ~$1,380 CAD rate)</li>
          <li>• <strong>Professional Plan: $1,299 CAD per month</strong> (Promotional discount off standard $1,599 USD / ~$2,200 CAD rate)</li>
        </ul>
      </li>
      <li>Services are billed strictly month-to-month with zero contract lock-in. Customer may upgrade, downgrade, or cancel at any time.</li>
      <li>Non-payment may result in a suspension of services until payment is received.</li>
    </ul>

    <div class="section-title">4. Cancellation and Termination</div>
    <ul class="bullet-list">
      <li>The Customer may terminate this Agreement at any time, with or without cause, by notifying the Service Provider.</li>
      <li>No refunds will be provided for any partial month of services rendered.</li>
    </ul>
  </div>

  <!-- Footer Banner -->
  <div class="footer-banner">
    <svg class="footer-svg" viewBox="0 0 816 95" preserveAspectRatio="none">
      <path d="M0,45 C250,5 550,75 816,20 L816,95 L0,95 Z" fill="#1d63ed" />
      <path d="M0,58 C260,20 560,85 816,35 L816,95 L0,95 Z" fill="#0b1e3b" />
    </svg>
    <div class="footer-content">
      <strong>DISCLAIMER:</strong><br>
      This document is confidential and intended only for the recipient; unauthorized use, disclosure, or distribution is prohibited by Innovate Marketers LLC.
    </div>
  </div>
</div>


<!-- ========================================== -->
<!-- PAGE 2: Responsibilities, Legal Terms      -->
<!-- ========================================== -->
<div class="page">
  <!-- Header Banner -->
  <div class="header-banner">
    <svg class="header-svg" viewBox="0 0 816 125" preserveAspectRatio="none">
      <defs>
        <linearGradient id="headerGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0b1e3b"/>
          <stop offset="100%" stop-color="#112952"/>
        </linearGradient>
      </defs>
      <path d="M0,0 L816,0 L816,95 C620,135 420,70 0,115 Z" fill="#1d63ed" />
      <path d="M0,0 L816,0 L816,80 C600,125 380,55 0,98 Z" fill="url(#headerGrad2)" />
    </svg>
    <div class="header-content">
      <div class="header-logo">
        <img src="data:image/png;base64,{logo_b64}" alt="Innovate Marketers">
      </div>
      <div class="header-contact">
        <div class="header-contact-item">
          <span>+1 (645) 220-1660</span>
          <svg viewBox="0 0 24 24"><path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.57a1 1 0 01-.25 1.02l-2.2 2.2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>shiv.f@innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>www.innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>30 N Gould St Ste R Sheridan, WY 82801 USA</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
        </div>
      </div>
    </div>
  </div>

  <!-- Content -->
  <div class="content">
    <div class="section-title">5. Service Provider’s Responsibilities</div>
    <ul class="bullet-list">
      <li>Perform SEO and AI optimization activities as outlined in Annexure 1 for the elected plan tier to improve Customer's organic search rankings and executive discovery.</li>
      <li>Provide regular updates, monthly rankings reports, and performance tracking of all SEO efforts.</li>
    </ul>

    <div class="section-title">6. Customer’s Responsibilities</div>
    <ul class="bullet-list">
      <li>Provide access to necessary platforms, including website CMS, analytics tools, and social media accounts (or coordinate with Customer's in-house web developer) to enable implementation.</li>
      <li>Ensure timely payment of the monthly service fee.</li>
    </ul>

    <div class="section-title">7. Confidentiality</div>
    <div class="section-content">
      Both parties agree to maintain strict confidentiality of proprietary, strategic, or sensitive business information disclosed during the term of this Agreement.
    </div>

    <div class="section-title">8. Indemnification</div>
    <div class="section-content">
      The Customer agrees to indemnify and hold harmless the Service Provider from any claims or liabilities arising from the use of the Customer’s website or marketing materials.
    </div>

    <div class="section-title">9. Miscellaneous</div>
    <ul class="bullet-list">
      <li>This Agreement constitutes the entire understanding between the parties and supersedes all prior agreements.</li>
      <li>Any amendments must be made in writing and signed by both parties.</li>
      <li>This Agreement shall be governed by and construed in accordance with the laws of the United States of America.</li>
    </ul>
  </div>

  <!-- Footer Banner -->
  <div class="footer-banner">
    <svg class="footer-svg" viewBox="0 0 816 95" preserveAspectRatio="none">
      <path d="M0,45 C250,5 550,75 816,20 L816,95 L0,95 Z" fill="#1d63ed" />
      <path d="M0,58 C260,20 560,85 816,35 L816,95 L0,95 Z" fill="#0b1e3b" />
    </svg>
    <div class="footer-content">
      <strong>DISCLAIMER:</strong><br>
      This document is confidential and intended only for the recipient; unauthorized use, disclosure, or distribution is prohibited by Innovate Marketers LLC.
    </div>
  </div>
</div>


<!-- ========================================== -->
<!-- PAGE 3: Signatures Execution & Election    -->
<!-- ========================================== -->
<div class="page">
  <!-- Header Banner -->
  <div class="header-banner">
    <svg class="header-svg" viewBox="0 0 816 125" preserveAspectRatio="none">
      <defs>
        <linearGradient id="headerGrad3" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0b1e3b"/>
          <stop offset="100%" stop-color="#112952"/>
        </linearGradient>
      </defs>
      <path d="M0,0 L816,0 L816,95 C620,135 420,70 0,115 Z" fill="#1d63ed" />
      <path d="M0,0 L816,0 L816,80 C600,125 380,55 0,98 Z" fill="url(#headerGrad3)" />
    </svg>
    <div class="header-content">
      <div class="header-logo">
        <img src="data:image/png;base64,{logo_b64}" alt="Innovate Marketers">
      </div>
      <div class="header-contact">
        <div class="header-contact-item">
          <span>+1 (645) 220-1660</span>
          <svg viewBox="0 0 24 24"><path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.57a1 1 0 01-.25 1.02l-2.2 2.2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>shiv.f@innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>www.innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>30 N Gould St Ste R Sheridan, WY 82801 USA</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
        </div>
      </div>
    </div>
  </div>

  <!-- Content -->
  <div class="content">
    <div class="sig-section">
      IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.
    </div>

    <!-- Service Provider -->
    <div class="sig-block" style="margin-top: 25px;">
      <strong style="font-size: 13.5px; color: #0b1e3b;">Innovate Marketers LLC</strong>
      <div style="margin-top: 8px; font-size: 12px; line-height: 1.55;">
        <div><strong>By:</strong> Shivaprasad Farale (Shiv)</div>
        <div><strong>Title:</strong> Senior Client Lead & SEO Consultant</div>
        <div><strong>Direct:</strong> +1 (645) 220-1660</div>
        <div><strong>Email:</strong> shiv.f@innovatemarketers.com</div>
        <div><strong>Date:</strong> 23rd October, 2026</div>
      </div>
    </div>

    <!-- Customer -->
    <div class="sig-block" style="margin-top: 25px;">
      <div style="color: #0284c7; font-weight: 700; font-size: 12.5px;">https://blueoasisglobal.com/</div>
      <strong style="font-size: 13.5px; color: #0b1e3b;">Dayna Hale</strong>
      <div style="font-size: 11.5px; color: #64748b; margin-bottom: 8px;">Founder & Executive Director • Blue Oasis Life Programs / Goldfields Global Canada</div>

      <!-- Plan Selection Checkboxes -->
      <div class="plan-select-box">
        <strong style="color: #0b1e3b; text-transform: uppercase; font-size: 10.5px; letter-spacing: 0.5px;">Customer Selected Plan Tier (Check One):</strong>
        <div style="margin-top: 8px; display: flex; gap: 24px; font-size: 11.5px;">
          <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
            <span style="display: inline-block; width: 15px; height: 15px; border: 1.5px solid #000; border-radius: 3px;"></span>
            <strong>Standard Plan: $799 CAD / month</strong> (Month-to-Month)
          </label>
          <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
            <span style="display: inline-block; width: 15px; height: 15px; border: 1.5px solid #000; border-radius: 3px;"></span>
            <strong>Professional Plan: $1,299 CAD / month</strong> (Month-to-Month)
          </label>
        </div>
      </div>

      <div class="sig-row" style="margin-top: 20px;">
        <span class="label">By:</span>
        <span class="underline"></span>
      </div>
      <div class="sig-row">
        <span class="label">Title:</span>
        <span class="underline"></span>
      </div>
      <div class="sig-row">
        <span class="label">Date:</span>
        <span class="underline"></span>
      </div>
    </div>
  </div>

  <!-- Footer Banner -->
  <div class="footer-banner">
    <svg class="footer-svg" viewBox="0 0 816 95" preserveAspectRatio="none">
      <path d="M0,45 C250,5 550,75 816,20 L816,95 L0,95 Z" fill="#1d63ed" />
      <path d="M0,58 C260,20 560,85 816,35 L816,95 L0,95 Z" fill="#0b1e3b" />
    </svg>
    <div class="footer-content">
      <strong>DISCLAIMER:</strong><br>
      This document is confidential and intended only for the recipient; unauthorized use, disclosure, or distribution is prohibited by Innovate Marketers LLC.
    </div>
  </div>
</div>


<!-- ========================================== -->
<!-- PAGE 4: Annexure 1 Side-by-Side Comparison -->
<!-- ========================================== -->
<div class="page">
  <!-- Header Banner -->
  <div class="header-banner">
    <svg class="header-svg" viewBox="0 0 816 125" preserveAspectRatio="none">
      <defs>
        <linearGradient id="headerGrad4" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0b1e3b"/>
          <stop offset="100%" stop-color="#112952"/>
        </linearGradient>
      </defs>
      <path d="M0,0 L816,0 L816,95 C620,135 420,70 0,115 Z" fill="#1d63ed" />
      <path d="M0,0 L816,0 L816,80 C600,125 380,55 0,98 Z" fill="url(#headerGrad4)" />
    </svg>
    <div class="header-content">
      <div class="header-logo">
        <img src="data:image/png;base64,{logo_b64}" alt="Innovate Marketers">
      </div>
      <div class="header-contact">
        <div class="header-contact-item">
          <span>+1 (645) 220-1660</span>
          <svg viewBox="0 0 24 24"><path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.57a1 1 0 01-.25 1.02l-2.2 2.2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>shiv.f@innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>www.innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>30 N Gould St Ste R Sheridan, WY 82801 USA</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
        </div>
      </div>
    </div>
  </div>

  <!-- Content -->
  <div class="content" style="padding: 6px 42px;">
    <div class="annexure-title">Annexure 1: Comparative Breakdown of SEO Services & Activities:</div>

    <table class="compare-table">
      <thead>
        <tr>
          <th style="width: 50%; text-align: left; background: #0b1e3b; color: #ffffff;">DELIVERABLE / SCOPE OF ACTIVITY</th>
          <th style="width: 25%; text-align: center; background: #ffeb3b; color: #000000; border-left: 1px solid #000000;">
            STANDARD PLAN<br><span style="font-size: 10px; font-weight: 800;">$799 CAD / mo</span>
          </th>
          <th style="width: 25%; text-align: center; background: #0f172a; color: #ffffff; border-left: 1px solid #000000;">
            PROFESSIONAL PLAN<br><span style="font-size: 10px; font-weight: 800; color: #38bdf8;">$1,299 CAD / mo</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr class="cat-header">
          <td colspan="3">1. CORE SEARCH & AUTHORITY DELIVERABLES</td>
        </tr>
        <tr>
          <td class="col-act"><strong>Target Commercial Search Phrases</strong></td>
          <td class="col-std"><strong>40 Phrases</strong></td>
          <td class="col-pro"><strong>60 Phrases</strong> (Priority & Expansion)</td>
        </tr>
        <tr>
          <td class="col-act"><strong>Monthly Verified Backlinks (DA 50+ Assets)</strong></td>
          <td class="col-std"><strong>150 Links / mo</strong></td>
          <td class="col-pro"><strong>250 Links / mo</strong></td>
        </tr>
        <tr>
          <td class="col-act"><strong>Google Business Profile (GMB / Maps)</strong></td>
          <td class="col-std">Included (Regional Optimization)</td>
          <td class="col-pro">Included (Multi-Region Reach)</td>
        </tr>
        <tr>
          <td class="col-act"><strong>Guest Posts on High DA Publication Sites</strong></td>
          <td class="col-std"><strong>2 Posts / mo</strong></td>
          <td class="col-pro"><strong>4 Posts / mo</strong></td>
        </tr>
        <tr>
          <td class="col-act">Paid Press Release Syndication</td>
          <td class="col-std cross">× (Optional Add-on)</td>
          <td class="col-pro check">✓ (1 Included PR Campaign)</td>
        </tr>
        <tr>
          <td class="col-act">Geo Tagging & Regional Citation Targeting</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓ (Multi-Hub Florida/Colorado)</td>
        </tr>

        <tr class="cat-header">
          <td colspan="3">2. WEBSITE REVIEW AND ANALYSIS (INITIAL)</td>
        </tr>
        <tr>
          <td class="col-act">Before Optimization Technical Website Audit</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Direct Competitor Benchmark Analysis</td>
          <td class="col-std">2 Competitors</td>
          <td class="col-pro"><strong>4 Competitors (Full Conquest)</strong></td>
        </tr>
        <tr>
          <td class="col-act">Keyword Research & Affluent Buyer Intent Mapping</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Keywords Initial Ranking Baseline Tracker</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Google Penalty & Algorithmic De-indexing Check</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Duplicate Content & Canonical Audit</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Backlink Quality & Toxic Profile Clean-Up</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>

        <tr class="cat-header">
          <td colspan="3">3. ON-SITE OPTIMIZATION ACTIVITIES</td>
        </tr>
        <tr>
          <td class="col-act">Title Tag Optimization (Click-Engineered)</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">META Description Tags Optimization</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Website Canonical Check (301 Loop Fix across 4 Domains)</td>
          <td class="col-std check">✓ (Full 301 Blueprint)</td>
          <td class="col-pro check">✓ (Full 301 Blueprint)</td>
        </tr>
        <tr>
          <td class="col-act">Heading Tags Optimization (H1-H5 Hierarchy Restructuring)</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Image Alt Tags Optimization & Mobile Compression</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">On-Page Content Optimization for Executive Intent</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">SEO Friendly URL Architecture & Silos</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">404 Error Page Implementation & Redirect Mapping</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Broken Links & Crawl Error Rectification</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Mobile Speed Check & Responsive Viewport Verification</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Robots.txt Creation & Google Indexed Pages Check</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Google XML Sitemap Creation & Submission</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Footer Banner -->
  <div class="footer-banner">
    <svg class="footer-svg" viewBox="0 0 816 95" preserveAspectRatio="none">
      <path d="M0,45 C250,5 550,75 816,20 L816,95 L0,95 Z" fill="#1d63ed" />
      <path d="M0,58 C260,20 560,85 816,35 L816,95 L0,95 Z" fill="#0b1e3b" />
    </svg>
    <div class="footer-content">
      <strong>DISCLAIMER:</strong><br>
      This document is confidential and intended only for the recipient; unauthorized use, disclosure, or distribution is prohibited by Innovate Marketers LLC.
    </div>
  </div>
</div>


<!-- ========================================== -->
<!-- PAGE 5: Annexure 1 (Part 2) & Add-Ons      -->
<!-- ========================================== -->
<div class="page">
  <!-- Header Banner -->
  <div class="header-banner">
    <svg class="header-svg" viewBox="0 0 816 125" preserveAspectRatio="none">
      <defs>
        <linearGradient id="headerGrad5" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0b1e3b"/>
          <stop offset="100%" stop-color="#112952"/>
        </linearGradient>
      </defs>
      <path d="M0,0 L816,0 L816,95 C620,135 420,70 0,115 Z" fill="#1d63ed" />
      <path d="M0,0 L816,0 L816,80 C600,125 380,55 0,98 Z" fill="url(#headerGrad5)" />
    </svg>
    <div class="header-content">
      <div class="header-logo">
        <img src="data:image/png;base64,{logo_b64}" alt="Innovate Marketers">
      </div>
      <div class="header-contact">
        <div class="header-contact-item">
          <span>+1 (645) 220-1660</span>
          <svg viewBox="0 0 24 24"><path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.57a1 1 0 01-.25 1.02l-2.2 2.2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>shiv.f@innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>www.innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>30 N Gould St Ste R Sheridan, WY 82801 USA</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
        </div>
      </div>
    </div>
  </div>

  <!-- Content -->
  <div class="content" style="padding: 6px 42px;">
    <div class="annexure-title">Annexure 1 (Continued): Off-Page, Social, AI Infrastructure & Terms:</div>

    <table class="compare-table">
      <thead>
        <tr>
          <th style="width: 50%; text-align: left; background: #0b1e3b; color: #ffffff;">DELIVERABLE / SCOPE OF ACTIVITY</th>
          <th style="width: 25%; text-align: center; background: #ffeb3b; color: #000000; border-left: 1px solid #000000;">
            STANDARD PLAN<br><span style="font-size: 10px; font-weight: 800;">$799 CAD / mo</span>
          </th>
          <th style="width: 25%; text-align: center; background: #0f172a; color: #ffffff; border-left: 1px solid #000000;">
            PROFESSIONAL PLAN<br><span style="font-size: 10px; font-weight: 800; color: #38bdf8;">$1,299 CAD / mo</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr class="cat-header">
          <td colspan="3">4. OFF PAGE CONTENT & AUTHORITY SYNDICATION</td>
        </tr>
        <tr>
          <td class="col-act">Article Writing & Posting (Monthly)</td>
          <td class="col-std">2 Articles</td>
          <td class="col-pro"><strong>4 Articles</strong></td>
        </tr>
        <tr>
          <td class="col-act">Blog Writing & Posting (Monthly)</td>
          <td class="col-std">2 Blogs</td>
          <td class="col-pro"><strong>4 Blogs</strong></td>
        </tr>
        <tr>
          <td class="col-act">Article & Blog Social Bookmarking</td>
          <td class="col-std">20 Bookmarks</td>
          <td class="col-pro"><strong>40 Bookmarks</strong></td>
        </tr>
        <tr>
          <td class="col-act">Classified Ad Submissions</td>
          <td class="col-std">20 Submissions</td>
          <td class="col-pro"><strong>30 Submissions</strong></td>
        </tr>
        <tr>
          <td class="col-act">Business Directory Citations & Listings</td>
          <td class="col-std">6 Listings</td>
          <td class="col-pro"><strong>10 Listings</strong></td>
        </tr>
        <tr>
          <td class="col-act">High-DA Profile Creation & Entity Anchors</td>
          <td class="col-std">10 Profiles</td>
          <td class="col-pro"><strong>20 Profiles</strong></td>
        </tr>
        <tr>
          <td class="col-act">Quora Q&A Expert Authority Answers</td>
          <td class="col-std">2 Answers</td>
          <td class="col-pro"><strong>4 Answers</strong></td>
        </tr>
        <tr>
          <td class="col-act">Image Sharing & PPT/PDF Submissions</td>
          <td class="col-std">5 Images / 2 Docs</td>
          <td class="col-pro"><strong>10 Images / 4 Docs</strong></td>
        </tr>
        <tr>
          <td class="col-act">Micro Blogging Submissions</td>
          <td class="col-std">10 Submissions</td>
          <td class="col-pro"><strong>20 Submissions</strong></td>
        </tr>

        <tr class="cat-header">
          <td colspan="3">5. SOCIAL MEDIA OPTIMIZATION (SMO)</td>
        </tr>
        <tr>
          <td class="col-act">Dedicated Social Media Channels Managed</td>
          <td class="col-std"><strong>2 Channels</strong> (FB, Instagram)</td>
          <td class="col-pro"><strong>4 Channels</strong> (FB, IG, Pinterest, YouTube)</td>
        </tr>
        <tr>
          <td class="col-act">Total Monthly Branded Social Posts</td>
          <td class="col-std"><strong>8 Posts / month</strong></td>
          <td class="col-pro"><strong>16 Posts / month</strong></td>
        </tr>
        <tr>
          <td class="col-act">Social Profiles Creation & Bio Optimization</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Interactive Branded Hashtag Research</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>

        <tr class="cat-header">
          <td colspan="3">6. AI SEARCH OPTIMIZATION (AEO) & TECHNICAL TRACKING</td>
        </tr>
        <tr>
          <td class="col-act"><strong>AI Recommendation Audit (ChatGPT & Google AI)</strong></td>
          <td class="col-std"><strong>4 Priority Pages</strong></td>
          <td class="col-pro"><strong>8 Comprehensive Pages</strong></td>
        </tr>
        <tr>
          <td class="col-act">Schema.org JSON-LD Structured Data Setup</td>
          <td class="col-std check">✓ (TouristTrip / LocalBusiness)</td>
          <td class="col-pro check">✓ (Advanced Entity Graph)</td>
        </tr>
        <tr>
          <td class="col-act">Google Analytics 4 (GA4) & Search Console Setup</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>

        <tr class="cat-header">
          <td colspan="3">7. COLLABORATION, TERMS & SUPPORT</td>
        </tr>
        <tr>
          <td class="col-act">In-House Developer Directives & Blueprints (Dayna Credit)</td>
          <td class="col-std check">✓</td>
          <td class="col-pro check">✓</td>
        </tr>
        <tr>
          <td class="col-act">Executive KPI & Ranking Reports</td>
          <td class="col-std">Monthly Executive Report</td>
          <td class="col-pro"><strong>Bi-Weekly Live Strategy & Report</strong></td>
        </tr>
        <tr>
          <td class="col-act">Dedicated Senior Consultant (+1 645-220-1660)</td>
          <td class="col-std check">✓ (Shiv)</td>
          <td class="col-pro check">✓ (Shiv + Tech Lead)</td>
        </tr>
        <tr>
          <td class="col-act"><strong>Contract Commitment & Guarantee</strong></td>
          <td class="col-std" style="font-weight: 700; color: #0284c7;">NO CONTRACT (Cancel Anytime)</td>
          <td class="col-pro" style="font-weight: 700; color: #0284c7;">NO CONTRACT (Cancel Anytime)</td>
        </tr>
      </tbody>
    </table>

    <div class="addon-summary-grid">
      <div class="addon-box-green">
        <strong>Included Technical Add-Ons (Both Plans):</strong><br>
        XML & HTML Sitemaps • Keyword Mapping • Initial Backlink Cleanup • Silo Linking • OpenGraph Meta • Mobile Clickable Directives • Favicon/Icons Setup • User Experience & Bounce Rate Audits.
      </div>
      <div class="partnership-note-card">
        <strong>In-House Developer Credit:</strong><br>
        Because Dayna maintains an in-house web developer, both rates reflect direct partner discounts (Standard: $799 CAD vs list $1,380 CAD; Professional: $1,299 CAD vs list $2,200 CAD) with 100% asset ownership.
      </div>
    </div>
  </div>

  <!-- Footer Banner -->
  <div class="footer-banner">
    <svg class="footer-svg" viewBox="0 0 816 95" preserveAspectRatio="none">
      <path d="M0,45 C250,5 550,75 816,20 L816,95 L0,95 Z" fill="#1d63ed" />
      <path d="M0,58 C260,20 560,85 816,35 L816,95 L0,95 Z" fill="#0b1e3b" />
    </svg>
    <div class="footer-content">
      <strong>DISCLAIMER:</strong><br>
      This document is confidential and intended only for the recipient; unauthorized use, disclosure, or distribution is prohibited by Innovate Marketers LLC.
    </div>
  </div>
</div>


<!-- ========================================== -->
<!-- PAGE 6: Annexure 2 Key Strategic Points    -->
<!-- ========================================== -->
<div class="page">
  <!-- Header Banner -->
  <div class="header-banner">
    <svg class="header-svg" viewBox="0 0 816 125" preserveAspectRatio="none">
      <defs>
        <linearGradient id="headerGrad6" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0b1e3b"/>
          <stop offset="100%" stop-color="#112952"/>
        </linearGradient>
      </defs>
      <path d="M0,0 L816,0 L816,95 C620,135 420,70 0,115 Z" fill="#1d63ed" />
      <path d="M0,0 L816,0 L816,80 C600,125 380,55 0,98 Z" fill="url(#headerGrad6)" />
    </svg>
    <div class="header-content">
      <div class="header-logo">
        <img src="data:image/png;base64,{logo_b64}" alt="Innovate Marketers">
      </div>
      <div class="header-contact">
        <div class="header-contact-item">
          <span>+1 (645) 220-1660</span>
          <svg viewBox="0 0 24 24"><path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.57a1 1 0 01-.25 1.02l-2.2 2.2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>shiv.f@innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>www.innovatemarketers.com</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        </div>
        <div class="header-contact-item">
          <span>30 N Gould St Ste R Sheridan, WY 82801 USA</span>
          <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
        </div>
      </div>
    </div>
  </div>

  <!-- Content -->
  <div class="content" style="padding: 10px 42px;">
    <div class="annexure-title" style="font-size: 13.5px; margin-bottom: 3px;">Annexure 2: Key Strategic Objectives & Executive Takeaways</div>
    <div style="font-size: 11px; color: #475569; font-style: italic; margin-bottom: 12px; padding-bottom: 4px; border-bottom: 2px solid #0284c7;">
      Essential commercial priorities extracted from your strategic proposal to guide implementation.
    </div>

    <div style="display: flex; flex-direction: column; gap: 8.5px;">
      <!-- Point 1 -->
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 3.5px solid #0284c7; border-radius: 6px; padding: 7px 11px;">
        <div style="font-size: 11px; font-weight: 800; color: #0b2545; margin-bottom: 2px;">
          1. High-Net-Worth Buyer Targeting (Quality Over Mass Traffic)
        </div>
        <div style="font-size: 10px; color: #334155; line-height: 1.4;">
          Because Blue Oasis delivers exclusive retreats ($10k VIP tier & bespoke executive cohorts), we do not waste budget on mass traffic. Our campaign targets the <strong>50 to 100 affluent decision-makers</strong> actively searching for restorative wellness retreats each month.
        </div>
      </div>

      <!-- Point 2 -->
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 3.5px solid #059669; border-radius: 6px; padding: 7px 11px;">
        <div style="font-size: 11px; font-weight: 800; color: #0b2545; margin-bottom: 2px;">
          2. Immediate Resolution of the 4x Canonical Duplicate Loop
        </div>
        <div style="font-size: 10px; color: #334155; line-height: 1.4;">
          Currently, <code>http://</code>, <code>https://</code>, <code>www.</code>, and non-www load as 4 separate websites, splitting your 382 backlinks into four and causing Google to suppress your rankings for duplicate content. We deploy a permanent 301 canonical redirect blueprint to consolidate 100% of domain power into your primary secure URL.
        </div>
      </div>

      <!-- Point 3 -->
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 3.5px solid #7c3aed; border-radius: 6px; padding: 7px 11px;">
        <div style="font-size: 11px; font-weight: 800; color: #0b2545; margin-bottom: 2px;">
          3. AI Answer Engine Optimization (ChatGPT, Siri & Google AI Overviews)
        </div>
        <div style="font-size: 10px; color: #334155; line-height: 1.4;">
          Affluent executives increasingly use AI to research private wellness travel. We inject rich Schema.org (<code>TouristTrip</code>, <code>LocalBusiness</code>, <code>WellnessProgram</code>) machine-readable structured code so ChatGPT and Google AI directly cite and recommend Blue Oasis by name.
        </div>
      </div>

      <!-- Point 4 -->
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 3.5px solid #d97706; border-radius: 6px; padding: 7px 11px;">
        <div style="font-size: 11px; font-weight: 800; color: #0b2545; margin-bottom: 2px;">
          4. In-House Web Developer Synergy (Zero Duplicate Costs)
        </div>
        <div style="font-size: 10px; color: #334155; line-height: 1.4;">
          You retain your trusted in-house web developer for site edits, saving $581 CAD/month. Innovate Marketers delivers clear code directives and technical blueprints directly to your developer, while our agency executes 100% of the external off-page backlinks, publication guest articles, and social media syndication.
        </div>
      </div>

      <!-- Point 5 -->
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 3.5px solid #0284c7; border-radius: 6px; padding: 7px 11px;">
        <div style="font-size: 11px; font-weight: 800; color: #0b2545; margin-bottom: 2px;">
          5. 100% Client Pre-Approval & Brand Protection Guarantee
        </div>
        <div style="font-size: 10px; color: #334155; line-height: 1.4;">
          Your luxury brand identity is fully protected. Zero articles, blogs, directory listings, or social media updates will ever be published without Dayna's prior review and approval. You maintain complete editorial and tone control at all times.
        </div>
      </div>

      <!-- Point 6 -->
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 3.5px solid #e11d48; border-radius: 6px; padding: 7px 11px;">
        <div style="font-size: 11px; font-weight: 800; color: #0b2545; margin-bottom: 2px;">
          6. Zero Contract Lock-In & Total Asset Ownership
        </div>
        <div style="font-size: 10px; color: #334155; line-height: 1.4;">
          Our partnership is built entirely on month-to-month flexibility. You are never locked into an inflexible term; if you ever wish to cancel, you can do so anytime without penalties. Furthermore, Dayna permanently retains 100% ownership of all created content, backlinks, schemas, and analytics setups.
        </div>
      </div>
    </div>
  </div>

  <!-- Footer Banner -->
  <div class="footer-banner">
    <svg class="footer-svg" viewBox="0 0 816 95" preserveAspectRatio="none">
      <path d="M0,45 C250,5 550,75 816,20 L816,95 L0,95 Z" fill="#1d63ed" />
      <path d="M0,58 C260,20 560,85 816,35 L816,95 L0,95 Z" fill="#0b1e3b" />
    </svg>
    <div class="footer-content">
      <strong>DISCLAIMER:</strong><br>
      This document is confidential and intended only for the recipient; unauthorized use, disclosure, or distribution is prohibited by Innovate Marketers LLC.
    </div>
  </div>
</div>

</body>
</html>
"""
    return html

def compile_agreement_pdf(out_pdf_path: str):
    html = generate_agreement_html()
    temp_html_path = WORKSPACE_ROOT / "scratch" / "temp_dayna_agreement.html"
    os.makedirs(temp_html_path.parent, exist_ok=True)
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(temp_html_path.as_uri(), wait_until="networkidle")
        page.pdf(
            path=out_pdf_path,
            format="Letter",
            print_background=True,
            margin={"top": "0in", "right": "0in", "bottom": "0in", "left": "0in"},
            prefer_css_page_size=True,
        )
        browser.close()
    
    print(f"[SUCCESS] Agreement PDF generated at: {out_pdf_path}")

if __name__ == "__main__":
    out_dir = WORKSPACE_ROOT / "clients" / "blueoasisglobal"
    os.makedirs(out_dir, exist_ok=True)
    out_pdf = out_dir / "Dayna_Hale_SEO_Services_Agreement.pdf"
    compile_agreement_pdf(str(out_pdf))
