import os
import json
from datetime import datetime, timezone

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE_DIR, 'data')
STATE_FILE = os.path.join(DATA_DIR, 'tracker_state.json')

os.makedirs(DATA_DIR, exist_ok=True)

def get_today_str() -> str:
    """Returns today's date in local machine YYYY-MM-DD."""
    return datetime.now().strftime('%Y-%m-%d')

def load_raw_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {STATE_FILE}: {e}")
    return {'date': get_today_str(), 'daily_goal': 25, 'leads': {}}

def save_state(state: dict):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_tracker_state() -> dict:
    state = load_raw_state()
    today_str = get_today_str()
    
    # Check for midnight automatic reset
    saved_date = state.get('date', '')
    if saved_date != today_str:
        print(f"New day detected ({saved_date} -> {today_str})! Performing automatic midnight reset of called_today checkmarks...")
        state['date'] = today_str
        leads_dict = state.setdefault('leads', {})
        for slug, lead_data in leads_dict.items():
            lead_data['called_today'] = False
        save_state(state)
        
    return state

def update_lead_status(slug: str, outcome: str = None, note: str = None, meeting_datetime: str = None, callback_datetime: str = None, toggle_called: bool = None) -> dict:
    state = get_tracker_state()
    leads_dict = state.setdefault('leads', {})
    lead_data = leads_dict.setdefault(slug, {
        'called_today': False,
        'call_history': [],
        'last_outcome': '',
        'last_called_at': '',
        'total_calls': 0,
        'quick_notes': '',
        'meeting_datetime': '',
        'callback_datetime': ''
    })
    
    now_iso = datetime.now().strftime('%Y-%m-%d %I:%M %p')
    
    if toggle_called is not None:
        lead_data['called_today'] = toggle_called
        if toggle_called and not lead_data.get('last_called_at'):
            lead_data['last_called_at'] = now_iso
            lead_data['total_calls'] = lead_data.get('total_calls', 0) + 1
            
    if outcome:
        lead_data['called_today'] = True
        lead_data['last_outcome'] = outcome
        lead_data['last_called_at'] = now_iso
        lead_data['total_calls'] = lead_data.get('total_calls', 0) + 1
        
        history_entry = {
            'timestamp': now_iso,
            'outcome': outcome,
            'note': note or ''
        }
        if meeting_datetime:
            history_entry['meeting_datetime'] = meeting_datetime
            lead_data['meeting_datetime'] = meeting_datetime
            
        if callback_datetime:
            history_entry['callback_datetime'] = callback_datetime
            lead_data['callback_datetime'] = callback_datetime
            
        lead_data.setdefault('call_history', []).append(history_entry)
        
    if note is not None:
        lead_data['quick_notes'] = note
        
    save_state(state)
    return lead_data

def manual_reset_today() -> dict:
    """Manually resets called_today for all leads."""
    state = load_raw_state()
    state['date'] = get_today_str()
    for slug, lead_data in state.setdefault('leads', {}).items():
        lead_data['called_today'] = False
    save_state(state)
    return state

def get_daily_report() -> dict:
    """Returns today's comprehensive call statistics and logs."""
    state = get_tracker_state()
    today_str = get_today_str()
    leads_dict = state.get('leads', {})
    
    dials_today = 0
    meetings_booked = []
    callbacks_set = []
    voicemails_left = []
    no_answers = []
    all_dialed = []
    
    for slug, l in leads_dict.items():
        if l.get('called_today'):
            dials_today += 1
            entry = {
                'slug': slug,
                'outcome': l.get('last_outcome', 'dialed'),
                'called_at': l.get('last_called_at', ''),
                'note': l.get('quick_notes', ''),
                'meeting': l.get('meeting_datetime', ''),
                'callback': l.get('callback_datetime', '')
            }
            all_dialed.append(entry)
            
            outcome = l.get('last_outcome', '')
            if outcome == 'meeting_booked':
                meetings_booked.append(entry)
            elif outcome == 'spoke_followup':
                callbacks_set.append(entry)
            elif outcome == 'left_voicemail':
                voicemails_left.append(entry)
            elif outcome == 'no_answer':
                no_answers.append(entry)
                
    return {
        'date': today_str,
        'daily_goal': state.get('daily_goal', 25),
        'total_dials': dials_today,
        'meetings_booked_count': len(meetings_booked),
        'meetings_booked': meetings_booked,
        'callbacks_count': len(callbacks_set),
        'callbacks_set': callbacks_set,
        'voicemails_count': len(voicemails_left),
        'no_answers_count': len(no_answers),
        'all_dialed': all_dialed
    }
