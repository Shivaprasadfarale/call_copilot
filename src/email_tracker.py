import os
import re
import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE_DIR, 'data')
CACHE_FILE = os.path.join(DATA_DIR, 'email_sent_history.json')
ANALYZED_SENT_FILE = os.path.join(WORKSPACE_DIR, 'scratch', 'analyzed_sent.json')

def norm_email(e: str) -> str:
    if not e: return ''
    e = e.lower().strip()
    e = re.sub(r'\s*@\s*', '@', e)
    e = re.sub(r'\s*\.\s*', '.', e)
    return e

def format_relative_time(dt: datetime) -> str:
    now = datetime.now(timezone.utc)
    # Ensure dt is aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    total_seconds = int(diff.total_seconds())

    if total_seconds < 0:
        return "Just now"
    elif total_seconds < 3600:
        mins = max(1, total_seconds // 60)
        return f"{mins}m ago"
    elif total_seconds < 86400:
        hrs = total_seconds // 3600
        return f"{hrs}h ago"
    elif total_seconds < 172800:
        return "Yesterday"
    else:
        days = total_seconds // 86400
        return f"{days}d ago"

def load_sent_cache() -> dict:
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    # Seed from analyzed_sent.json if empty
    if not cache and os.path.exists(ANALYZED_SENT_FILE):
        try:
            with open(ANALYZED_SENT_FILE, 'r', encoding='utf-8') as f:
                analyzed = json.load(f)
            for item in analyzed:
                em = norm_email(item.get('email'))
                if not em: continue
                date_str = item.get('date', '')
                subj = item.get('subject', '')
                dt_iso = ''
                try:
                    dt = parsedate_to_datetime(date_str)
                    dt_iso = dt.isoformat()
                except Exception:
                    pass

                if em not in cache:
                    cache[em] = []
                cache[em].append({
                    'date_raw': date_str,
                    'date_iso': dt_iso,
                    'subject': subj
                })
            save_sent_cache(cache)
        except Exception as e:
            print(f"Error seeding cache from analyzed_sent: {e}")
    return cache

def save_sent_cache(cache: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def get_lead_email_history(email: str) -> dict:
    clean_em = norm_email(email)
    cache = load_sent_cache()
    records = cache.get(clean_em, [])

    if not records:
        return {
            'has_history': False,
            'sent_count': 0,
            'first_sent_date': 'Not sent yet',
            'first_sent_relative': '',
            'last_sent_date': 'Not sent yet',
            'last_sent_relative': '',
            'days_since_last_sent': None,
            'last_subject': '',
            'followup_due': False,
            'timeline': []
        }

    # Parse and sort by datetime
    parsed_items = []
    for r in records:
        dt = None
        iso_str = r.get('date_iso')
        if iso_str:
            try:
                dt = datetime.fromisoformat(iso_str)
            except Exception:
                pass
        if not dt and r.get('date_raw'):
            try:
                dt = parsedate_to_datetime(r['date_raw'])
            except Exception:
                pass

        parsed_items.append({
            'dt': dt,
            'date_raw': r.get('date_raw', ''),
            'subject': r.get('subject', '')
        })

    # Filter valid dt and sort chronological
    valid_items = [p for p in parsed_items if p['dt']]
    if valid_items:
        valid_items.sort(key=lambda x: x['dt'])
    else:
        valid_items = parsed_items

    first_item = valid_items[0]
    last_item = valid_items[-1]

    first_dt = first_item['dt']
    last_dt = last_item['dt']

    first_date_str = first_dt.strftime('%b %d, %Y') if first_dt else first_item['date_raw']
    last_date_str = last_dt.strftime('%b %d, %Y (%I:%M %p)') if last_dt else last_item['date_raw']
    last_date_short = last_dt.strftime('%b %d, %Y') if last_dt else last_item['date_raw']

    first_rel = format_relative_time(first_dt) if first_dt else ''
    last_rel = format_relative_time(last_dt) if last_dt else ''

    days_since = None
    followup_due = False
    if last_dt:
        now = datetime.now(timezone.utc)
        if last_dt.tzinfo is None:
            last_dt_aware = last_dt.replace(tzinfo=timezone.utc)
        else:
            last_dt_aware = last_dt
        diff = now - last_dt_aware
        days_since = max(0, diff.days)
        if days_since >= 2:
            followup_due = True

    timeline = []
    for it in reversed(valid_items):
        it_dt = it['dt']
        timeline.append({
            'date': it_dt.strftime('%b %d, %Y • %I:%M %p') if it_dt else it['date_raw'],
            'relative': format_relative_time(it_dt) if it_dt else '',
            'subject': it['subject']
        })

    return {
        'has_history': True,
        'sent_count': len(records),
        'first_sent_date': first_date_str,
        'first_sent_relative': first_rel,
        'last_sent_date': last_date_str,
        'last_sent_date_short': last_date_short,
        'last_sent_relative': last_rel,
        'days_since_last_sent': days_since,
        'last_subject': last_item['subject'],
        'followup_due': followup_due,
        'timeline': timeline
    }

def sync_latest_gmail_sent(max_results: int = 25) -> int:
    """Fast incremental sync of latest sent emails from Gmail."""
    try:
        from gmail_helper import get_gmail_service
        service = get_gmail_service()
        if not service:
            return 0
            
        res = service.users().messages().list(userId='me', q='in:sent', maxResults=max_results).execute()
        msgs = res.get('messages', [])
        if not msgs:
            return 0
            
        cache = load_sent_cache()
        updated = 0
        
        for m_summary in msgs:
            msg_id = m_summary['id']
            msg = service.users().messages().get(
                userId='me',
                id=msg_id,
                format='metadata',
                metadataHeaders=['Date', 'Subject', 'To', 'From']
            ).execute()
            
            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            to_raw = headers.get('To', '')
            subj = headers.get('Subject', '')
            date_raw = headers.get('Date', '')
            
            # extract emails from To header
            recipients = re.findall(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', to_raw)
            for r in recipients:
                em = norm_email(r)
                if not em: continue
                
                dt_iso = ''
                try:
                    dt = parsedate_to_datetime(date_raw)
                    dt_iso = dt.isoformat()
                except Exception:
                    pass
                    
                existing = cache.get(em, [])
                if not any(ex.get('subject') == subj and ex.get('date_raw') == date_raw for ex in existing):
                    if em not in cache:
                        cache[em] = []
                    cache[em].append({
                        'date_raw': date_raw,
                        'date_iso': dt_iso,
                        'subject': subj
                    })
                    updated += 1
                    
        if updated > 0:
            save_sent_cache(cache)
        return updated
    except Exception as e:
        print(f"Incremental Gmail sync error: {e}")
        return 0

