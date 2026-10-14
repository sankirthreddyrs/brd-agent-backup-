"""
Standalone extraction testing script:
Loads files from demo/data/, calls gemini_client.extract_requirements (live if configured, else demo),
verifies evidence with verify.verify_requirements, and prints a clean summary table.
"""
import os
import sys

# Ensure root dir is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import config, gemini_client, verify


def main():
    print("==================================================")
    print("      BRD Agent: Standalone Extraction Script     ")
    print("==================================================")

    data_dir = os.path.join(os.path.dirname(__file__), "..", "demo", "data")
    if not os.path.exists(data_dir):
        print(f"Error: Demo data directory not found at {data_dir}")
        sys.exit(1)

    # Load files from demo/data/
    files = {}
    for fname in sorted(os.listdir(data_dir)):
        fpath = os.path.join(data_dir, fname)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                files[fname] = f.read()

    print(f"Loaded {len(files)} files from {data_dir}: {', '.join(files.keys())}")

    is_live = bool(config.GCP_PROJECT_ID and not config.DEMO_MODE)
    mode_str = "LIVE (Vertex AI + Gemini)" if is_live else "DEMO (Local Mock/Cache)"
    print(f"Execution Mode: {mode_str}\n")

    if is_live:
        print("Calling live Gemini extraction...")
        try:
            extracted_reqs = gemini_client.extract_requirements(files)
        except Exception as e:
            print(f"Live extraction failed: {e}. Falling back to demo mode.")
            extracted_reqs = gemini_client.demo_extraction(files)
    else:
        print("Calling demo extraction...")
        extracted_reqs = gemini_client.demo_extraction(files)

    print(f"Extracted {len(extracted_reqs)} raw requirements.\n")

    # Run strict verification
    print("Running verification against source files...")
    verified_reqs = verify.verify_requirements(extracted_reqs, files)

    # Print clean summary table
    print("\n" + "=" * 90)
    print(f"{'ID':<7} | {'Status':<10} | {'Type':<15} | {'Requirement Text'}")
    print("=" * 90)

    for r in verified_reqs:
        status_symbol = "PASS [OK]" if r.verification_status == "verified" else "FAIL [X]"
        print(f"{r.id:<7} | {status_symbol:<10} | {r.type:<15} | {r.text}")
        for idx, ev in enumerate(r.evidence):
            ev_status = "OK" if ev.verified else "NOT VERIFIED"
            if ev.kind == "image":
                detail = f"box: {ev.box_2d}"
            elif ev.kind == "pdf":
                detail = f"p.{ev.page} quote: \"{ev.quote}\""
            else:
                detail = f"line {ev.line} quote: \"{ev.quote}\""
            print(f"        -> [{ev_status}] {ev.file_name} ({ev.kind}): {detail}")
            if not ev.verified:
                print(f"            Note: {ev.verify_note}")
        print("-" * 90)

    verified_count = sum(1 for r in verified_reqs if r.verification_status == "verified")
    print(f"\nSummary: {verified_count}/{len(verified_reqs)} requirements verified.")
    print("=" * 90)


if __name__ == "__main__":
    main()
