import os
import sys
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from google_auth_oauthlib.flow import InstalledAppFlow
from src.gmail_helper import SCOPES, CREDENTIALS_FILE, TOKEN_FILE, WORKSPACE_DIR


def run():
    print("Preparing authentication...", flush=True)
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    
    # We will run the local server on an available port
    # But before blocking, we will grab the exact authorization URL so you can click it!
    flow.redirect_uri = 'http://localhost:8080/'
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline'
    )
    
    with open(os.path.join(WORKSPACE_DIR, 'auth_link.txt'), 'w') as f:
        f.write(auth_url)
        
    print("\n" + "="*70, flush=True)
    print("YOUR AUTHENTICATION LINK IS READY:", flush=True)
    print(auth_url, flush=True)
    print("="*70 + "\n", flush=True)
    
    # Force open in user's Windows default browser (Chrome)
    try:
        subprocess.Popen(['powershell', '-Command', f'Start-Process "{auth_url}"'])
    except Exception as e:
        print(f"Could not auto-open browser: {e}", flush=True)
        
    print("Listening on http://localhost:8080/ for Google's approval...", flush=True)
    
    # Run the server on port 8080 (which matches redirect_uri)
    creds = flow.run_local_server(
        port=8080,
        open_browser=False,
        success_message='Success! Call Copilot is connected. You can close this tab now.'
    )
    
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print("\nToken saved successfully! You are connected.", flush=True)
    
    # Now create the draft for Rags To Rinses!
    to = "rags2rinses419@gmail.com"
    subject = "Re: Startings"
    with open(os.path.join(WORKSPACE_DIR, 'emails', 'ragstorinses_outreach.eml'), 'rb') as f:
        # We already have the HTML and image in gmail_helper
        pass
        
    print("Creating Gmail draft for Rags To Rinses...", flush=True)
    # Import and run create draft
    from src.gmail_helper import create_gmail_draft
    with open(os.path.join(WORKSPACE_DIR, 'scratch', 'build_eml.py'), 'r', encoding='utf-8') as f:
        content = f.read()
    
    img = os.path.join(WORKSPACE_DIR, 'screenshots', 'ragstorinses_semrush.png')
    
    # Run helper directly
    import src.gmail_helper
    src.gmail_helper.create_gmail_draft(
        to_email=to,
        subject=subject,
        html_body="""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: Calibri, Arial, sans-serif; font-size: 15px; color: #222; line-height: 1.5; }
  .quote-box { border-left: 3px solid #ccc; padding-left: 12px; margin: 15px 0; color: #555; font-size: 13px; font-family: monospace; }
  .highlight { background-color: #fef08a; padding: 2px 5px; font-weight: bold; border-radius: 3px; }
  .alert-text { color: #b91c1c; font-weight: bold; }
  .sig { margin-top: 25px; color: #333; line-height: 1.3; }
</style>
</head>
<body>
<p>Hi,</p>

<p>My team got an email response from you looking for more information:</p>

<div class="quote-box">
_____________________________________<br>
<b>From:</b> RagsToRinses Premium Detailing LLC &lt;rags2rinses419 @ gmail . com&gt;<br>
<b>Date:</b> Sun, Aug 30, 2026 at 1:49 PM<br>
<b>Subject:</b> Re: Startings<br>
<b>To:</b> ellenalexander626 @ gmail . com<br><br>
<b>Yes</b><br>
_____________________________________
</div>

<p>When someone in Michigan searches Google for <b>premium mobile car detailing, ceramic coating, or paint correction</b>, your business should be one of the first names they see.</p>

<p>But getting found online isn’t just about having a great-looking website — it’s about having the right local keywords, Google presence, and domain authority working together.</p>

<p>That’s where we help.</p>

<div style="margin: 20px 0;">
  <img src="cid:semrush_screenshot" style="max-width: 600px; width: 100%; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); display: block;" alt="Semrush SEO Overview">
</div>

<p>According to our live Semrush audit, your website currently receives <span class="highlight">0 monthly organic visitors from Google search</span>, with an Authority Score of <span class="alert-text">2 / 100</span>. While you have 16 keywords indexed, none of them are currently ranking on Page 1 where active customers are searching.</p>

<p>It looks like someone tried to build initial backlinks (145 links recorded), but lacked the local SEO strategy needed to actually convert those into Google Map pack and search rankings.</p>

<p>At <b>Innovate Marketers</b>, we help auto detailing businesses improve their Google rankings, map visibility, and turn online searchers into booked detailing appointments.</p>

<p>And here’s the interesting part — <b>local competitors in your area are currently capturing the high-ticket ceramic coating and full detail inquiries that should be calling you.</b></p>

<p>We can show you exactly where those opportunities are.</p>

<p><b>Once you reply to this email, we can send over your detailed roadmap and audit report.</b> (Without your reply, there’s a chance the report may land in spam.)</p>

<div class="sig">
<p>Regards,<br>
<b>Shiv</b><br>
Innovate Marketers<br>
Direct: (645) 220-1660<br>
<a href="mailto:shivaprasad.farale@innovatemarketers.com">shivaprasad.farale@innovatemarketers.com</a></p>
</div>
</body>
</html>""",
        image_path=img
    )

if __name__ == '__main__':
    run()
