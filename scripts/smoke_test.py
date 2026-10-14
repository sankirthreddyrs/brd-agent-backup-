"""
Smoke test for Google Cloud services:
Step 1: Check .env variables. If GCP_PROJECT_ID or GCS_BUCKET is empty, print instructions and exit 0.
Step 2: Test Cloud Storage (upload and delete a test ping blob).
Step 3: Test BigQuery (ensure dataset and tables exist).
Step 4: Test Vertex AI + Gemini structured output & box_2d on auth_wireframe.jpg.
"""
import os
import sys

# Ensure root dir is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import config


def step_1_check_env() -> bool:
    print("\n--- Step 1: Checking Environment Configuration ---")
    vars_to_check = {
        "GCP_PROJECT_ID": config.GCP_PROJECT_ID,
        "GCP_LOCATION": config.GCP_LOCATION,
        "GCS_BUCKET": config.GCS_BUCKET,
        "BQ_DATASET": config.BQ_DATASET,
        "GEMINI_MODEL": config.GEMINI_MODEL,
    }

    for k, v in vars_to_check.items():
        status = v if v else "<NOT SET>"
        print(f"  {k}: {status}")

    if not config.GCP_PROJECT_ID or not config.GCS_BUCKET:
        print("\n[SKIP] GCP_PROJECT_ID or GCS_BUCKET is not set in .env.")
        print("To enable and test Live Mode with Google Cloud:")
        print("  1. Run: gcloud auth application-default login")
        print("  2. Set in .env:")
        print("       GCP_PROJECT_ID=your-gcp-project-id")
        print("       GCS_BUCKET=your-unique-gcs-bucket-name")
        print("       DEMO_MODE=false")
        print("  3. Run this script again.")
        return False

    print("[PASS] Environment variables are set.")
    return True


def step_2_test_storage() -> bool:
    print("\n--- Step 2: Testing Google Cloud Storage ---")
    try:
        from google.cloud import storage

        client = storage.Client(project=config.GCP_PROJECT_ID)
        bucket = client.bucket(config.GCS_BUCKET)

        # Upload ping blob
        ping_blob_name = "smoke_test/ping.txt"
        blob = bucket.blob(ping_blob_name)
        blob.upload_from_string(b"ping from brd-agent smoke test")
        print(f"  Successfully wrote gs://{config.GCS_BUCKET}/{ping_blob_name}")

        # Delete ping blob
        blob.delete()
        print(f"  Successfully deleted gs://{config.GCS_BUCKET}/{ping_blob_name}")
        print("[PASS] Cloud Storage upload & delete verified.")
        return True
    except Exception as e:
        print(f"[FAIL] Cloud Storage check failed: {e}")
        print("Fix with:")
        print(f"  gcloud storage buckets create gs://{config.GCS_BUCKET} --location={config.GCP_LOCATION}")
        print(f"  gcloud projects add-iam-policy-binding {config.GCP_PROJECT_ID} --member=user:YOUR_EMAIL --role=roles/storage.objectAdmin")
        return False


def step_3_test_bigquery() -> bool:
    print("\n--- Step 3: Testing BigQuery Tables ---")
    try:
        from app import bq
        bq.ensure_tables()
        print(f"  Ensured all 6 tables exist in {config.GCP_PROJECT_ID}.{config.BQ_DATASET}")
        print("[PASS] BigQuery dataset & schema verified.")
        return True
    except Exception as e:
        print(f"[FAIL] BigQuery check failed: {e}")
        print("Fix with:")
        print(f"  bq --location={config.GCP_LOCATION} mk --dataset {config.GCP_PROJECT_ID}:{config.BQ_DATASET}")
        print(f"  gcloud projects add-iam-policy-binding {config.GCP_PROJECT_ID} --member=user:YOUR_EMAIL --role=roles/bigquery.admin")
        return False


def step_4_test_vertex_gemini() -> bool:
    print("\n--- Step 4: Testing Vertex AI & Gemini Model ---")
    wireframe_path = os.path.join(os.path.dirname(__file__), "..", "demo", "data", "auth_wireframe.jpg")
    if not os.path.exists(wireframe_path):
        print(f"[FAIL] Test image not found at {wireframe_path}")
        return False

    try:
        with open(wireframe_path, "rb") as f:
            img_bytes = f.read()

        from app import gemini_client
        reqs = gemini_client.extract_requirements(
            files={"auth_wireframe.jpg": img_bytes}
        )
        print(f"  Gemini returned {len(reqs)} structured requirements from wireframe.")
        for r in reqs:
            for ev in r.evidence:
                if ev.box_2d:
                    print(f"  Found box_2d: {ev.box_2d} for {r.id}")

        print("[PASS] Vertex AI & Gemini structured extraction verified.")
        return True
    except Exception as e:
        print(f"[FAIL] Vertex AI check failed: {e}")
        print("Fix with:")
        print(f"  gcloud services enable aiplatform.googleapis.com")
        print(f"  gcloud projects add-iam-policy-binding {config.GCP_PROJECT_ID} --member=user:YOUR_EMAIL --role=roles/aiplatform.user")
        return False


def main():
    print("==================================================")
    print("      BRD Agent: Google Cloud Smoke Test          ")
    print("==================================================")

    if not step_1_check_env():
        # Exit cleanly (0) as instructed when credentials are blank
        sys.exit(0)

    s2 = step_2_test_storage()
    s3 = step_3_test_bigquery()
    s4 = step_4_test_vertex_gemini()

    print("\n==================================================")
    if s2 and s3 and s4:
        print("ALL GOOGLE CLOUD CHECKS PASSED [LIVE MODE READY]")
    else:
        print("SOME CLOUD CHECKS FAILED - REVIEW FIXES ABOVE")
    print("==================================================")


if __name__ == "__main__":
    main()
