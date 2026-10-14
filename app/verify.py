import re
from typing import Optional
import pymupdf
from PIL import Image
import io

from app.schemas import Evidence, Requirement, ExtractedRequirement


def _normalize_text(s: Optional[str]) -> str:
    """
    Normalize text for strict verbatim matching:
    - Lowercase
    - Replace smart quotes (‘, ’, “, ”) with standard single/double quotes (' / ")
    - Replace common PDF ligatures (ﬁ -> fi, ﬂ -> fl, ﬀ -> ff, ﬃ -> ffi, ﬄ -> ffl)
    - Collapse all whitespace (spaces, tabs, newlines) into a single space
    """
    if s is None:
        return ""
    # Smart quotes to standard quotes
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    # Ligatures
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff").replace("ﬃ", "ffi").replace("ﬄ", "ffl")
    # Lowercase & collapse whitespace
    return re.sub(r"\s+", " ", s.strip().lower())


def verify_text_evidence(ev: Evidence, file_bytes: bytes) -> tuple[bool, str, Optional[int]]:
    """
    Check if quote appears in the text source (smart quotes, ligatures, whitespace, and case normalized).
    Returns (verified, note, detected_line_number).
    """
    if ev.quote is None or not ev.quote.strip():
        return False, "Missing quote for text evidence", None

    try:
        text_content = file_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        return False, f"Failed to decode text: {e}", None

    lines = text_content.splitlines()
    norm_quote = _normalize_text(ev.quote)
    if not norm_quote:
        return False, "Quote contains no valid content after normalization", None

    # 1. Direct line check (check claimed line first if provided)
    if ev.line is not None and 1 <= ev.line <= len(lines):
        if norm_quote in _normalize_text(lines[ev.line - 1]):
            return True, f"Found on line {ev.line}", ev.line

    # 2. Search individual lines
    for idx, line in enumerate(lines, start=1):
        if norm_quote in _normalize_text(line):
            return True, f"Found on line {idx}", idx

    # 3. Multi-line search across consecutive lines
    for i in range(len(lines)):
        accumulated: list[str] = []
        for j in range(i, min(len(lines), i + 6)):
            accumulated.append(lines[j])
            chunk_norm = _normalize_text(" ".join(accumulated))
            if norm_quote in chunk_norm:
                start_line = i + 1
                return True, f"Found across lines {start_line}-{j+1}", start_line

    return False, "Quote not found in text file", None


def verify_pdf_evidence(ev: Evidence, file_bytes: bytes) -> tuple[bool, str, Optional[int]]:
    """
    Check if quote appears in PDF using PyMuPDF.
    Try claimed page first, then search all pages.
    """
    if ev.quote is None or not ev.quote.strip():
        return False, "Missing quote for PDF evidence", None

    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        return False, f"Failed to open PDF: {e}", None

    norm_quote = _normalize_text(ev.quote)
    if not norm_quote:
        return False, "Quote contains no valid content after normalization", None

    # Order of pages to check: claimed page first (1-based), then others
    page_indices = list(range(len(doc)))
    if ev.page is not None and 1 <= ev.page <= len(doc):
        claimed_idx = ev.page - 1
        page_indices.remove(claimed_idx)
        page_indices.insert(0, claimed_idx)

    for p_idx in page_indices:
        page = doc[p_idx]
        page_num = p_idx + 1

        # 1. Exact PyMuPDF search_for with raw quote
        hits = page.search_for(ev.quote.strip())
        if hits:
            return True, f"Found on page {page_num}", page_num

        # 2. PyMuPDF search_for with normalized smart quotes
        cleaned_quote = ev.quote.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').strip()
        if cleaned_quote != ev.quote.strip():
            hits = page.search_for(cleaned_quote)
            if hits:
                return True, f"Found on page {page_num}", page_num

        # 3. Normalized page text comparison (handles ligatures, line wraps, smart quotes)
        page_text = page.get_text()
        norm_page_text = _normalize_text(page_text)
        if norm_quote in norm_page_text:
            return True, f"Found in page text on page {page_num}", page_num

    return False, "Quote not found in PDF", None


def verify_image_evidence(ev: Evidence, file_bytes: bytes) -> tuple[bool, str]:
    """
    Validate bounding box: 4 ints [ymin, xmin, ymax, xmax], 0-1000, positive area.
    """
    box = ev.box_2d
    if not box or len(box) != 4:
        return False, "box_2d must be [ymin, xmin, ymax, xmax]"

    ymin, xmin, ymax, xmax = box
    for coord in box:
        if not isinstance(coord, int) or coord < 0 or coord > 1000:
            return False, "box_2d coordinates must be integers between 0 and 1000"

    if ymin >= ymax or xmin >= xmax:
        return False, "box_2d must have positive area (ymin < ymax, xmin < xmax)"

    # Validate image can be loaded
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
    except Exception as e:
        return False, f"Invalid image file: {e}"

    return True, f"Valid box {box}"


def verify_requirements(
    extracted_reqs: list[ExtractedRequirement],
    files: dict[str, bytes],
) -> list[Requirement]:
    """
    Verify every evidence item in the extracted requirements.
    Derives verification_status: 'verified' if at least one evidence item passes,
    otherwise 'unverified'. Never trusts Gemini's claims.
    """
    verified_reqs: list[Requirement] = []

    for req in extracted_reqs:
        verified_evidence: list[Evidence] = []
        has_at_least_one_verified = False

        for ev in req.evidence:
            ev_data = ev.model_dump()
            evidence_obj = Evidence(**ev_data)
            file_bytes = files.get(ev.file_name)

            if not file_bytes:
                evidence_obj.verified = False
                evidence_obj.verify_note = f"File {ev.file_name} not found in uploaded files"
            elif ev.kind == "text":
                ok, note, line = verify_text_evidence(evidence_obj, file_bytes)
                evidence_obj.verified = ok
                evidence_obj.verify_note = note
                if line is not None:
                    evidence_obj.line = line
            elif ev.kind == "pdf":
                ok, note, page = verify_pdf_evidence(evidence_obj, file_bytes)
                evidence_obj.verified = ok
                evidence_obj.verify_note = note
                if page is not None:
                    evidence_obj.page = page
            elif ev.kind == "image":
                ok, note = verify_image_evidence(evidence_obj, file_bytes)
                evidence_obj.verified = ok
                evidence_obj.verify_note = note
            else:
                evidence_obj.verified = False
                evidence_obj.verify_note = f"Unknown evidence kind: {ev.kind}"

            if evidence_obj.verified:
                has_at_least_one_verified = True

            verified_evidence.append(evidence_obj)

        req_status = "verified" if has_at_least_one_verified else "unverified"

        verified_reqs.append(
            Requirement(
                id=req.id,
                text=req.text,
                type=req.type,
                evidence=verified_evidence,
                verification_status=req_status,
                review_status="pending",
            )
        )

    return verified_reqs
