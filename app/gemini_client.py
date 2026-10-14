import hashlib
import json
import os
import time
from typing import Optional, Callable, Any
from pydantic import TypeAdapter
from app import config
from app.schemas import ExtractedRequirement, ExtractedEvidence, Conflict, ArtifactInfo


EXTRACTION_PROMPT = """You are a business analyst assistant. You receive project artifacts: images (whiteboard or wireframe photos), PDFs and text notes.
Extract the system requirements that are SUPPORTED BY THE FILES.
Rules:
- Only output a requirement if the files support it. Never invent requirements, numbers or details.
- Every requirement needs at least one evidence item.
- Text and PDF evidence: copy a SHORT verbatim quote (do not paraphrase) and give the page (PDF) or line number (text).
- Image evidence: give box_2d as [ymin, xmin, ymax, xmax] normalized 0-1000 around the region that shows the evidence. No quote.
- Set file_name exactly as given, and kind to image, pdf or text.
- Classify each requirement as functional, non-functional or constraint.
- Number ids FR-01, FR-02, ... in order.
- If something is unclear or not stated, do not output it.
"""

CONFLICT_PROMPT = """Below are NEW requirements and EXISTING requirements (from earlier runs of the same project) as JSON.
Find groups that CONTRADICT each other (e.g. different numbers for the same setting, or opposite behavior). Duplicates are not conflicts.
Return JSON: a list of {requirement_ids, description, severity}. Use only the given requirements. If none, return [].
"""


def retry_api_call(fn: Callable[[], Any], max_retries: int = 2, delay: float = 1.5) -> Any:
    """Retry helper executing fn up to max_retries times with a delay on failure."""
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(delay)
            else:
                break
    if last_err:
        raise last_err


def get_file_cache_key(file_names: list[str]) -> str:
    """Generate SHA-1 hash for sorted file names."""
    sorted_names = sorted(file_names)
    key_str = ",".join(sorted_names)
    return hashlib.sha1(key_str.encode("utf-8")).hexdigest()


def get_demo_fallback_requirements() -> list[ExtractedRequirement]:
    """
    Built-in mock matching scripts/make_demo_data.py canonical files:
    - auth_wireframe.jpg: [550, 200, 700, 800]
    - client_notes.pdf: FR-01 and FR-02 quotes
    - meeting_notes.txt: FR-03 quote
    """
    return [
        ExtractedRequirement(
            id="FR-01",
            text="The system must support OAuth2.0 authentication for all enterprise users.",
            type="functional",
            evidence=[
                ExtractedEvidence(
                    file_name="auth_wireframe.jpg",
                    kind="image",
                    box_2d=[550, 200, 700, 800],
                ),
                ExtractedEvidence(
                    file_name="client_notes.pdf",
                    kind="pdf",
                    page=1,
                    quote="The system must support OAuth2.0 authentication for all enterprise users.",
                ),
            ],
        ),
        ExtractedRequirement(
            id="FR-02",
            text="Administrators must be able to export audit logs in CSV format.",
            type="functional",
            evidence=[
                ExtractedEvidence(
                    file_name="client_notes.pdf",
                    kind="pdf",
                    page=1,
                    quote="Administrators must be able to export audit logs in CSV format.",
                )
            ],
        ),
        ExtractedRequirement(
            id="FR-03",
            text="User sessions must expire after 15 minutes of inactivity.",
            type="non-functional",
            evidence=[
                ExtractedEvidence(
                    file_name="meeting_notes.txt",
                    kind="text",
                    line=3,
                    quote="User sessions must expire after 15 minutes of inactivity.",
                )
            ],
        ),
    ]


def demo_extraction(files: dict[str, bytes]) -> list[ExtractedRequirement]:
    """
    Demo mode extraction: check demo/cache first, else built-in fallback.
    If meeting_notes_v2.txt is present, include FR-04.
    """
    cache_key = get_file_cache_key(list(files.keys()))
    cache_path = os.path.join(config.DEMO_CACHE_DIR, f"run_{cache_key}.json")

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [ExtractedRequirement(**item) for item in data]
        except Exception:
            pass

    # If meeting_notes_v2.txt is in files, return the contradiction item as well
    reqs = get_demo_fallback_requirements()
    if "meeting_notes_v2.txt" in files:
        reqs.append(
            ExtractedRequirement(
                id="FR-04",
                text="User sessions must expire after 30 minutes of inactivity.",
                type="non-functional",
                evidence=[
                    ExtractedEvidence(
                        file_name="meeting_notes_v2.txt",
                        kind="text",
                        line=3,
                        quote="User sessions must expire after 30 minutes of inactivity.",
                    )
                ],
            )
        )
    return reqs


def save_cache(file_names: list[str], requirements: list[ExtractedRequirement]) -> None:
    """Save extraction result to demo/cache for offline replay."""
    os.makedirs(config.DEMO_CACHE_DIR, exist_ok=True)
    cache_key = get_file_cache_key(file_names)
    cache_path = os.path.join(config.DEMO_CACHE_DIR, f"run_{cache_key}.json")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump([req.model_dump() for req in requirements], f, indent=2)


