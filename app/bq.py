from datetime import datetime, timezone
from typing import Any, Optional
from app import config
from app.schemas import RunResult


def ensure_tables() -> None:
    """
    Ensure the dataset {BQ_DATASET} and six BigQuery tables exist:
    runs, artifacts, requirements, evidence, conflicts, gaps.
    Follows PRD Section 10.3 exact column names and types.
    """
    if not config.GCP_PROJECT_ID:
        raise RuntimeError("GCP_PROJECT_ID is not configured in environment or .env")

    from google.cloud import bigquery

    client = bigquery.Client(project=config.GCP_PROJECT_ID)
    dataset_id = f"{config.GCP_PROJECT_ID}.{config.BQ_DATASET}"

    # Ensure dataset exists
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = config.GCP_LOCATION
    client.create_dataset(dataset, exists_ok=True)

    ddl_statements = [
        f"""
        CREATE TABLE IF NOT EXISTS `{dataset_id}.runs` (
          run_id STRING,
          project_id STRING,
          mode STRING,
          model STRING,
          created_at TIMESTAMP
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS `{dataset_id}.artifacts` (
          run_id STRING,
          project_id STRING,
          file_name STRING,
          kind STRING,
          mime_type STRING,
          gcs_uri STRING,
          size_bytes INT64
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS `{dataset_id}.requirements` (
          project_id STRING,
          run_id STRING,
          display_id STRING,
          text STRING,
          type STRING,
          verification_status STRING,
          review_status STRING,
          created_at TIMESTAMP
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS `{dataset_id}.evidence` (
          project_id STRING,
          run_id STRING,
          display_id STRING,
          file_name STRING,
          kind STRING,
          quote STRING,
          page INT64,
          line INT64,
          box_ymin INT64,
          box_xmin INT64,
          box_ymax INT64,
          box_xmax INT64,
          verified BOOL,
          verify_note STRING
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS `{dataset_id}.conflicts` (
          project_id STRING,
          run_id STRING,
          requirement_ids ARRAY<STRING>,
          description STRING,
          severity STRING,
          resolved BOOL
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS `{dataset_id}.gaps` (
          project_id STRING,
          run_id STRING,
          category STRING,
          question STRING,
          answer STRING
        );
        """,
    ]

    for ddl in ddl_statements:
        client.query(ddl).result()


def load_active_requirements(project_id: str) -> list[dict[str, Any]]:
    """
    Load past verified, non-rejected requirements for the given project from BigQuery.
    IDs are formatted as f"{run_id}:{display_id}" to prevent collision in conflict checks.
    """
    if not config.GCP_PROJECT_ID:
        return []

    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=config.GCP_PROJECT_ID)
        dataset_id = f"{config.GCP_PROJECT_ID}.{config.BQ_DATASET}"
        query = f"""
        SELECT run_id, display_id, text, type
        FROM `{dataset_id}.requirements`
        WHERE project_id = @project_id
          AND verification_status = 'verified'
          AND review_status != 'rejected'
        ORDER BY created_at DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("project_id", "STRING", project_id)
            ]
        )
        rows = client.query(query, job_config=job_config).result()
        return [
            {
                "id": f"{row.run_id}:{row.display_id}",
                "display_id": row.display_id,
                "text": row.text,
                "type": row.type,
            }
            for row in rows
        ]
    except Exception:
        return []


def save_run(result: RunResult, model_name: Optional[str] = None) -> None:
    """
    Insert RunResult rows into BigQuery tables.
    Skips inserting into conflicts or gaps when empty to avoid BigQuery errors.
    Unpacks box_2d into box_ymin, box_xmin, box_ymax, box_xmax.
    """
    if not config.GCP_PROJECT_ID:
        return

    from google.cloud import bigquery
    client = bigquery.Client(project=config.GCP_PROJECT_ID)
    dataset_id = f"{config.GCP_PROJECT_ID}.{config.BQ_DATASET}"
    now = datetime.now(timezone.utc).isoformat()
    chosen_model = model_name or config.GEMINI_MODEL

    # 1. Insert run
    run_row = {
        "run_id": result.run_id,
        "project_id": result.project_id,
        "mode": result.mode,
        "model": chosen_model,
        "created_at": now,
    }
    client.insert_rows_json(f"{dataset_id}.runs", [run_row])

    # 2. Insert artifacts (if any)
    if result.artifacts:
        art_rows = [
            {
                "run_id": result.run_id,
                "project_id": result.project_id,
                "file_name": art.file_name,
                "kind": art.kind,
                "mime_type": art.mime_type,
                "gcs_uri": art.gcs_uri,
                "size_bytes": art.size_bytes,
            }
            for art in result.artifacts
        ]
        client.insert_rows_json(f"{dataset_id}.artifacts", art_rows)

    # 3. Insert requirements
    if result.requirements:
        req_rows = [
            {
                "project_id": result.project_id,
                "run_id": result.run_id,
                "display_id": req.id,
                "text": req.text,
                "type": req.type,
                "verification_status": req.verification_status,
                "review_status": req.review_status,
                "created_at": now,
            }
            for req in result.requirements
        ]
        client.insert_rows_json(f"{dataset_id}.requirements", req_rows)

    # 4. Insert evidence
    ev_rows = []
    for req in result.requirements:
        for ev in req.evidence:
            ymin, xmin, ymax, xmax = (None, None, None, None)
            if ev.box_2d and len(ev.box_2d) == 4:
                ymin, xmin, ymax, xmax = ev.box_2d[0], ev.box_2d[1], ev.box_2d[2], ev.box_2d[3]

            ev_rows.append(
                {
                    "project_id": result.project_id,
                    "run_id": result.run_id,
                    "display_id": req.id,
                    "file_name": ev.file_name,
                    "kind": ev.kind,
                    "quote": ev.quote,
                    "page": ev.page,
                    "line": ev.line,
                    "box_ymin": ymin,
                    "box_xmin": xmin,
                    "box_ymax": ymax,
                    "box_xmax": xmax,
                    "verified": ev.verified,
                    "verify_note": ev.verify_note,
                }
            )
    if ev_rows:
        client.insert_rows_json(f"{dataset_id}.evidence", ev_rows)

    # 5. Insert conflicts (only if non-empty)
    if result.conflicts:
        conf_rows = [
            {
                "project_id": result.project_id,
                "run_id": result.run_id,
                "requirement_ids": c.requirement_ids,
                "description": c.description,
                "severity": c.severity,
                "resolved": c.resolved,
            }
            for c in result.conflicts
        ]
        client.insert_rows_json(f"{dataset_id}.conflicts", conf_rows)

    # 6. Insert gaps (only if non-empty)
    if result.gaps:
        gap_rows = [
            {
                "project_id": result.project_id,
                "run_id": result.run_id,
                "category": g.category,
                "question": g.question,
                "answer": g.answer,
            }
            for g in result.gaps
        ]
        client.insert_rows_json(f"{dataset_id}.gaps", gap_rows)
