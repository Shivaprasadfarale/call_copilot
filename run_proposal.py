"""
Unified CLI Entrypoint for Proposal Generation
Usage:
    python run_proposal.py --slug blueoasis
    python run_proposal.py --config clients/blueoasisglobal/proposal_config.json
"""

import os
import sys
import argparse

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from src.proposal_pipeline import generate_proposal_pdf

def main():
    parser = argparse.ArgumentParser(description="Master Executive Proposal CLI Runner")
    parser.add_argument("--slug", type=str, help="Client slug (e.g., blueoasis, ecosystems_northwest)")
    parser.add_argument("--config", type=str, help="Direct path to proposal config JSON")
    parser.add_argument("--out", type=str, help="Optional custom output PDF name")
    args = parser.parse_args()

    if not args.slug and not args.config:
        print("[ERROR] Please provide --slug [client_slug] or --config [path/to/config.json]")
        print("Example: python run_proposal.py --slug blueoasis")
        sys.exit(1)

    target = args.config if args.config else args.slug
    print(f"\n=======================================================")
    print(f"  RUNNING EXECUTIVE PROPOSAL GENERATOR: {target.upper()}")
    print(f"=======================================================\n")

    out_pdf = generate_proposal_pdf(target, args.out)

    if os.path.exists(out_pdf):
        size_mb = os.path.getsize(out_pdf) / (1024 * 1024)
        print(f"\n[SUCCESS] Proposal Ready: {out_pdf}")
        print(f"File Size: {size_mb:.2f} MB")
        print("=======================================================\n")
    else:
        print(f"\n[ERROR] Failed to generate proposal PDF at: {out_pdf}")
        sys.exit(1)

if __name__ == "__main__":
    main()
