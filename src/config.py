"""
Call Copilot - Configuration Management
Loads from config.yaml, provides defaults, validates keys.
"""
import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "call_logs")

DEFAULT_CONFIG = {
    "deepgram_api_key": "",
    "groq_api_key": "",
    "groq_model": "qwen/qwen3.8-27b",
    "language": "en-US",
    "stt_model": "nova-3",
    "utterance_end_ms": 1200,
    "silence_trigger_sec": 2.0,
    "max_response_tokens": 200,
    "temperature": 0.7,
    "overlay_width": 440,
    "overlay_height": 560,
    "overlay_opacity": 0.92,
    "font_size_response": 13,
    "font_size_transcript": 12,
    "save_call_logs": True,
    "company_name": "Innovate Marketers",
    "company_location": "Miami, FL",
    "services": "SEO, PPC (Google Ads), Web Design, Social Media Marketing",
}


def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config.yaml: {e}")
    return config


def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"Warning: Could not save config.yaml: {e}")


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)
    return LOG_DIR
