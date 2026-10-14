"""
Generate clean, realistic canonical demo files in demo/data/ for BRD Agent:
- auth_wireframe.jpg: Pillow wireframe with Continue with Google (OAuth 2.0)
- client_notes.pdf: PyMuPDF PDF with FR-01 & FR-02 verbatim text (NO retention/privacy/gdpr)
- meeting_notes.txt: Multi-line notes with FR-03 verbatim line
- meeting_notes_v2.txt: Stage-2 follow-up notes with FR-04 verbatim contradiction
"""
import os
import pymupdf
from PIL import Image, ImageDraw, ImageFont


def make_auth_wireframe(output_path: str):
    # Standard dimensions: 1000 x 1000 for intuitive 0-1000 normalized coordinates
    w, h = 1000, 1000
    img = Image.new("RGB", (w, h), color="#F8F9FA")
    draw = ImageDraw.Draw(img)

    # Wireframe container box
    draw.rectangle([100, 80, 900, 920], outline="#4A5568", width=4, fill="#FFFFFF")

    # Header / Title
    draw.text((380, 140), "Enterprise Portal", fill="#1A202C")
    draw.text((420, 180), "Sign in to continue", fill="#718096")

    # Username Field
    draw.text((200, 240), "Username / Email", fill="#2D3748")
    draw.rectangle([200, 270, 800, 340], outline="#CBD5E0", width=3, fill="#F7FAFC")
    draw.text((220, 295), "user@enterprise.com", fill="#A0AEC0")

    # Password Field
    draw.text((200, 370), "Password", fill="#2D3748")
    draw.rectangle([200, 400, 800, 470], outline="#CBD5E0", width=3, fill="#F7FAFC")
    draw.text((220, 425), "••••••••••••", fill="#A0AEC0")

    # Standard "Sign In" Button
    draw.rectangle([200, 490, 800, 550], fill="#3182CE")
    draw.text((460, 510), "Sign In", fill="#FFFFFF")

    # "OR" divider line
    draw.line([200, 580, 460, 580], fill="#E2E8F0", width=2)
    draw.text((485, 570), "OR", fill="#A0AEC0")
    draw.line([540, 580, 800, 580], fill="#E2E8F0", width=2)

    # "Continue with Google (OAuth 2.0)" Button
    # Bounding box coordinates: [ymin: 620, xmin: 200, ymax: 720, xmax: 800]
    # Let's place it at ymin=550, xmin=200, ymax=700, xmax=800 as targeted in the prompt:
    # "inside a well-defined bounding box (e.g., normalized [ymin, xmin, ymax, xmax] around [550, 200, 700, 800])"
    ymin, xmin, ymax, xmax = 550, 200, 700, 800
    draw.rectangle([xmin, ymin, xmax, ymax], outline="#4285F4", width=4, fill="#EBF8FF")
    draw.text((310, 615), "Continue with Google (OAuth 2.0)", fill="#2B6CB0")

    # Footer note
    draw.text((320, 820), "Protected by Enterprise Security Policies", fill="#A0AEC0")

    img.save(output_path, "JPEG", quality=95)
    print(f"Created {output_path} (box: [{ymin}, {xmin}, {ymax}, xmax: {xmax}])")


def make_client_notes_pdf(output_path: str):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4 size in points

    # Document Title
    page.insert_text(
        pymupdf.Point(50, 70),
        "Enterprise Architecture - Client Requirements Notes",
        fontsize=16,
        color=(0.1, 0.2, 0.4),
    )
    page.insert_text(
        pymupdf.Point(50, 95),
        "Project: Enterprise Portal Modernization | Stakeholder Interview Summary",
        fontsize=10,
        color=(0.4, 0.4, 0.4),
    )

    content_lines = [
        "1. Executive Overview",
        "The client seeks to consolidate enterprise identity and streamline administrative compliance.",
        "",
        "2. Key Requirements",
        "The system must support OAuth2.0 authentication for all enterprise users.",
        "Administrators must be able to export audit logs in CSV format.",
        "",
        "3. System Specifications & Targets",
        "The infrastructure should be provisioned for 500 concurrent users during peak operations.",
        "All outbound reports must be generated with timestamp and origin identifiers.",
    ]

    y = 140
    for line in content_lines:
        if line.startswith(("1.", "2.", "3.")):
            page.insert_text(pymupdf.Point(50, y), line, fontsize=12, color=(0.1, 0.1, 0.1))
            y += 25
        elif line == "":
            y += 10
        else:
            page.insert_text(pymupdf.Point(70, y), line, fontsize=11, color=(0.2, 0.2, 0.2))
            y += 22

    doc.save(output_path)
    doc.close()
    print(f"Created {output_path}")


def make_meeting_notes_txt(output_path: str):
    content = """Sprint 1 Kickoff Meeting Notes
Date: 2026-10-14 | Attendees: Architecture Team, Product Owner, Security Lead
User sessions must expire after 15 minutes of inactivity.
All security groups must sync automatically with the central directory.
Token refreshes should be performed silently in the background.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {output_path}")


def make_meeting_notes_v2_txt(output_path: str):
    content = """Sprint 2 Follow-up Security Review Notes
Date: 2026-10-15 | Attendees: Product Manager, Security Lead, Operations Lead
User sessions must expire after 30 minutes of inactivity.
Review of operational complaints regarding sudden session disconnects during long form submissions.
Agreed to align timeout settings with the revised enterprise usability baseline.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {output_path}")


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "demo", "data")
    os.makedirs(data_dir, exist_ok=True)

    make_auth_wireframe(os.path.join(data_dir, "auth_wireframe.jpg"))
    make_client_notes_pdf(os.path.join(data_dir, "client_notes.pdf"))
    make_meeting_notes_txt(os.path.join(data_dir, "meeting_notes.txt"))
    make_meeting_notes_v2_txt(os.path.join(data_dir, "meeting_notes_v2.txt"))
    print("All canonical demo data files generated successfully.")


if __name__ == "__main__":
    main()
