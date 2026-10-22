"""
Automated Stress-Test Suite for Intake, Site Analyzer, Keyword Generator & Email Pipelines
Tests all core functions and scripts for zero runtime exceptions and data integrity.
"""

import os
import sys
import json
import traceback

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

failed_tests = []
passed_tests = []

def run_test(name, func):
    print(f"\n--- [TEST] {name} ---", flush=True)
    try:
        func()
        print(f"[PASS] PASSED: {name}", flush=True)
        passed_tests.append(name)
    except Exception as e:
        print(f"[FAIL] FAILED: {name}", flush=True)
        traceback.print_exc()
        failed_tests.append((name, str(e)))


def test_keyword_generator():
    from src.keyword_generator import generate_smart_keywords
    
    # 1. Virtual model: Must NOT have city names
    kw_virtual = generate_smart_keywords(
        company_name="Vince Cortese",
        niche="mindset",
        model="NATIONWIDE_VIRTUAL",
        base_city="Pittsburgh"
    )
    assert len(kw_virtual) == 10, f"Expected 10 keywords, got {len(kw_virtual)}"
    for k in kw_virtual:
        assert "pittsburgh" not in k["phrase"].lower(), f"Virtual query contains city: {k['phrase']}"
        assert k["id"] >= 1 and k["id"] <= 10
        assert k["fee_range"]
        
    # 2. Local model: Must have regional hubs
    hubs = ["Denton", "Dallas", "Fort Worth", "Plano", "Frisco", "McKinney", "Arlington", "Grapevine", "Irving", "Garland"]
    kw_local = generate_smart_keywords(
        company_name="Apex Roofing",
        niche="commercial roofing",
        model="LOCAL_IN_PERSON",
        base_city="Denton",
        regional_hubs=hubs
    )
    assert len(kw_local) == 10, f"Expected 10 keywords, got {len(kw_local)}"
    cities_found = [k["phrase"].split()[-1].title() for k in kw_local]
    assert len(set(cities_found)) >= 5, f"Expected varied regional hubs, got: {cities_found}"


def test_email_generator():
    from src.email_generator import generate_track_a_diagnostic, generate_track_b_executive, format_anti_autolink

    # Test anti-autolink
    clean = format_anti_autolink("https://vincecortese.com/ and email vinnie@vinniecmarketing.com")
    assert "https://" not in clean
    assert " . com" in clean
    assert " @ " in clean

    # Test Track A
    track_a = generate_track_a_diagnostic(
        client_name="Vince",
        colleague_name="Megan",
        quoted_headers="From: Vince\nSubject: Re: Website",
        quoted_body="Yes please.",
        website="https://vincecortese.com/",
        diagnostics={"authority_score": "2", "organic_traffic": "0", "backlinks": "891", "ref_domains": "806"},
        real_competitors=["Heidi Sadecky", "Coach Monique"],
        open_loop_question="Are most of your clients corporate or private?",
        service_type="virtual program"
    )
    assert "Hi Vince," in track_a
    assert "Domain Authority Score: 2 / 100" in track_a
    assert "Heidi Sadecky and Coach Monique" in track_a
    assert "Are most of your clients corporate or private?" in track_a

    # Test Track B
    track_b = generate_track_b_executive(
        client_name="Vince",
        colleague_name="Megan",
        quoted_headers="From: Vince\nSubject: Re: Website",
        quoted_body="Yes please.",
        company_name="InVINCEble Mindset",
        packages=[
            {"name": "30 Days Fundamentals", "price": "$397"},
            {"name": "180 Days Optimization", "price": "$3,582"}
        ],
        competitors=["Christine Hassler", "Molly Fletcher"],
        delivery_scope="nationwide across the United States",
        service_label="mindset training and executive coaching"
    )
    assert "Hi Vince," in track_b
    assert "spent over 3 hours specifically for you" in track_b
    assert "30 Days Fundamentals ($397)" in track_b
    assert "Christine Hassler and Molly Fletcher" in track_b


def test_site_analyzer_parser():
    from src.site_analyzer import extract_packages_and_pricing, detect_operational_model

    sample_text = """
    Vince Cortese
    Available Online
    30 Days - Fundamentals
    Develop the line of thinking required
    Ended
    Jul 20, 2026 - Oct 12, 2026
    $397
    4 Zoom Calls
    
    90 Days Basic Training
    Unlock your potential
    $1,191
    13 Zoom calls
    
    180 Days Performance Optimization
    Build a lasting framework
    $3,582
    26 Zoom Calls
    """

    pkgs = extract_packages_and_pricing(sample_text)
    assert len(pkgs) >= 3, f"Expected at least 3 packages, got {len(pkgs)}"
    prices = [p["price"] for p in pkgs]
    assert any("$397" in p for p in prices), f"Missing $397 in {prices}"
    assert any("$1,191" in p for p in prices), f"Missing $1,191 in {prices}"
    assert any("$3,582" in p for p in prices), f"Missing $3,582 in {prices}"

    # Operational model detection
    model_info = detect_operational_model(sample_text)
    assert model_info["model"] == "NATIONWIDE_VIRTUAL", f"Expected NATIONWIDE_VIRTUAL, got {model_info['model']}"


def test_proof_sheet_generator():
    from src.proof_sheet_generator import generate_proof_sheet
    pdf_path = os.path.join(WORKSPACE_DIR, "clients", "vinniecmarketing", "Vinniecmarketing_Google_Search_Audit.pdf")
    config_path = os.path.join(WORKSPACE_DIR, "clients", "vinniecmarketing", "config.json")
    
    if os.path.exists(pdf_path) and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        out_sheet = os.path.join(WORKSPACE_DIR, "scratch", "test_proof_sheet.png")
        res = generate_proof_sheet(pdf_path, cfg, output_path=out_sheet)
        assert os.path.exists(out_sheet), "Proof sheet was not generated"
        assert os.path.getsize(out_sheet) > 50000, "Proof sheet is too small"
        os.remove(out_sheet)


def test_run_intake_dry_run():
    from run_intake import parse_lead_input
    sample_lead = """
    From: Vince <vinnie@vinniecmarketing.com>
    Date: October 13, 2026
    Subject: Re: Every week you wait costs you leads
    To: Megan <adke3091@gmail.com>

    Yes, that would be great.
    """
    data = parse_lead_input(sample_lead)
    assert data["client_name"] == "Vince", f"Expected Vince, got {data['client_name']}"
    assert data["email"] == "vinnie@vinniecmarketing.com", f"Expected vinnie@vinniecmarketing.com, got {data['email']}"
    assert "vinniecmarketing.com" in data["website"], f"Expected website from domain, got {data['website']}"


if __name__ == "__main__":
    print("=" * 60)
    print("  RUNNING PIPELINE STRESS-TEST & INTEGRITY VERIFICATION")
    print("=" * 60)

    run_test("Keyword Generator (Virtual vs Local)", test_keyword_generator)
    run_test("Email Generator (Track A & Track B)", test_email_generator)
    run_test("Site Analyzer Multi-Line Package Parser", test_site_analyzer_parser)
    run_test("Proof Sheet Composite Generator", test_proof_sheet_generator)
    run_test("Pre-Flight Lead Parser", test_run_intake_dry_run)

    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {len(passed_tests)} Passed, {len(failed_tests)} Failed")
    print("=" * 60)

    if failed_tests:
        print("\nFailed Tests:")
        for name, err in failed_tests:
            print(f"  • {name}: {err}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED WITH 100% SUCCESS!")
        sys.exit(0)
