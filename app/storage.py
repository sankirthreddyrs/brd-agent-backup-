import os
from typing import Optional
from app import config
from app.schemas import ArtifactInfo


def upload_files(
    project_id: str,
    run_id: str,
    files: dict[str, bytes],
    artifacts: Optional[list[ArtifactInfo]] = None,
) -> dict[str, str]:
    """
    Upload raw files to Google Cloud Storage.
    Layout: gs://{GCS_BUCKET}/projects/{project_id}/runs/{run_id}/{file_name}
    Sets content_type=artifact.mime_type and sets artifact.gcs_uri if artifacts list is provided.
    Returns dict mapping file_name -> gcs_uri.
    Raises a clean, descriptive RuntimeError if GCS_BUCKET is missing or upload fails.
    """
    if not config.GCS_BUCKET:
        raise RuntimeError("GCS_BUCKET is not set in environment or .env. Cannot upload to Cloud Storage.")

    from google.cloud import storage

    client = storage.Client(project=config.GCP_PROJECT_ID)
    bucket = client.bucket(config.GCS_BUCKET)
    gcs_map: dict[str, str] = {}

    art_by_name = {a.file_name: a for a in artifacts} if artifacts else {}

    for file_name, file_bytes in files.items():
        try:
            blob_path = f"projects/{project_id}/runs/{run_id}/{file_name}"
            blob = bucket.blob(blob_path)

            mime_type = "application/octet-stream"
            if file_name in art_by_name:
                mime_type = art_by_name[file_name].mime_type
            else:
                lower = file_name.lower()
                if lower.endswith((".jpg", ".jpeg")):
                    mime_type = "image/jpeg"
                elif lower.endswith(".png"):
                    mime_type = "image/png"
                elif lower.endswith(".pdf"):
                    mime_type = "application/pdf"
                elif lower.endswith(".txt"):
                    mime_type = "text/plain"

            blob.upload_from_string(file_bytes, content_type=mime_type)
            uri = f"gs://{config.GCS_BUCKET}/{blob_path}"
            gcs_map[file_name] = uri

            if file_name in art_by_name:
                art_by_name[file_name].gcs_uri = uri
        except Exception as e:
            raise RuntimeError(f"Failed to upload '{file_name}' to gs://{config.GCS_BUCKET}/{blob_path}: {e}") from e

    return gcs_map
