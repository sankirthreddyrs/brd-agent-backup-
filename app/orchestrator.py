import os
import uuid
import time
from typing import Callable, Optional
from app import config, verify, gaps
from app.schemas import RunResult, ArtifactInfo, Kind


def _detect_kind(file_name: str) -> tuple[Kind, str]:
    lower = file_name.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image", "image/jpeg"
    elif lower.endswith(".png"):
        return "image", "image/png"
    elif lower.endswith(".pdf"):
        return "pdf", "application/pdf"
    elif lower.endswith(".txt"):
        return "text", "text/plain"
    return "text", "application/octet-stream"


def load_demo_files() -> dict[str, bytes]:
    """Load canonical demo files from demo/data directory."""
    files: dict[str, bytes] = {}
    data_dir = config.DEMO_DATA_DIR
    if os.path.exists(data_dir):
        for name in os.listdir(data_dir):
            full_path = os.path.join(data_dir, name)
            if os.path.isfile(full_path):
                with open(full_path, "rb") as f:
                    files[name] = f.read()
    return files


def run_pipeline(
    project_id: str,
    files: dict[str, bytes],
    demo_mode: bool,
    on_progress: Optional[Callable[[str], None]] = None,
) -> RunResult:
    """
    Run the 10-step BRD extraction and verification pipeline.
    Contract locked signature.
    Records per-stage timings and counts in result.notes.
    Catches external service exceptions and appends plain-language notes.
    """
    start_total = time.time()
    run_id = uuid.uuid4().hex[:8]
    notes: list[str] = []

    def notify(msg: str):
        notes.append(msg)
        if on_progress:
            on_progress(msg)

    notify(f"Starting run {run_id} (mode: {'demo' if demo_mode else 'live'})")

    # Step 1: Register artifacts
    t0 = time.time()
    artifacts: list[ArtifactInfo] = []
    for fname, data in files.items():
        kind, mime = _detect_kind(fname)
        artifacts.append(
            ArtifactInfo(
                file_name=fname,
                kind=kind,
                mime_type=mime,
                size_bytes=len(data),
            )
        )
    t_art = time.time() - t0
    notify(f"Registered {len(artifacts)} source artifacts in {t_art:.2f}s")

    gcs_uris: dict[str, str] = {}
    if not demo_mode:
        # Step 2: Upload raw files to Cloud Storage
        t0 = time.time()
        try:
            from app import storage
            notify("Uploading raw files to Cloud Storage...")
            gcs_uris = storage.upload_files(project_id, run_id, files, artifacts)
            t_storage = time.time() - t0
            notify(f"Uploaded {len(gcs_uris)} files to Cloud Storage in {t_storage:.2f}s")
        except Exception as e:
            notify(f"Cloud Storage upload warning: {e}")

    # Step 3: Extract requirements
    t0 = time.time()
    extracted_reqs = []
    if demo_mode:
        from app import gemini_client
        notify("Loading extraction from demo cache / mock...")
        extracted_reqs = gemini_client.demo_extraction(files)
    else:
        from app import gemini_client
        notify("Extracting requirements with Gemini on Vertex AI...")
        try:
            extracted_reqs = gemini_client.extract_requirements(files, gcs_uris, artifacts)
        except Exception as e:
            notify(f"Live Gemini extraction failed: {e}. Falling back to demo mode.")
            extracted_reqs = gemini_client.demo_extraction(files)

    t_extract = time.time() - t0
    notify(f"Extracted {len(extracted_reqs)} raw requirements in {t_extract:.2f}s")

    # Step 4: Verify evidence (Always real)
    t0 = time.time()
    notify("Verifying evidence across sources...")
    verified_reqs = verify.verify_requirements(extracted_reqs, files)
    v_count = sum(1 for r in verified_reqs if r.verification_status == "verified")
    t_verify = time.time() - t0
    notify(f"Verification complete in {t_verify:.2f}s: {v_count}/{len(verified_reqs)} requirements verified")

    # Step 5: Gap check (Always real)
    t0 = time.time()
    notify("Checking requirement coverage and identifying gaps...")
    gap_questions = gaps.coverage_gaps(verified_reqs)
    t_gaps = time.time() - t0
    notify(f"Identified {len(gap_questions)} open clarification questions in {t_gaps:.2f}s")

    # Step 6 & 7: Past requirements & conflict detection
    past_reqs: list[dict] = []
    if not demo_mode:
        try:
            from app import bq
            past_reqs = bq.load_active_requirements(project_id)
            if past_reqs:
                notify(f"Loaded {len(past_reqs)} past requirements from BigQuery project memory")
        except Exception as e:
            notify(f"BigQuery past requirements note: {e}")

    t0 = time.time()
    from app import gemini_client
    conflicts = gemini_client.detect_conflicts(extracted_reqs, past_reqs)
    t_conflicts = time.time() - t0
    if conflicts:
        notify(f"Detected {len(conflicts)} conflict(s) in {t_conflicts:.2f}s")
    else:
        notify(f"Conflict check completed in {t_conflicts:.2f}s (0 conflicts)")

    # Step 8: Save run to BigQuery (Live mode)
    result = RunResult(
        run_id=run_id,
        project_id=project_id,
        mode="demo" if demo_mode else "live",
        artifacts=artifacts,
        requirements=verified_reqs,
        conflicts=conflicts,
        gaps=gap_questions,
        notes=notes,
    )

    if not demo_mode:
        t0 = time.time()
        try:
            from app import bq
            bq.save_run(result, config.GEMINI_MODEL)
            t_bq = time.time() - t0
            notify(f"Run saved to BigQuery in {t_bq:.2f}s")
        except Exception as e:
            notify(f"BigQuery save note: {e}")

        # Step 9: Save cache for demo mode
        try:
            gemini_client.save_cache(list(files.keys()), extracted_reqs)
        except Exception:
            pass

    total_duration = time.time() - start_total
    notify(f"Pipeline finished in {total_duration:.2f}s (Total)")
    return result


def set_review_status(
    result: RunResult,
    requirement_id: str,
    status: str,
) -> RunResult:
    """Set review status (pending, approved, rejected) for a requirement."""
    for req in result.requirements:
        if req.id == requirement_id:
            req.review_status = status  # type: ignore
            break
    return result
