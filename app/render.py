import io
from typing import Any, Optional
import pymupdf  # type: ignore # pyrefly: ignore
from PIL import Image, ImageDraw  # type: ignore # pyrefly: ignore
from app.schemas import Evidence


def render_evidence(ev: Evidence, file_bytes: Optional[bytes]) -> dict[str, Any]:
    """
    Renders evidence visually for the UI:
    - image: PIL Image with crisp red bounding box (converted from 0-1000 normalized to pixels)
    - pdf: PIL Image of page with yellow highlight annotation rendered at 2x resolution
    - text: snippet with 2-3 lines of surrounding context, 1-based line numbers, matched line prefixed with >>
    - missing: text fallback
    Returns dict: {"type": ..., "image": ..., "text": ..., "caption": ..., "verified": ..., "verify_note": ...}
    """
    if not file_bytes:
        return {
            "type": "text",
            "image": None,
            "text": f"File '{ev.file_name}' not available in session.\nEvidence: {ev.quote or ev.box_2d}",
            "caption": f"{ev.file_name} (offline)",
            "verified": ev.verified,
            "verify_note": ev.verify_note,
        }

    if ev.kind == "image":
        try:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            w, h = img.size
            if ev.box_2d and len(ev.box_2d) == 4:
                ymin, xmin, ymax, xmax = ev.box_2d
                # Convert 0-1000 normalized to pixel coordinates
                left = int(xmin * w / 1000)
                top = int(ymin * h / 1000)
                right = int(xmax * w / 1000)
                bottom = int(ymax * h / 1000)

                draw = ImageDraw.Draw(img)
                # Draw crisp red rectangle with width=4
                draw.rectangle([left, top, right, bottom], outline="red", width=4)

            return {
                "type": "image",
                "image": img,
                "text": None,
                "caption": f"{ev.file_name} (region: {ev.box_2d})",
                "verified": ev.verified,
                "verify_note": ev.verify_note,
            }
        except Exception as e:
            return {
                "type": "text",
                "image": None,
                "text": f"Error rendering image: {e}",
                "caption": ev.file_name,
                "verified": False,
                "verify_note": str(e),
            }

    elif ev.kind == "pdf":
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            p_idx = (ev.page - 1) if (ev.page is not None and 1 <= ev.page <= len(doc)) else 0
            page = doc[p_idx]

            # Locate quote and highlight matching rects with yellow highlight annotation
            if ev.quote:
                clean_q = ev.quote.strip()
                hits = page.search_for(clean_q)
                if not hits:
                    # Try smart quotes replacement
                    norm_q = clean_q.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
                    hits = page.search_for(norm_q)
                if not hits:
                    words = clean_q.split()
                    if len(words) >= 4:
                        hits = page.search_for(" ".join(words[:4]))

                for rect in hits:
                    annot = page.add_highlight_annot(rect)
                    annot.set_colors(stroke=(1.0, 0.9, 0.0))  # yellow highlight
                    annot.update()

            # Render page at 2x resolution for crisp high-DPI display in Streamlit
            mat = pymupdf.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

            return {
                "type": "image",
                "image": img,
                "text": None,
                "caption": f"{ev.file_name} (Page {p_idx + 1})",
                "verified": ev.verified,
                "verify_note": ev.verify_note,
            }
        except Exception as e:
            return {
                "type": "text",
                "image": None,
                "text": f"Error rendering PDF: {e}",
                "caption": ev.file_name,
                "verified": False,
                "verify_note": str(e),
            }

    elif ev.kind == "text":
        try:
            text_str = file_bytes.decode("utf-8", errors="replace")
            lines = text_str.splitlines()
            target_line = ev.line if (ev.line is not None and 1 <= ev.line <= len(lines)) else 1

            start_idx = max(0, target_line - 3)
            end_idx = min(len(lines), target_line + 2)

            snippet_lines = []
            for i in range(start_idx, end_idx):
                line_no = i + 1
                prefix = ">> " if line_no == target_line else "   "
                snippet_lines.append(f"{prefix}{line_no:3d} | {lines[i]}")

            return {
                "type": "text",
                "image": None,
                "text": "\n".join(snippet_lines),
                "caption": f"{ev.file_name} (Line {target_line})",
                "verified": ev.verified,
                "verify_note": ev.verify_note,
            }
        except Exception as e:
            return {
                "type": "text",
                "image": None,
                "text": f"Error rendering text: {e}",
                "caption": ev.file_name,
                "verified": False,
                "verify_note": str(e),
            }

    return {
        "type": "text",
        "image": None,
        "text": f"Unknown evidence kind: {ev.kind}",
        "caption": ev.file_name,
        "verified": False,
        "verify_note": "Unknown evidence kind",
    }
