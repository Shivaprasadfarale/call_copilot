import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any
import boto3
import yaml

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(WORKSPACE_DIR, "config.yaml")

OFFICIAL_SIGNATURE_HTML = ""

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

def get_dynamic_days() -> str:
    """Calculate the next two business days from today."""
    today = datetime.now()
    days_found = []
    check = today
    while len(days_found) < 2:
        check += timedelta(days=1)
        if check.weekday() < 5:
            days_found.append(check.strftime('%A'))
    return f"{days_found[0]} or {days_found[1]}"

def generate_followup_body(lead_info: Dict[str, Any], fatal_flaw: str = "", is_post_report: bool = False) -> str:
    """Generates an ultra-crisp, high-converting follow-up email body
    to be injected directly into an existing conversation thread in Gmail.
    Strictly under 45 words, zero fluff, low friction.
    """
    first_name = lead_info.get("first_name") or lead_info.get("client_name", "there")
    company_name = lead_info.get("company_name", "your business")
    niche = lead_info.get("niche", "your industry")
    location = lead_info.get("location", "your area")

    dynamic_days = get_dynamic_days()

    cfg = load_config()
    model_id = cfg.get("bedrock_model", "moonshotai.kimi-k2.5")
    bedrock_client = get_bedrock_client(cfg)

    if is_post_report:
        prompt = f"""You are an elite SEO/AEO consultant at Innovate Marketers.
Write a razor-sharp follow-up email to {first_name} at {company_name}.
In this exact email thread, we already attached and delivered the complete 22-page visual Google search audit comparing {company_name} against their top local competitors.

CRITICAL RULES (POST-REPORT MEETING INVITE):
1. STRICT WORD LIMIT: Under 45 words total (2 to 3 crisp sentences).
2. Polite bump: Ask if they got a chance to look through the visual report / competitor screenshots attached above.
3. Meeting invite: Offer a quick 10-minute Google Meet to share your screen and walk through the exact technical fixes to get {company_name} ranking ahead of competitors on Page 1.
4. Call to action: "What day and time work best for you this week?"
5. NO SIGNATURE: Do not include any signoff or signature block.

Output ONLY the follow-up body text inside <FOLLOWUP_TEXT></FOLLOWUP_TEXT>. Do not include signature or greeting."""
        fallback_text = f"Following up on the visual search audit I attached above for {company_name}.<br><br>Did you get a chance to look through the competitor screenshots?<br><br>I would love to walk you through the exact technical fixes to get your business ranking on Page 1. Can we do a quick 10-minute Google Meet this week? What day and time work best for you?"
    else:
        prompt = f"""You are an elite SEO/AEO consultant at Innovate Marketers.
Write a razor-sharp 48-hour follow-up email to {first_name} at {company_name}.
This email is a direct reply in the EXACT SAME email thread where we already sent the website diagnostic report and scorecard.

CRITICAL RULES (STRICT OPEN LOOP STANDARD):
1. STRICT WORD LIMIT: Under 40 words total (2 to 3 short sentences).
2. DO NOT attach images, DO NOT repeat numbers, DO NOT ask for a Zoom or phone call.
3. Polite bump: "Did you get a chance to see the scorecard above?"
4. Reference the held 3rd finding: Mention that you still have the 3rd finding on hold for {company_name} and just need their quick 1-sentence input on operations/service focus ({fatal_flaw or niche}).
5. Low-friction close: "Once you let me know, I'll send over the complete fix list."
6. NO SIGNATURE: Do not include any signature block or company footer.

Output ONLY the follow-up body text inside <FOLLOWUP_TEXT></FOLLOWUP_TEXT>. Do not include signature or greeting."""
        fallback_text = f"Did you get a chance to see the scorecard above?<br><br>I still have that third finding on hold for {company_name} &mdash; just need your quick input on whether most of your inquiries are local or broader. Once you let me know, I'll send over the complete fix list."

    try:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}]
        )
        raw_text = response['output']['message']['content'][0]['text'].strip()
        match = re.search(r'<FOLLOWUP_TEXT>([\s\S]*?)</FOLLOWUP_TEXT>', raw_text, re.IGNORECASE)
        if match and match.group(1).strip():
            msg_content = match.group(1).strip()
        else:
            msg_content = raw_text
    except Exception as e:
        print(f"Bedrock warning in follow-up generator: {e}")
        msg_content = fallback_text

    # Clean text
    msg_content = msg_content.replace('—', ' &mdash; ').replace('–', ' &mdash; ').replace('’', "'").replace('‘', "'")

    # Strip any redundant leading greeting generated by LLM so it does not duplicate
    msg_content = re.sub(r'^\s*(?:Hi|Hello|Hey|Dear)\s+[^,\n\–\—\-:]+[,!\n\–\—\-:]+\s*', '', msg_content, flags=re.IGNORECASE).strip()
    
    # Strip bare name if LLM started with e.g. "Mark —" or "Mark &mdash;"
    clean_name = re.escape(first_name)
    first_word = re.escape(first_name.split()[0])
    msg_content = re.sub(rf'^\s*(?:{clean_name}|{first_word})\s*(?:&mdash;|[\–\—\-:,!])+\s*', '', msg_content, flags=re.IGNORECASE).strip()

    # Strip any trailing signoff/signature generated by LLM
    msg_content = re.sub(r'(?:Best|Regards|Sincerely|Thanks|Cheers)[,\s]+.*$', '', msg_content, flags=re.IGNORECASE).strip()

    # Ensure paragraphs
    lines = [p.strip() for p in msg_content.split('\n') if p.strip()]
    formatted_body = "".join([f'<p style="margin: 0 0 14px 0; font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.6;">{line}</p>' for line in lines])

    email_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.6;">

<p style="margin: 0 0 14px 0; font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.6;">Hi {first_name},</p>

{formatted_body}

{OFFICIAL_SIGNATURE_HTML}

</body>
</html>"""
    return email_html