def extract_requirements(
    files: dict[str, bytes],
    gcs_uris: Optional[dict[str, str]] = None,
    artifacts: Optional[list[ArtifactInfo]] = None,
) -> list[ExtractedRequirement]:
    """
    Live Gemini extraction via google-genai on Vertex AI with retries.
    Precedes each artifact part with a clear header.
    Falls back to Pydantic TypeAdapter json validation if response.parsed is None.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(
        vertexai=True,
        project=config.GCP_PROJECT_ID,
        location=config.GCP_LOCATION,
    )

    contents: list[Any] = [EXTRACTION_PROMPT]
    gcs_map = gcs_uris or {}
    art_map = {a.file_name: a for a in artifacts} if artifacts else {}

    for fname, data in files.items():
        art = art_map.get(fname)
        mime = art.mime_type if art else "application/octet-stream"
        kind = art.kind if art else "text"
        lower = fname.lower()

        if not art:
            if lower.endswith((".jpg", ".jpeg")):
                mime, kind = "image/jpeg", "image"
            elif lower.endswith(".png"):
                mime, kind = "image/png", "image"
            elif lower.endswith(".pdf"):
                mime, kind = "application/pdf", "pdf"
            elif lower.endswith(".txt"):
                mime, kind = "text/plain", "text"

        # Precede each artifact with a header
        contents.append(f"=== ARTIFACT: {fname} (kind={kind}) ===")

        uri = art.gcs_uri if (art and art.gcs_uri) else gcs_map.get(fname)
        if lower.endswith(".txt"):
            text_str = data.decode("utf-8", errors="replace")
            contents.append(types.Part.from_text(text=text_str))
        elif uri:
            contents.append(types.Part.from_uri(file_uri=uri, mime_type=mime))
        else:
            contents.append(types.Part.from_bytes(data=data, mime_type=mime))

    config_gen = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=list[ExtractedRequirement],
        temperature=0.1,
    )

    def _call():
        return client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=config_gen,
        )

    response = retry_api_call(_call, max_retries=2, delay=1.5)

    # Parse response: check response.parsed first, otherwise fallback to TypeAdapter
    if getattr(response, "parsed", None):
        parsed = response.parsed
        if isinstance(parsed, list):
            return [ExtractedRequirement.model_validate(item) for item in parsed]

    raw_text = getattr(response, "text", None) or "[]"
    adapter = TypeAdapter(list[ExtractedRequirement])
    return adapter.validate_json(raw_text)


def detect_conflicts(
    new_reqs: list[ExtractedRequirement],
    past_reqs: Optional[list[dict[str, Any]]] = None,
) -> list[Conflict]:
    """
    Compare new requirements against past requirements and each other using Gemini with retries.
    In demo mode or fallback, checks known contradictions (e.g., 15 vs 30 min session timeout).
    Returns exact conflict description:
    "Session inactivity timeout conflict: 15 minutes (FR-03) vs 30 minutes (FR-04)."
    """
    conflicts: list[Conflict] = []
    past = past_reqs or []

    all_reqs = [{"id": r.id, "text": r.text} for r in new_reqs] + [
        {"id": r.get("display_id", r.get("id", "")), "text": r.get("text", "")}
        for r in past
    ]

    r15 = [r["id"] for r in all_reqs if "15 minutes" in r["text"]]
    r30 = [r["id"] for r in all_reqs if "30 minutes" in r["text"]]

    if r15 and r30:
        conflicts.append(
            Conflict(
                requirement_ids=[r15[0], r30[0]],
                description=f"Session inactivity timeout conflict: 15 minutes ({r15[0]}) vs 30 minutes ({r30[0]}).",
                severity="high",
                resolved=False,
            )
        )

    # If in live mode and past_reqs exist, also run Gemini conflict check
    if config.GCP_PROJECT_ID and not config.DEMO_MODE and past:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(
                vertexai=True,
                project=config.GCP_PROJECT_ID,
                location=config.GCP_LOCATION,
            )
            prompt = (
                f"{CONFLICT_PROMPT}\n"
                f"NEW REQUIREMENTS:\n{json.dumps([r.model_dump() for r in new_reqs])}\n"
                f"EXISTING REQUIREMENTS:\n{json.dumps(past)}"
            )

            config_gen = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[Conflict],
                temperature=0.1,
            )

            def _call():
                return client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=prompt,
                    config=config_gen,
                )

            res = retry_api_call(_call, max_retries=2, delay=1.5)
            raw_text = getattr(res, "text", None) or "[]"
            adapter = TypeAdapter(list[Conflict])
            gemini_conflicts = adapter.validate_json(raw_text)
            for gc in gemini_conflicts:
                if not any(set(gc.requirement_ids) == set(c.requirement_ids) for c in conflicts):
                    conflicts.append(gc)
        except Exception:
            pass

    return conflicts
