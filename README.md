# 📋 BRD Agent: The BRD That Shows Its Work

> **From messy files to a verified, traceable BRD.**
> Built for **HackSprint Track 4: BRD Generation Agent (Problem Statement PS42)**.

---

## 🌟 Executive Summary & Problem Statement

**Problem Statement (PS42):**
Build a scalable, multi-modal AI system using Google Gemini AI and integrated Google Cloud tools (such as Vertex AI, Cloud Storage, and BigQuery) that can process real-time, fragmented data (text, images, and documents) and deliver accurate, context-aware, and explainable decisions in complex and dynamic environments.

Requirements typically begin scattered across hand-drawn wireframes, client PDFs, and meeting notes. Manually consolidating them leads to missed details, unspotted contradictions, and untraceable scope disputes.

**BRD Agent** ingests fragmented project artifacts simultaneously, uses Google Gemini on Vertex AI to extract structured functional and non-functional requirements, **programmatically verifies the source evidence of every single requirement**, flags contradictions and coverage gaps, and exports a clean Business Requirements Document (BRD) where **every confirmed requirement cites its exact evidence**.

---

## 🎯 Key Innovation: "The BRD That Shows Its Work"

1. **Explainable Evidence Viewer (Core USP):**
   - Click any requirement to see its exact grounded proof:
     - **Image / Wireframe:** Bounding box (`[ymin, xmin, ymax, xmax]`) highlighted in red over UI elements.
     - **PDF Document:** Verbatim quote highlighted in yellow on high-resolution 2x rendered PDF pages.
     - **Text Notes:** Multi-line context viewer highlighting the line with `>> `.
2. **Strict Verification Guardrail:**
   - Programmatically validated by `app/verify.py`. If a quote or bounding box cannot be verified in the source file, the requirement is flagged as `unverified` and **never appears in confirmed sections of the BRD**.
3. **Contradiction Detection:**
   - Detects conflicts across incoming files (e.g. 15-minute vs. 30-minute session timeouts) with severity badges and interactive resolution controls.
4. **Coverage Gap Analysis:**
   - Uses whole-word boundary matching across 7 core governance categories (Authentication, Authorization, Data Retention & Privacy, Performance, Availability, Audit & Logging, Security) to raise targeted clarification questions.
5. **Project Memory in BigQuery:**
   - Stores runs, artifacts, requirements, evidence citations, conflicts, and gaps to ground future runs against past project baselines.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Streamlit Web Interface                        │
│          Upload Tab | Requirements Viewer | Conflicts | BRD Export    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ calls
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     BRD Agent Orchestrator (Python)                    │
│   1. Artifact Registration ──► 2. Cloud Storage Upload (Raw Blobs)    │
│   3. Gemini Extraction     ──► 4. Strict Evidence Verification        │
│   5. Gap Coverage Analysis ──► 6. Historical Grounding & Conflicts    │
│   7. BigQuery Persistence  ──► 8. BRD Export (Markdown & DOCX)        │
└───────────┬───────────────────────┬───────────────────────┬────────────┘
            │                       │                       │
            ▼                       ▼                       ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
