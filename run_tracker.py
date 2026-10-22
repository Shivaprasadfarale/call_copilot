import os
import sys
import json
import mimetypes
from urllib.parse import urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(WORKSPACE_DIR, 'src'))

from lead_parser import get_all_leads, get_current_local_time
from tracker_db import get_tracker_state, update_lead_status, manual_reset_today, get_daily_report
from email_tracker import get_lead_email_history


STATIC_DIR = os.path.join(WORKSPACE_DIR, 'static')
SCREENSHOTS_DIR = os.path.join(WORKSPACE_DIR, 'screenshots')

class TrackerHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_file_response(self, filepath, content_type=None):
        if not os.path.exists(filepath) or os.path.isdir(filepath):
            self.send_error(404, "File Not Found")
            return
            
        if not content_type:
            content_type, _ = mimetypes.guess_type(filepath)
            if not content_type:
                content_type = 'application/octet-stream'
                
        with open(filepath, 'rb') as f:
            content = f.read()
            
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/' or path == '/index.html':
            self.send_file_response(os.path.join(STATIC_DIR, 'index.html'), 'text/html; charset=utf-8')
            return

        if path.startswith('/static/'):
            rel_path = path[len('/static/'):].replace('/', os.sep)
            filepath = os.path.join(STATIC_DIR, rel_path)
            self.send_file_response(filepath)
            return

        if path.startswith('/screenshots/'):
            filename = os.path.basename(path)
            filepath = os.path.join(SCREENSHOTS_DIR, filename)
            self.send_file_response(filepath)
            return

        if path == '/api/leads':
            raw_leads = get_all_leads()
            state = get_tracker_state()
            leads_state = state.get('leads', {})
            
            dials_today = 0
            meetings_booked = 0
            callbacks_count = 0
            safe_to_call_count = 0
            
            merged_leads = []
            for lead in raw_leads:
                slug = lead['slug']
                l_state = leads_state.get(slug, {})
                
                called_today = l_state.get('called_today', False)
                if called_today:
                    dials_today += 1
                    
                last_outcome = l_state.get('last_outcome', '')
                if last_outcome == 'meeting_booked':
                    meetings_booked += 1
                elif last_outcome == 'spoke_followup' or l_state.get('callback_datetime'):
                    callbacks_count += 1
                    
                on_hold = lead.get('on_hold', False) or l_state.get('on_hold', False)
                callback_dt = l_state.get('callback_datetime', '') or lead.get('snooze_until', '')
                today_str = state.get('date', '')
                is_future_callback = bool(callback_dt and callback_dt > today_str)

                local_time = get_current_local_time(lead['timezone'])
                if local_time['is_safe'] and not called_today and not on_hold and not is_future_callback:
                    safe_to_call_count += 1
                    
                # Priority Score calculation:
                # Lower score = higher priority in table!
                if on_hold or is_future_callback:
                    priority = 9999  # On hold / snoozed leads pushed to very bottom
                elif called_today:
                    priority = 1000  # Pushed to the bottom
                elif local_time['is_safe']:
                    hour_dist = abs(local_time['hour'] - 13) # distance from 1pm peak
                    priority = hour_dist
                else:
                    priority = 200 # outside safe hours
                    
                email_hist = get_lead_email_history(lead.get('email', ''))

                merged = dict(lead)
                merged.update({
                    'called_today': called_today,
                    'on_hold': on_hold,
                    'is_future_callback': is_future_callback,
                    'snooze_until': l_state.get('snooze_until', '') or lead.get('snooze_until', ''),
                    'last_outcome': last_outcome,
                    'last_called_at': l_state.get('last_called_at', ''),
                    'total_calls': l_state.get('total_calls', 0),
                    'quick_notes': l_state.get('quick_notes', ''),
                    'call_history': l_state.get('call_history', []),
                    'meeting_datetime': l_state.get('meeting_datetime', ''),
                    'callback_datetime': callback_dt,
                    'local_time': local_time,
                    'priority_score': priority,
                    'email_history': email_hist
                })
                merged_leads.append(merged)


            clocks = {
                'EST': get_current_local_time('EST'),
                'CST': get_current_local_time('CST'),
                'MST': get_current_local_time('MST'),
                'PST': get_current_local_time('PST')
            }

            response_data = {
                'leads': merged_leads,
                'stats': {
                    'total_leads': len(merged_leads),
                    'dials_today': dials_today,
                    'daily_goal': state.get('daily_goal', 25),
                    'meetings_booked': meetings_booked,
                    'callbacks_count': callbacks_count,
                    'safe_to_call': safe_to_call_count
                },
                'timezone_clocks': clocks
            }
            self.send_json(response_data)
            return

        if path == '/api/daily_report':
            report = get_daily_report()
            self.send_json(report)
            return

        self.send_error(404, "Endpoint Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else '{}'
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if path == '/api/lead/log_call':
            slug = req_data.get('slug')
            outcome = req_data.get('outcome')
            note = req_data.get('note')
            meeting_time = req_data.get('meeting_datetime')
            callback_time = req_data.get('callback_datetime')
            
            if not slug:
                self.send_json({'error': 'Missing slug'}, 400)
                return
                
            lead_data = update_lead_status(
                slug=slug,
                outcome=outcome,
                note=note,
                meeting_datetime=meeting_time,
                callback_datetime=callback_time
            )
            self.send_json({'success': True, 'lead': lead_data})
            return

        if path == '/api/lead/toggle_called':
            slug = req_data.get('slug')
            called_today = req_data.get('called_today', True)
            if not slug:
                self.send_json({'error': 'Missing slug'}, 400)
                return
            lead_data = update_lead_status(slug=slug, toggle_called=called_today)
            self.send_json({'success': True, 'lead': lead_data})
            return

        if path == '/api/lead/save_note':
            slug = req_data.get('slug')
            note = req_data.get('note', '')
            if not slug:
                self.send_json({'error': 'Missing slug'}, 400)
                return
            lead_data = update_lead_status(slug=slug, note=note)
            self.send_json({'success': True, 'lead': lead_data})
            return

        if path == '/api/reset_today':
            res = manual_reset_today()
            self.send_json({'success': True, 'state': res})
            return

        if path == '/api/sync_emails':
            from email_tracker import sync_latest_gmail_sent
            added = sync_latest_gmail_sent(max_results=30)
            self.send_json({'success': True, 'added': added})
            return

        if path == '/api/lead/add':
            company = req_data.get('company', '').strip()
            name = req_data.get('name', '').strip()
            phone = req_data.get('phone', '').strip()
            email = req_data.get('email', '').strip()
            website = req_data.get('website', '').strip()
            location = req_data.get('location', '').strip()
            colleague = req_data.get('colleague', '').strip() or 'Direct'
            notes = req_data.get('notes', '').strip()

            if not company:
                self.send_json({'error': 'Company name is required'}, 400)
                return

            slug = re.sub(r'[^a-z0-9]', '', company.lower())
            if not slug:
                slug = f"lead_{int(datetime.now().timestamp())}"

            leads_dir = os.path.join(WORKSPACE_DIR, 'knowledge_base', 'leads')
            os.makedirs(leads_dir, exist_ok=True)
            lead_md_path = os.path.join(leads_dir, f"{slug}.md")

            md_content = f"""# CALL COPILOT SALES DOSSIER: {company}

## 1. CONTACT & LEAD PROFILE
| Field | Details |
|---|---|
| **Business Name** | {company} |
| **Contact / Decision Maker** | {name or company} |
| **Phone** | {phone or 'N/A'} |
| **Email** | {email or 'N/A'} |
| **Website** | {website or 'N/A'} |
| **Location & Timezone** | {location or 'USA (EST)'} |
| **Outreach Colleague** | {colleague} |
| **Initial Reply** | {notes or 'Replied to outreach'} |

---

### Live Call Opener:
> "Hi {name or company}, this is Shiv. This is a follow-up call regarding your email reply to {colleague} about your website and Google visibility. Can we do a quick 5-minute call tomorrow to look at it together?"

### If they ask "What is it about?":
> "Your website is not ranking on Google for key buyer searches, and local competitors are capturing the market share. I can show you what to fix in 5 minutes."

### Voicemail (Under 15 seconds):
> "Hi {name or company}, this is Shiv. This is a follow-up call regarding your email reply to {colleague} about your website and SEO problem. I just sent the details to your email. Please check your inbox or call me back at (645) 220-1660. Thank you!"
"""
            with open(lead_md_path, 'w', encoding='utf-8') as fp:
                fp.write(md_content)

            pms_cache_path = os.path.join(WORKSPACE_DIR, 'data', 'pms_cache.json')
            cache = {}
            if os.path.exists(pms_cache_path):
                try:
                    with open(pms_cache_path, 'r', encoding='utf-8') as fp:
                        cache = json.load(fp)
                except Exception:
                    pass
            cache[slug] = {
                'company_name': company,
                'client_name': name,
                'website': website,
                'email': email,
                'phone': phone,
                'location': location,
                'pms_colleague': colleague
            }
            with open(pms_cache_path, 'w', encoding='utf-8') as fp:
                json.dump(cache, fp, indent=2, ensure_ascii=False)

            self.send_json({'success': True, 'slug': slug})
            return

        self.send_error(404, "Endpoint Not Found")

def run(port=5000):
    import threading
    def auto_sync_worker():
        import time
        from email_tracker import sync_latest_gmail_sent
        while True:
            time.sleep(90)
            try:
                sync_latest_gmail_sent(20)
            except Exception:
                pass

    t = threading.Thread(target=auto_sync_worker, daemon=True)
    t.start()

    server_address = ('127.0.0.1', port)

    try:
        httpd = HTTPServer(server_address, TrackerHandler)
    except OSError:
        port = 5050
        server_address = ('127.0.0.1', port)
        httpd = HTTPServer(server_address, TrackerHandler)

    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f"[ONLINE] CALL COPILOT LEAD TRACKER & CALLING COCKPIT RUNNING!")
    print(f"--> Open in your browser: {url}")
    print(f"=======================================================\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Call Copilot Tracker...")
        httpd.server_close()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run(port)
