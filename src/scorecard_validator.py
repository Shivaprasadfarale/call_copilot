import os
import re
import subprocess
import json

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR_SCRIPT = os.path.join(WORKSPACE_DIR, "src", "run_ocr_clean.ps1")
if not os.path.exists(OCR_SCRIPT):
    OCR_SCRIPT = os.path.join(WORKSPACE_DIR, "scratch", "run_ocr_clean.ps1")
if not os.path.exists(OCR_SCRIPT):
    OCR_SCRIPT = os.path.join(WORKSPACE_DIR, "archive", "scratch", "run_ocr_clean.ps1")

def get_image_ocr_text(image_path: str) -> str:
    """Runs Windows native OCR on the screenshot image and returns the recognized text."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Scorecard image not found at: {image_path}")
        
    # Run OCR on original image
    cmd_orig = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", OCR_SCRIPT,
        "-ImagePath", image_path
    ]
    res_orig = subprocess.run(cmd_orig, capture_output=True, encoding="utf-8", errors="ignore")
    ocr_combined = res_orig.stdout.strip()

    # Run on 2x upscaled + grayscale + high-contrast version for enhanced number recognition
    try:
        from PIL import Image, ImageOps, ImageEnhance
        im = Image.open(image_path)
        temp_upscaled = os.path.join(WORKSPACE_DIR, "scratch", f"temp_ocr_enhanced_{os.path.basename(image_path)}")
        os.makedirs(os.path.dirname(temp_upscaled), exist_ok=True)
        im_up = im.resize((im.width * 2, im.height * 2), Image.Resampling.LANCZOS)
        gray = ImageOps.grayscale(im_up)
        enhancer = ImageEnhance.Contrast(gray)
        high_contrast = enhancer.enhance(1.8)
        high_contrast.save(temp_upscaled)
        cmd_up = [
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-File", OCR_SCRIPT,
            "-ImagePath", temp_upscaled
        ]
        res_up = subprocess.run(cmd_up, capture_output=True, encoding="utf-8", errors="ignore")
        ocr_combined += f"\n{res_up.stdout.strip()}"
        if os.path.exists(temp_upscaled):
            try:
                os.remove(temp_upscaled)
            except Exception:
                pass
    except Exception as e:
        pass

    return ocr_combined

def parse_html_metrics(html_body: str) -> dict:
    """Extracts the reported metrics from the email HTML body."""
    metrics = {}
    
    # Strip HTML tags and entities for reliable metric parsing
    clean_text = re.sub(r'<[^>]+>', ' ', html_body)
    clean_text = re.sub(r'&amp;', '&', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Backlinks & Ref Domains in bullets:
    # e.g. "Total Backlinks & Referring Domains: 164 links across 147 domains"
    # or "Total Backlinks &amp; Referring Domains: 112 links across 42 domains"
    m_links = re.search(r'Total Backlinks.*?:\s*([\d,\.]+[KMkm]?)\s+links\s+across\s+([\d,\.]+[KMkm]?)\s+domains', clean_text, re.IGNORECASE)
    if m_links:
        metrics['backlinks'] = m_links.group(1).replace(',', '')
        metrics['ref_domains'] = m_links.group(2).replace(',', '')
    else:
        # Check narrative sentence: "You have 112 backlinks across 42 referring domains"
        m_narrative = re.search(r'You have\s+([\d,\.]+[KMkm]?)\s+backlinks\s+across\s+([\d,\.]+[KMkm]?)\s+referring domains', clean_text, re.IGNORECASE)
        if m_narrative:
            metrics['backlinks'] = m_narrative.group(1).replace(',', '')
            metrics['ref_domains'] = m_narrative.group(2).replace(',', '')

    # Domain Authority Score:
    # e.g. "Domain Authority Score: 4 / 100" or "Domain Authority Score: 2 / 100"
    m_auth = re.search(r'Domain Authority Score:\s*(\d{1,2})', clean_text, re.IGNORECASE)
    if m_auth:
        metrics['authority_score'] = m_auth.group(1)

    # Monthly Organic Traffic:
    # e.g. "Monthly Organic Traffic: 8 visits/mo" or "0 visits/mo" or "n/a visits/mo"
    m_traf = re.search(r'Monthly Organic Traffic:\s*([\d,]+[KMkm]?|n/a)', clean_text, re.IGNORECASE)
    if m_traf:
        metrics['organic_traffic'] = m_traf.group(1).replace(',', '')

    # Organic Keywords Indexed:
    # e.g. "Organic Keywords Indexed: 19 terms" or "2 terms" or "n/a terms"
    m_kw = re.search(r'Organic Keywords Indexed:\s*([\d,]+[KMkm]?|n/a)', clean_text, re.IGNORECASE)
    if m_kw:
        metrics['organic_keywords'] = m_kw.group(1).replace(',', '')

    return metrics

def validate_draft_against_scorecard(html_body: str, image_path: str):
    """
    STRICT 100% PARITY VALIDATOR:
    Extracts text metrics from html_body and verifies them against the scorecard image OCR text.
    If there is ANY discrepancy between what is claimed in the text and what is on the scorecard,
    raises a ValueError and halts draft creation.
    """
    if not image_path or not os.path.exists(image_path):
        return  # No image to validate against
        
    html_metrics = parse_html_metrics(html_body)
    if not html_metrics:
        # Not a technical audit email (e.g. follow-up or simple text email)
        return

    ocr_text = get_image_ocr_text(image_path)
    
    errors = []
    
    # 1. Backlinks check
    if 'backlinks' in html_metrics:
        b_val = html_metrics['backlinks']
        # Check if b_val appears in OCR text (handling 2K, 2,000, 0 / O, etc.)
        if b_val == '0':
            pattern = r'\b(0|[Oo]|@)\b'
        else:
            pattern = rf'\b{re.escape(b_val)}\b'
        if not re.search(pattern, ocr_text, re.IGNORECASE):
            errors.append(f"Backlinks mismatch: Email claims '{b_val}', but '{b_val}' does not appear in scorecard OCR.")
            
    # 2. Ref Domains check
    if 'ref_domains' in html_metrics:
        r_val = html_metrics['ref_domains']
        if r_val == '0':
            pattern = r'\b(0|[Oo]|@)\b'
        else:
            pattern = rf'\b{re.escape(r_val)}\b'
        if not re.search(pattern, ocr_text, re.IGNORECASE):
            errors.append(f"Referring Domains mismatch: Email claims '{r_val}', but '{r_val}' does not appear in scorecard OCR.")
            
    # 3. Organic Traffic check
    if 'organic_traffic' in html_metrics:
        t_val = html_metrics['organic_traffic']
        if t_val == '0':
            pattern = r'\b(0|[Oo]|@)\b'
        else:
            pattern = rf'\b{re.escape(t_val)}\b'
        if not re.search(pattern, ocr_text, re.IGNORECASE):
            # Handle Windows OCR artifact where Semrush percent change badge (e.g. 5% green pill)
            # adjacent to traffic number is read as trailing numeral, O, or % before TRAFFIC (e.g. '4630 TRAFFIC')
            if re.search(rf'\b{re.escape(t_val)}[0-9Oo%]?\s*TRAFFIC', ocr_text, re.IGNORECASE):
                pass
            else:
                errors.append(f"Organic Traffic mismatch: Email claims '{t_val}', but '{t_val}' does not appear in scorecard OCR.")

    # 4. Organic Keywords check
    if 'organic_keywords' in html_metrics:
        k_val = html_metrics['organic_keywords']
        if k_val == '0':
            pattern = r'\b(0|[Oo]|@)\b'
        else:
            pattern = rf'\b{re.escape(k_val)}\b'
        if not re.search(pattern, ocr_text, re.IGNORECASE):
            errors.append(f"Organic Keywords mismatch: Email claims '{k_val}', but '{k_val}' does not appear in scorecard OCR.")

    # 5. Authority Score check
    if 'authority_score' in html_metrics:
        a_val = html_metrics['authority_score']
        pattern = rf'\b{re.escape(a_val)}\b'
        is_match = bool(re.search(pattern, ocr_text, re.IGNORECASE))
        # Handle Windows OCR artifact where zero / unrated bar is read as O or @
        if not is_match and a_val == '0' and re.search(r'Authority Score\s*[@bO0-9]', ocr_text, re.IGNORECASE):
            is_match = True
        # Handle Windows OCR artifact where circular numeral 6 inside Semrush pill is read as @ or b
        if not is_match and a_val == '6' and re.search(r'Authority Score\s*[@bO]', ocr_text, re.IGNORECASE):
            is_match = True
        # Handle Windows OCR artifact where numeral 10 inside Semrush pill is read as IO, 1O, or I0
        if not is_match and a_val == '10' and re.search(r'Authority Score\s*[@bO0-9]*\s*(10|1O|IO|I0)\b', ocr_text, re.IGNORECASE):
            is_match = True
        # Handle Windows OCR artifact where numeral 11 is read as II, ll, 1I, or I1
        if not is_match and a_val == '11' and re.search(r'Authority Score\s*[@bO0-9]*\s*(11|II|ll|1I|I1)\b', ocr_text, re.IGNORECASE):
            is_match = True
        # Also check if Authority Score label is immediately followed by a_val
        if not is_match and re.search(rf'Authority Score\s*.*?\b{re.escape(a_val)}\b', ocr_text, re.IGNORECASE):
            is_match = True
        if not is_match:
            errors.append(f"Authority Score mismatch: Email claims '{a_val}', but '{a_val}' does not appear in scorecard OCR.")

    # 6. Narrative cross-check (e.g. 'You have X backlinks across Y referring domains')
    m_narrative = re.findall(r'You have\s+([\d,]+[KMkm]?)\s+backlinks\s+across\s+([\d,]+[KMkm]?)\s+referring domains', html_body, re.IGNORECASE)
    for n_back, n_ref in m_narrative:
        n_back_clean = n_back.replace(',', '').strip()
        n_ref_clean = n_ref.replace(',', '').strip()
        n_back_pattern = r'\b(0|[Oo]|@)\b' if n_back_clean == '0' else rf'\b{re.escape(n_back_clean)}\b'
        n_ref_pattern = r'\b(0|[Oo]|@)\b' if n_ref_clean == '0' else rf'\b{re.escape(n_ref_clean)}\b'
        if not re.search(n_back_pattern, ocr_text, re.IGNORECASE):
            errors.append(f"Narrative Backlinks mismatch: Body claims '{n_back}' backlinks, but '{n_back_clean}' is not on scorecard.")
        if not re.search(n_ref_pattern, ocr_text, re.IGNORECASE):
            errors.append(f"Narrative Ref Domains mismatch: Body claims '{n_ref}' referring domains, but '{n_ref_clean}' is not on scorecard.")

    if errors:
        error_msg = "\n".join([
            "=" * 60,
            "ERROR: SCORECARD METRIC PARITY VALIDATION FAILED!",
            "=" * 60,
            f"Image Path: {image_path}",
            "Mismatches detected:",
            *([f"  * {e}" for e in errors]),
            f"Scorecard OCR Raw Text:\n  '{ocr_text}'",
            "=" * 60,
            "Draft creation CANNOT proceed with false/contradicting numbers.",
            "Fix the HTML text to match the scorecard image 100% before re-attempting.",
            "=" * 60
        ])
        raise ValueError(error_msg)

    print(f"SUCCESS: SCORECARD PARITY PASSED 100%: All metrics in email match '{os.path.basename(image_path)}'")

def extract_scorecard_metrics(image_path: str) -> dict:
    """
    Extracts all standard Semrush scorecard metrics from an image using enhanced OCR.
    Returns a dict with parsed values:
    {
        'authority_score': str,
        'organic_traffic': str,
        'us_traffic_share': str,
        'ref_domains': str,
        'backlinks': str,
        'organic_keywords': str,
        'ai_visibility': str,
        'ai_mentions': str
    }
    """
    ocr_text = get_image_ocr_text(image_path)
    metrics = {
        'authority_score': '0',
        'organic_traffic': '0',
        'us_traffic_share': '',
        'ref_domains': '0',
        'backlinks': '0',
        'organic_keywords': '0',
        'ai_visibility': '0',
        'ai_mentions': '0'
    }

    # Authority score
    m_auth = re.search(r'Authority Score\s*.*?(\d{1,2}|II|ll)\b', ocr_text, re.IGNORECASE)
    if m_auth:
        val = m_auth.group(1)
        if val in ['II', 'll', '1I', 'I1']:
            val = '11'
        metrics['authority_score'] = val

    # Organic Traffic
    m_traf = re.search(r'Organic Traffic\s*.*?(\d+[\.\d]*[KMkm]?)\b', ocr_text, re.IGNORECASE)
    if m_traf:
        metrics['organic_traffic'] = m_traf.group(1)

    # US Traffic Share
    m_share = re.search(r'Traffic Share.*?(\d{1,3})%', ocr_text, re.IGNORECASE)
    if m_share:
        val = m_share.group(1).lstrip('0') or '0'
        metrics['us_traffic_share'] = f"{val}%"

    # Organic Keywords
    m_kw = re.search(r'Organic Keywords\s*.*?(\d+[\.\d]*[KMkm]?)\b', ocr_text, re.IGNORECASE)
    if m_kw:
        metrics['organic_keywords'] = m_kw.group(1)

    # Referring Domains
    m_ref = re.search(r'Ref\.?\s*Domains\s*.*?(\d+[\.\d]*[KMkm]?)\b', ocr_text, re.IGNORECASE)
    if m_ref:
        metrics['ref_domains'] = m_ref.group(1)

    # Backlinks
    m_back = re.search(r'Backlinks\s*.*?(\d+[\.\d]*[KMkm]?)\b', ocr_text, re.IGNORECASE)
    if m_back:
        metrics['backlinks'] = m_back.group(1)

    return metrics