│ Google Cloud Storage │ │ Vertex AI + Gemini   │ │ Google BigQuery      │
│ Private bucket for   │ │ gemini-2.5-flash for │ │ Dataset `brd_agent`  │
│ uploaded artifacts   │ │ structured JSON      │ │ Tables: runs, reqs,  │
│ (IAM-controlled)     │ │ extraction           │ │ evidence, conflicts  │
└──────────────────────┘ └──────────────────────┘ └──────────────────────┘
```

> **Architecture Honesty Note:** Vertex AI hosts and runs the Gemini model; Python plain code (`orchestrator.py`) orchestrates the pipeline and enforces verification rules.

---

## 📊 Built vs. Planned Status

| Feature / Capability | Status | Description |
|---|---|---|
| **Streamlit Review UI** | `MVP` | 4-tab interface: Upload, Requirements & Evidence, Conflicts & Gaps, BRD Export. |
| **Evidence Viewer** | `MVP` | Visual red bounding box on wireframes, yellow highlight on PDFs, line context on text. |
| **Strict Evidence Verification** | `MVP` | Programmatic verification in `app/verify.py` rejecting fake quotes and bad boxes. |
| **Demo Mode (Offline Replay)** | `MVP` | Cached demo extraction with live verification, gap checks, and export. |
| **BRD Markdown Export** | `MVP` | 7-section structured markdown report citing verified sources. |
| **BRD DOCX Export** | `MVP` | Word document export via `python-docx` matching the 7 sections. |
| **Cloud Storage Artifact Storage** | `MVP` | Uploads raw files to private GCS bucket (`projects/{project_id}/runs/{run_id}/...`). |
| **BigQuery Persistence** | `MVP` | 6 tables: `runs`, `artifacts`, `requirements`, `evidence`, `conflicts`, `gaps`. |
| **Conflict Detection (Current vs. Past)** | `MVP` | Detects contradictions against incoming files and past verified runs in BigQuery. |
| **Coverage Gap Clarification Questions** | `MVP` | Whole-word matching across 7 standard enterprise requirement categories. |
| **Human Review Sign-off** | `MVP` | Per-requirement Approve/Reject controls. |
| **Image Second Check (Crop & Re-ask)** | `If time allows` | Cropping region to re-verify context with Gemini. |
| **OCR for Scanned PDFs** | `Next steps` | Document AI OCR for scanned physical documents. |
| **Jira & Confluence Integration** | `Next steps` | Direct export to issue trackers and wikis. |
| **Multi-User Collaboration & RBAC** | `Next steps` | Enterprise user authentication and role-based permissions. |

---

## 🚀 Setup & Quickstart

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Google Cloud SDK (`gcloud` CLI) installed (for live mode)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/sankirthreddyrs/brd-agent_hacksprint.git
cd brd-agent_hacksprint

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Generate Canonical Demo Data
```bash
python scripts/make_demo_data.py
```
This generates the 4 canonical files in `demo/data/`:
- `auth_wireframe.jpg` (Login wireframe with Google OAuth 2.0 button)
- `client_notes.pdf` (Client interview notes supporting FR-01 and FR-02)
- `meeting_notes.txt` (Kickoff notes supporting FR-03 session timeout)
- `meeting_notes_v2.txt` (Follow-up notes introducing FR-04 contradiction)

### 4. Run Core Tests
```bash
python tests/test_core.py -v
```
All 10 unit tests pass locally with no cloud dependencies required.

### 5. Launch the Streamlit App
```bash
streamlit run app/app.py
```
- Toggle **Demo Mode** ON to demo the complete workflow immediately from local sample files.
- Tick **"Use sample demo files (Stage 1)"** and click **"Process Files"** to inspect requirements and the Evidence Viewer.
- Tick **"Include Stage-2 file (meeting_notes_v2.txt)"** to trigger contradiction detection between FR-03 and FR-04.

---

## ☁️ Google Cloud Live Mode Setup

To run against live Vertex AI, Cloud Storage, and BigQuery:

1. **Authenticate and set quota project:**
   ```bash
   gcloud auth application-default login
   gcloud auth application-default set-quota-project YOUR_PROJECT_ID
   ```

2. **Configure `.env`:**
   ```env
   GCP_PROJECT_ID=your-project-id
   GCP_LOCATION=us-central1
   GCS_BUCKET=your-unique-bucket-name
   BQ_DATASET=brd_agent
   GEMINI_MODEL=gemini-2.5-flash
   DEMO_MODE=false
   ```

3. **Run the Cloud Smoke Test:**
   ```bash
   python scripts/smoke_test.py
   ```

---

## 🔍 Proof of Persistence (Acceptance Test A6)

To inspect stored requirements and verified evidence in the BigQuery Console:

```sql
SELECT
  r.run_id,
  r.display_id,
  r.text,
  r.verification_status,
  e.file_name,
  e.quote,
  e.verified
FROM
  `YOUR_PROJECT_ID.brd_agent.requirements` r
LEFT JOIN
  `YOUR_PROJECT_ID.brd_agent.evidence` e
USING (project_id, run_id, display_id)
ORDER BY
  r.created_at DESC;
```

---

## 🛡️ Honesty & Claims Guardrails

In compliance with HackSprint competition guidelines:
- **Reduces Unsupported Requirements:** We do not claim to "prevent hallucinations" or guarantee "100% accuracy". We reduce unsupported requirements by programmatically grounding outputs in source evidence and verifying quotes.
- **Human-in-the-Loop:** Gemini can misread inputs or produce false positives; a human reviews and approves the BRD before final sign-off.
- **Scalability:** Built on managed Google Cloud services designed to scale (Cloud Storage, Vertex AI, BigQuery); the prototype has not been load-tested.
- **Data Security:** Raw artifacts are stored in a private Cloud Storage bucket with IAM-controlled access.
