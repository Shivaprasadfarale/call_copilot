import os
import re
import time
import json
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from PIL import Image
import boto3
import yaml

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(WORKSPACE_DIR, "screenshots")
CONFIG_PATH = os.path.join(WORKSPACE_DIR, "config.yaml")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def extract_metrics_from_image(image_path: str) -> Dict[str, Any]:
    """Uses Bedrock multimodal to extract the 5 core Semrush scorecard numbers from the cropped screenshot."""
    cfg = load_config()
    client = boto3.client(
        "bedrock-runtime",
        region_name=cfg.get("aws_region", "us-east-1"),
        aws_access_key_id=cfg.get("aws_access_key_id"),
        aws_secret_access_key=cfg.get("aws_secret_access_key")
    )
    model_id = cfg.get("bedrock_model", "moonshotai.kimi-k2.5")

    with open(image_path, "rb") as f:
        img_bytes = f.read()

    prompt = """Analyze this Semrush SEO Overview scorecard image.
Extract the detailed SEO performance indicators shown:
1. authority_score (number or string, e.g. 2 or 0)
2. organic_traffic (monthly organic search visits, e.g. 0, 15, 120, 2.5K)
3. keywords (organic search keywords indexed, e.g. 2, 45, 1.2K)
4. referring_domains (number of referring domains, e.g. 21)
5. backlinks (total backlinks count, e.g. 21, 550, 1K, 2.2K)
6. traffic_share_us (US traffic share percentage if shown, e.g. "5%", "11%", "43%", "66%")
7. ai_visibility (AI visibility score or mentions across ChatGPT, Gemini, AI Overviews, e.g. "0" or "14 with 1 mention")
8. traffic_trend (trend note, e.g. "Flatline at 0" or "Declining -8.8%" or "Up +25%")
9. branded_traffic_pct (estimate based on keywords/traffic, e.g. "100% branded / 0% non-branded discovery")

Output ONLY valid JSON:
{
  "authority_score": "2",
  "organic_traffic": "0",
  "keywords": "2",
  "referring_domains": "21",
  "backlinks": "21",
  "traffic_share_us": "5%",
  "ai_visibility": "0",
  "traffic_trend": "Flatline at 0",
  "branded_traffic_pct": "100%",
  "notes": "Lacks organic traffic, no non-branded discovery"
}"""

    try:
        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": {"format": "png", "source": {"bytes": img_bytes}}},
                        {"text": prompt}
                    ]
                }
            ]
        )
        raw_text = response['output']['message']['content'][0]['text'].strip()
        clean_json = re.sub(r'^```(json)?\s*', '', raw_text, flags=re.MULTILINE)
        clean_json = re.sub(r'\s*```$', '', clean_json, flags=re.MULTILINE).strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Warning: Failed to extract metrics from screenshot via Bedrock: {e}")
        return {
            "authority_score": "0",
            "organic_traffic": "0",
            "keywords": "0",
            "referring_domains": "0",
            "backlinks": "0",
            "notes": ""
        }

