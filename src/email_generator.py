"""
Dual-Track Email Copy Generator
Generates both proven styles of outreach:
- Track A: Technical Diagnostic / Open Loop (Scorecard inline, DA/backlink numbers, 2 findings revealed, 3rd held).
- Track B: Executive / High-Ticket Pitch (3 hours spent on 22-page PDF, quotes exact packages & pricing, asks the logical visibility question).
"""

from typing import Dict, Any, List


def format_anti_autolink(text: str) -> str:
    """Ensures spaces around all dots and @ symbols to prevent spam filters from autolinking."""
    # Remove protocols
    text = text.replace("https://", "").replace("http://", "").replace("mailto:", "").rstrip("/")
    # Space out dots in domains/emails
    text = text.replace(".", " . ")
    # Space out @
    text = text.replace("@", " @ ")
    # Collapse multiple spaces
    while "  " in text:
        text = text.replace("  ", " ")
    return text


def clean_da(val: str) -> str:
    s = str(val).strip()
    if not s or s.lower() == "under review":
        return "Under Review"
    return s if "/ 100" in s else f"{s} / 100"

def clean_num(val: str, label: str) -> str:
    import re
    s = str(val).strip()
    return re.sub(rf"\s*{label}s?\b", "", s, flags=re.I).strip()

def generate_track_a_diagnostic(
    client_name: str,
    colleague_name: str,
    quoted_headers: str,
    quoted_body: str,
    website: str,
    diagnostics: Dict[str, Any],
    real_competitors: List[str],
    open_loop_question: str,
    service_type: str = "services"
) -> str:
    """Generates Track A: Technical Diagnostic with Open Loop format."""
    clean_site = format_anti_autolink(website)
    comp_str = " and ".join(real_competitors[:2]) if real_competitors else "top competitors"

    da_str = clean_da(diagnostics.get('authority_score', 'Under Review'))
    bl_val = clean_num(diagnostics.get('backlinks', '0'), 'backlink')
    rd_val = clean_num(diagnostics.get('ref_domains', '0'), 'domain')
    kw_val = clean_num(diagnostics.get('keywords_indexed', '0'), 'term')
    kw_val = clean_num(kw_val, 'keyword')

    lines = [
        f"Hi {client_name},",
        "",
        f"My colleague {colleague_name} forwarded me your reply asking us to send over the website report and errors we spotted on {clean_site}:",
        "",
        "--------------------------------------------------",
        quoted_headers.strip(),
        "",
        quoted_body.strip(),
        "--------------------------------------------------",
        "",
        f"I pulled your live Google search and domain diagnostic data today. Here is the high-level snapshot:",
        f"• Domain Authority Score: {da_str}",
        f"• Monthly Organic Traffic: {diagnostics.get('organic_traffic', '0 visits/mo')}",
        f"• Total Backlinks & Referring Domains: {bl_val} links across {rd_val} domains",
        f"• Organic Keywords Indexed: {kw_val} terms",
        f"• AI Search Visibility: {diagnostics.get('ai_mentions', '0 Mentions')}",
        "",
        "[Scorecard Screenshot Attached Inline]",
        "",
        f"You have {bl_val} backlinks and {rd_val} referring domains — that is a genuinely strong foundation.",
        f"However, despite that authority, Google is only sending you {diagnostics.get('organic_traffic', 'minimal traffic')}. Meanwhile, {comp_str} in your market are sitting right at the top of Google Page 1, capturing high-ticket {service_type} contracts every month.",
        "",
        f"We identified 3 technical issues blocking your website from Google's first page:",
        "",
        f"1. Commercial Search Indexation Gap: Google is currently indexing your domain for generic phrases instead of the high-intent commercial terms paying clients actually type.",
        f"2. Backlink Authority Leak: Your link equity is not being channeled into crawlable landing pages due to missing internal silos and structured schema.",
        f"3. [HELD] The third finding relates directly to your primary operational focus.",
        "",
        f"{open_loop_question}",
        "",
        "Once I know that, I can confirm whether this third technical issue applies to your setup and send you the complete fix list.",
        "",
        "I also put together a complete 22-page visual Google Search Audit mapping your exact positioning against competitors screenshot-by-screenshot across your market."
    ]
    return "\n".join(lines)


def generate_track_b_executive(
    client_name: str,
    colleague_name: str,
    quoted_headers: str,
    quoted_body: str,
    company_name: str,
    packages: List[Dict[str, str]],
    competitors: List[str],
    delivery_scope: str = "nationwide across the United States",
    service_label: str = "mindset training or performance coaching"
) -> str:
    """Generates Track B: Executive / High-Ticket Pitch focusing on exact packages, 3 hours spent, and logical visibility argument."""
    comp_str = " and ".join(competitors[:2]) if competitors else "top competitors"
    
    # Format packages string
    pkg_str = ""
    if packages:
        pkg_parts = [f"{p['name']} ({p['price']})" for p in packages[:3]]
        pkg_str = ", ".join(pkg_parts)

    lines = [
        f"Hi {client_name},",
        "",
        f"My colleague {colleague_name} forwarded me your reply asking us to send over the website report and errors we spotted on your platforms:",
        "",
        "--------------------------------------------------",
        quoted_headers.strip(),
        "",
        quoted_body.strip(),
        "--------------------------------------------------",
        "",
        f"First off, your personal story, your background, and the platform you've built across {company_name} look genuinely powerful.",
        "",
        f"I spent over 3 hours specifically for you preparing a complete 22-page visual Google Search Audit (attached to this email), and I want to share why this report is so critical for your business right now.",
        "",
        "Think about it from a simple, logical perspective:",
        "",
        f"Because your services are delivered {delivery_scope}, your market isn't limited to one town — your reach is nationwide.",
        f"When an executive, business leader, or prospective client is actively looking for high-level {service_label}, they have two options: either they know someone personally, or they search Google.",
        "",
        f"If someone is actively searching for your exact expertise, but they search Google and your platforms literally do not appear anywhere on Page 1 — while competitors like {comp_str} take up every top spot — what is the point of having great, structured programs {f'like your {pkg_str} ' if pkg_str else ''}if the people ready to hire you can't even find you?",
        "",
        "In the attached 22-page PDF, I documented this exact reality across commercial searches, showing you screenshot-by-screenshot:",
        "• Where your platforms are completely absent from Google Page 1.",
        "• Which competitors are currently capturing all the organic inquiries, speaking contracts, and client enrollments.",
        "• The exact structural errors under the hood preventing Google from connecting your link foundation to your service pages.",
        "",
        "Please make sure to zoom in and review the attached PDF — whether on your phone or on your computer — so you can see the actual live Google results for yourself and understand why your site is suppressed.",
        "",
        "What day and time works best for you this week for a quick 10-minute Google Meet or call so I can walk you through the report and show you the exact technical fixes to get your programs ranked on Page 1?"
    ]
    return "\n".join(lines)