def capture_semrush_overview(domain: str, client_slug: str, headless: bool = False) -> Dict[str, Any]:
    """Navigates to Semrush Domain Overview in headed/visible mode.
    Handles the 10-search limit modal with a console pause.
    Takes a clean, white-label crop of the SEO scorecards (0 sidebar, 0 address bar).
    Saves to screenshots/{client_slug}_seo.png.
    """
    output_path = os.path.join(SCREENSHOTS_DIR, f"{client_slug}_seo.png")
    
    # If the user already provided or saved this screenshot, we can reuse it
    if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
        print(f"[Semrush] Found existing clean screenshot at: {output_path}")
        metrics = extract_metrics_from_image(output_path)
        metrics["screenshot_path"] = output_path
        return metrics

    clean_domain = re.sub(r'^https?://', '', domain).strip('/').split('/')[0]
    clean_domain = re.sub(r'^www\.', '', clean_domain)
    
    target_url = f"https://www.semrush.com/analytics/overview/?q={clean_domain}&searchType=domain"
    print(f"\n[Semrush] Opening browser for domain: {clean_domain}...")
    print(f"[Semrush] Target URL: {target_url}")

    user_data_dir = os.path.join(WORKSPACE_DIR, ".semrush_browser_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    with sync_playwright() as p:
        # Launch persistent context so logins/cookies persist across runs
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            viewport={"width": 1440, "height": 900},
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        page = context.new_page()
        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

        # Check for free account search limit popup or login prompt
        print("[Semrush] Checking for login or daily 10-search limit dialog...")
        time.sleep(4)

        def check_limit_or_login():
            content = page.content().lower()
            limit_phrases = [
                "daily limit", 
                "reached your limit", 
                "you've reached your free searches", 
                "create a free account", 
                "log in to semrush", 
                "upgrade to pro"
            ]
            for phrase in limit_phrases:
                if phrase in content:
                    return phrase
            return None

        hit_limit = check_limit_or_login()
        if hit_limit:
            if not headless:
                print(f"\n{'='*70}")
                print(f"⚠️  SEMRUSH NOTICE: Triggered condition: '{hit_limit}'")
                print("Please log in or switch to your next free Gmail account in the opened browser window.")
                print("Once the Domain Overview report for the client is visible on screen, return here.")
                input("Press [ENTER] to continue capture once you are logged in and the report is visible... ")
                print(f"{'='*70}\n")
                time.sleep(3)
            else:
                print(f"[Semrush] Detected '{hit_limit}' in headless mode, continuing...")

        # Ensure page is scrolled slightly or scorecards container is visible
        print("[Semrush] Locating SEO scorecard cards...")
        
        # Look for the scorecard container
        cards_locator = None
        selectors_to_try = [
            'div[data-test="overview-scorecard"]',
            'div[data-ui-name="Box"]:has(div:has-text("Authority Score"))',
            'div:has-text("Authority Score"):has-text("Organic Search Traffic")',
            'section:has(div:has-text("Authority Score"))',
            'main div[class*="overview"]'
        ]

        # Wait up to 10 seconds for main content
        for selector in selectors_to_try:
            try:
                loc = page.locator(selector).first
                if loc.is_visible(timeout=2000):
                    cards_locator = loc
                    break
            except Exception:
                continue

        # Hide Semrush left sidebar and floating clutter before capturing
        try:
            page.evaluate("""() => {
                const sidebar = document.querySelector('aside, nav[class*="sidebar"], [data-test="sidebar"]');
                if (sidebar) sidebar.style.display = 'none';
                const header = document.querySelector('header, [data-test="navigation-header"]');
                if (header) header.style.display = 'none';
            }""")
        except Exception:
            pass

        time.sleep(2)

        # Take clean cropped screenshot
        captured = False
        if cards_locator and cards_locator.is_visible():
            try:
                cards_locator.screenshot(path=output_path)
                print(f"[Semrush] Card element cropped cleanly to: {output_path}")
                captured = True
            except Exception as e:
                print(f"[Semrush] Direct card screenshot failed: {e}")

        if not captured:
            # Fallback: take full viewport screenshot and crop out any top/left chrome
            temp_path = os.path.join(SCREENSHOTS_DIR, f"{client_slug}_temp.png")
            page.screenshot(path=temp_path)
            
            # Crop via Pillow to remove left sidebar and top navbar:
            im = Image.open(temp_path)
            w, h = im.size
            # Crop margins: left 80px (if sidebar existed), top 120px, right width, bottom 550px
            crop_box = (min(100, int(w*0.05)), min(150, int(h*0.15)), w - min(40, int(w*0.03)), min(h, 600))
            cropped = im.crop(crop_box)
            cropped.save(output_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"[Semrush] Cropped viewport saved to: {output_path}")

        context.close()

    # Extract metrics using Bedrock vision
    metrics = extract_metrics_from_image(output_path)
    metrics["screenshot_path"] = output_path
    print(f"[Semrush] Extracted Metrics: AS={metrics.get('authority_score')}, Traffic={metrics.get('organic_traffic')}, KWs={metrics.get('keywords')}, Backlinks={metrics.get('backlinks')}")
    return metrics

if __name__ == "__main__":
    test_domain = "willowcreekminihighlands.com"
    metrics = capture_semrush_overview(test_domain, "willowcreekminihighlands")
    print(json.dumps(metrics, indent=2))
