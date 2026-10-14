
# BRD Agent: Product Requirements Document (PRD) v2.0

| | |
|---|---|
| Version | **2.0** (14 October 2026). Replaces v1.0 |
| Product | BRD Agent |
| Team | Stark: **Sankirth Reddy (backend)**, **Yashwanth (frontend)** |
| Event | HackSprint 24-Hour Hackathon, MAHE, Round 3 (Manipal University Bengaluru) |
| Companion documents | `BRD_Agent_Build_Guide.md` (step-by-step plan), `brd-agent-starter.zip` (starter code) |

**What changed from v1.0:** two-person team and three-day plan (was four people, 24 hours); the data contract is now the tested `schemas.py`; requirements carry an owner and a starter-code status; the BigQuery tables, prompts, gap categories and UI spec now match the real code; added AI-agent briefs (section 22) and living logs (section 23); `import fitz` replaced by `import pymupdf`.

---

## 0. How humans and AI agents use this document

This PRD is the shared reference for **both teammates and for the AI coding assistants each of them uses** (ChatGPT, Gemini, Claude, Copilot, etc.). Write and read it as if the reader has no other context.

### 0.1 Source-of-truth precedence (if two sources disagree)
1. **Code contract** (`app/schemas.py` and the function signatures in `app/orchestrator.py`) wins for data shapes and function names.
2. **This PRD** wins for what to build and how it must behave.
3. **Build Guide** wins for order of work and commands.
4. Anything else (slides, chat messages) is lower priority. If you find a conflict, record it in the Decision log (section 23).

### 0.2 Tags used in this document
| Tag | Meaning |
|---|---|
| **MUST / SHOULD / COULD** | Priority. MUST = demo cannot work without it. |
| **NEXT / FUTURE** | Do not build now. |
| **[TESTED]** | Starter code that runs and has passing local tests. |
| **[UNTESTED]** | Starter code written but never run against real Google Cloud. Test it before trusting it. |
| **[TODO]** | Not written yet. |
| **[CONFIRM]** | Unknown that must be confirmed with the organizers (section 21). |

### 0.3 Context packs: which sections each agent should read
| Reader | Read these sections |
|---|---|
| Any agent (always) | 0, 2, 5, 6, 19, 22 |
| Frontend agent (Yashwanth) | + 7 (F-01 to F-05, F-50 to F-53, F-60 to F-62, F-70 to F-72), 12, 13, 17, 18 |
| Backend agent (Sankirth) | + 7 (F-03, F-10 to F-42), 8, 9, 10, 11, 14, 15, 20 |
| Reviewer / pitch writer | + 1, 2, 4, 18, 19, 21, Appendix A |

### 0.4 Rules for every AI agent
1. Edit only the files your human owns (section 6.1). Never change `app/schemas.py` or the signatures in `app/orchestrator.py` unless both humans agreed and logged it (section 23).
2. Do not invent Google Cloud services, APIs, features, numbers, results or completed work. If something is not specified, state your assumption in one line and choose the simplest option.
3. Keep the canonical names and example data (section 5) identical everywhere.
4. Return **complete replacement code** for each changed file, plus the exact command to test it and the expected output.
5. Never describe a feature as working unless it has been run. Use the tags in 0.2.
6. Be honest in anything user-facing (UI text, README, pitch). See section 19.

---

## 1. Context

### 1.1 Event and team

| Field | Value |
|---|---|
| Event | HackSprint 24-Hour Hackathon, Manipal Academy of Higher Education (MAHE), organized with Commudle |
| Dates | 17-18 October 2026 (Saturday 17th, 09:00 onwards) |
| Round | **Round 3**, on-site at Manipal University Bengaluru, Karnataka |
| Build window | **Thursday 15 to Saturday 17 October 2026 (3 days)**, setup on Wednesday 14 October. **[CONFIRM]** If the demo is on Sunday 18, add the spare day as buffer. |
| Team | Stark (1-4 members allowed). Sankirth Reddy (backend), Yashwanth (frontend) |
| Track | **Track 4: Business Requirements Document (BRD) Generation Agent** |
| Problem statement ID | **PS42** |

### 1.2 Problem statement from the organizers (verbatim)

> **PS42:** Build a scalable, multi-modal AI system using Google Gemini AI and integrated Google Cloud tools (such as Vertex AI, Cloud Storage, and BigQuery) that can process real-time, fragmented data (text, images, and documents) and deliver accurate, context-aware, and explainable decisions in complex and dynamic environments.

| Phrase in PS42 | How BRD Agent answers it |
|---|---|
| Scalable | Managed Google Cloud services. Design goal, not load-tested. |
| Multi-modal | Reads images, PDFs and text together. |
| Google Gemini AI | Gemini extracts and reasons. |
| Vertex AI, Cloud Storage, BigQuery | Vertex AI runs Gemini; Cloud Storage holds raw files; BigQuery stores requirements, evidence, history. |
| Fragmented data | Input is deliberately scattered across formats. |
| Accurate, context-aware | Evidence verification plus a grounding step against past project requirements. |
| Explainable | Every requirement links to its exact evidence, viewable in the UI. |

### 1.3 Tools the organizers expect
Google Gemini AI (core) plus integrated Google Cloud tools. The organizers name Vertex AI, Cloud Storage and BigQuery ("such as"); the submitted deck commits to all three.

### 1.4 Track description from the organizers
An automated AI agent that: synthesizes fragmented project artifacts (whiteboard photos, PDFs, text) into a structured BRD; processes visual wireframes and text notes simultaneously; cross-references incoming data against established enterprise logic; embeds a source-file citation for every requirement.

### 1.5 Submission and evaluation (as communicated)
- Shortlisted teams submitted: problem statement, solution, track, screenshot, GitHub repo link, DFD. **Done.**
- Teams are evaluated on **innovation and relevance**, then locked for Round 3.
- Screening guidance: a prototype (planned working, architecture pipeline or MVP) was enough.
- Round 3 criteria, demo format and rules: **[CONFIRM]**. Assume judges expect a **working demo** of the core flow.

---

## 2. Product summary

**Name:** BRD Agent. **One-liner:** From messy files to a verified, traceable BRD. **Pitch line:** *The BRD that shows its work.*

**What it is:** An AI requirements agent. A user uploads a whiteboard/wireframe photo, client PDFs and meeting notes. The agent reads them together with Gemini, extracts structured requirements, **verifies the evidence of each**, flags contradictions and gaps, and exports a BRD where every requirement cites its source.

### 2.1 Unique selling point
1. **Evidence viewer (core USP).** Click a requirement and see the exact evidence: a box on the image, the highlighted quote on the PDF page, the highlighted line in the text.
2. **No verified evidence, no confirmed requirement.** Enforced in code (`verify.py`, `export.py`), not only in the prompt.
3. **Conflict and gap detection.** Contradictions between sources and missing areas are flagged with clarification questions.
4. **Project memory.** Past requirements in BigQuery are checked against new uploads (grounding loop).

### 2.2 Why it is an agent and not "Gemini plus a prompt"
A plain prompt reads files once and writes a document. BRD Agent runs a multi-step workflow and acts on intermediate results: it downgrades unverified evidence, flags conflicts, and raises clarification questions. The demo must make this visible.

### 2.3 Naming honesty
The workflow runner is `orchestrator.py`, **plain Python**. Call it "BRD Agent Orchestrator". Do not call it an autonomous Vertex AI agent. Vertex AI runs Gemini; Python orchestrates.

---

## 3. Problem and users

**Problem:** Requirements start as whiteboard photos, client PDFs and meeting notes. Teams merge them by hand, details are missed or conflict, and later nobody can say which file a requirement came from. That causes rework and scope disputes. Generic summarizers read one file type at a time, do not check gaps, and give no way to verify a requirement's origin.

**Users:** Business Analyst (builds the BRD, must defend each line), Project Manager (needs conflicts and origin early), Product Manager (needs one verified source of truth). Secondary: hackathon judges, who must understand the problem, multimodal input, explainability and real Google Cloud use.

---

## 4. Goals, non-goals, acceptance

**Goals:** a working end-to-end flow (upload, extract with evidence, verify, review with evidence viewer, export); genuine use of Gemini on Vertex AI, Cloud Storage and BigQuery; a memorable demo of the evidence viewer and a caught contradiction; honest labeling of built vs planned.

**Non-goals (do NOT build):** user accounts or login; real-time collaboration; Jira/Confluence/Word integrations; agent frameworks (LangChain, ADK); fine-tuning; Docker or Cloud Run deployment; vector databases; mobile app; any front end other than Streamlit.

### 4.1 Acceptance tests (the product is demo-ready when all MUST items pass)

| ID | Priority | Test | Pass condition |
|---|---|---|---|
| A1 | MUST | Upload the 3 stage-1 files in live mode | 3 or more requirements, each with evidence, in about a minute (measure; do not promise) |
| A2 | MUST | Click FR-01 | Box on the whiteboard image and highlighted passage on the PDF page both show |
| A3 | MUST | A requirement with a fake quote | Marked `unverified` and excluded from confirmed BRD sections (`test_unverified_requirement_excluded_from_brd` passes) |
| A4 | SHOULD | Run stage 2 (`meeting_notes_v2.txt`) after stage 1 | The 15 vs 30 minute conflict is flagged |
| A5 | SHOULD | Check gaps | A data retention and privacy question appears |
| A6 | MUST | BigQuery console query | Shows requirement and evidence rows from the run |
| A7 | MUST | Download the BRD | Markdown has a citation on every confirmed line and separate sections for unverified items, conflicts, open questions |
| A8 | MUST | Network off, Demo mode on | The whole demo runs from the cache with the Demo-mode warning visible |

---

## 5. Canonical names and example data (use exactly)

| Thing | Value |
|---|---|
| Stage-1 files | `auth_wireframe.jpg` (hand-drawn login sketch), `client_notes.pdf`, `meeting_notes.txt` |
| Stage-2 file | `meeting_notes_v2.txt` (planted contradiction: 30 minutes vs 15) |
| Planted gap | No file mentions data retention or privacy |
| Requirements | FR-01 System must support OAuth2.0 (sources: `auth_wireframe.jpg`, `client_notes.pdf`); FR-02 Admins can export audit logs (`client_notes.pdf`); FR-03 Sessions expire after 15 minutes of inactivity (`meeting_notes.txt`); FR-04 Sessions expire after 30 minutes of inactivity (`meeting_notes_v2.txt`), conflicts with FR-03 |
| Evidence statuses | `verified`, `unverified` |
| Review statuses | `pending`, `approved`, `rejected` |
| Status words | MVP, If time allows, Next steps |

Honesty note: a "Continue with Google" button is evidence for Google sign-in, which implies OAuth. Do not imply a requirement can always be inferred from a visual alone. The example is illustrative.

**Glossary:** *Artifact* = uploaded file. *Evidence* = the exact place in an artifact that supports a requirement (quote with page or line, or an image region box). *Verified* = checked programmatically. *Unverified* = the model gave a requirement but its evidence could not be verified; it is never shown as confirmed. *Conflict* = two requirements that contradict. *Gap* = an expected area with no requirement; produces a clarification question. *Grounding loop* = loading past requirements from BigQuery and comparing new ones against them. *Demo mode* = replays cached Gemini output; verification, gap checks and export still run for real.

---

## 6. Team, ownership and the contract

### 6.1 File ownership

| File | Owner | Job | Status |
|---|---|---|---|
| `app/app.py` | Yashwanth | Streamlit screens | [TESTED] runs in demo mode; polish needed |
| `app/render.py` | Yashwanth | Evidence to image/text for the UI | [TESTED] |
| `app/export.py` | Yashwanth | BRD Markdown with citations | [TESTED] |
| `demo/data/*` | Yashwanth | Real demo files | placeholders written; replace with real files |
| `app/orchestrator.py` | Sankirth | The workflow (`run_pipeline`) | demo path [TESTED]; live path [UNTESTED] |
| `app/gemini_client.py` | Sankirth | Gemini calls, prompts, demo cache | demo path [TESTED]; live calls [UNTESTED] |
| `app/storage.py` | Sankirth | Cloud Storage uploads | [UNTESTED] |
| `app/bq.py` | Sankirth | BigQuery tables, save run, load history | [UNTESTED] |
| `app/verify.py` | Sankirth | Evidence verification | [TESTED] |
| `app/gaps.py` | Sankirth | Missing-area check | [TESTED] |
| `app/config.py`, `.env` | Sankirth | Settings, secrets (never commit `.env`) | [TESTED] |
| `app/schemas.py` | **Both** | THE CONTRACT | [TESTED] |
| `scripts/*`, `tests/*` | Sankirth | Smoke test, prompt tuning, tests | tests [TESTED]; `smoke_test.py`, `try_extract.py` [UNTESTED] |

### 6.2 The contract (functions)
The frontend calls **only** these, from `app/orchestrator.py`:

```python
load_demo_files() -> dict[str, bytes]
run_pipeline(project_id: str, files: dict[str, bytes], demo_mode: bool,
             on_progress: Callable[[str], None] | None = None) -> RunResult
set_review_status(result: RunResult, requirement_id: str, status: str) -> RunResult
```

And these helpers: `render.render_evidence(ev, file_bytes) -> dict`, `export.build_brd_markdown(project_name, result, approved_only=False) -> str`.

The frontend must **never** import `gemini_client`, `bq` or `storage`.

### 6.3 The contract (data shapes), exact file `app/schemas.py`

```python
"""THE CONTRACT. Shared by frontend and backend. Change only after telling the other person."""
from typing import Literal, Optional
from pydantic import BaseModel, Field

Kind = Literal["image", "pdf", "text"]


# ---- What Gemini returns (kept flat and simple for Vertex structured output) ----
class ExtractedEvidence(BaseModel):
    file_name: str
    kind: Kind
    quote: Optional[str] = None          # verbatim text (pdf/text)
    page: Optional[int] = None           # 1-based (pdf)
    line: Optional[int] = None           # 1-based (text)
    box_2d: Optional[list[int]] = None   # [ymin, xmin, ymax, xmax], 0-1000 (image)


class ExtractedRequirement(BaseModel):
    id: str                               # "FR-01"
    text: str
    type: Literal["functional", "non-functional", "constraint"]
    evidence: list[ExtractedEvidence] = Field(default_factory=list)


# ---- What the app stores and shows ----
class Evidence(ExtractedEvidence):
    verified: bool = False
    verify_note: str = ""


class Requirement(BaseModel):
    id: str
    text: str
    type: Literal["functional", "non-functional", "constraint"]
    evidence: list[Evidence] = Field(default_factory=list)
    verification_status: Literal["verified", "unverified"] = "unverified"
    review_status: Literal["pending", "approved", "rejected"] = "pending"


class Conflict(BaseModel):
    requirement_ids: list[str]
    description: str
    severity: Literal["low", "medium", "high"] = "medium"
    resolved: bool = False


class GapQuestion(BaseModel):
    category: str
    question: str
    answer: Optional[str] = None


class ArtifactInfo(BaseModel):
    file_name: str
    kind: Kind
    mime_type: str
    size_bytes: int
    gcs_uri: Optional[str] = None


class RunResult(BaseModel):
    run_id: str
    project_id: str
    mode: Literal["live", "demo"]
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    gaps: list[GapQuestion] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)   # stage timings / warnings shown in UI
```

### 6.4 Contract rules
- **File bytes never travel inside `RunResult`.** The UI keeps `files: dict[str, bytes]` in `st.session_state` and passes `files.get(ev.file_name)` to `render_evidence`.
- `ExtractedRequirement` and `ExtractedEvidence` are what Gemini returns. They are kept **flat and simple** because Vertex structured output supports only a subset of JSON schema.
- `Requirement.verification_status` is **derived by code** (`verify.py`), never trusted from the model.
- Changing `schemas.py` or the signatures requires: both humans agree, a Decision log entry, a Contract changelog entry, all tests green (section 23).

---

## 7. Functional requirements

Priority: MUST = MVP. SHOULD = MVP if time allows. COULD = stretch. NEXT = do not build now. Owner: S = Sankirth, Y = Yashwanth.

### 7.1 Upload and storage
| ID | Requirement | Priority | Owner | Starter status |
|---|---|---|---|---|
| F-01 | Upload multiple files (JPG, JPEG, PNG, PDF, TXT) with a Streamlit uploader | MUST | Y | [TESTED] done |
| F-02 | List uploaded files with name and size | MUST | Y | [TESTED] done |
| F-03 | Store each file in a private bucket at `projects/{project_id}/runs/{run_id}/{file_name}` (live mode) | MUST | S | [UNTESTED] |
| F-04 | Reject unsupported types (uploader filter) and handle oversized files (size limit about 10 MB per file **[CONFIRM against Gemini limits]**) | SHOULD | Y | type filter done; size limit [TODO] |
| F-05 | Project name input (default "Demo Project") | MUST | Y | [TESTED] done |

### 7.2 Extraction (Gemini on Vertex AI)
| ID | Requirement | Priority | Owner | Starter status |
|---|---|---|---|---|
| F-10 | Send all artifacts to Gemini together (images and PDFs via Cloud Storage URI or bytes, text as text) with a prompt and a JSON schema | MUST | S | [UNTESTED] |
| F-11 | Gemini returns requirements: id, text, type, evidence list | MUST | S | [UNTESTED] |
| F-12 | Text/PDF evidence includes a verbatim quote and page (PDF) or line (text) | MUST | S | prompt written [UNTESTED] |
| F-13 | Image evidence includes `box_2d` = `[ymin, xmin, ymax, xmax]`, normalized 0-1000. Test early on the real photo. | MUST (with fallback) | S | prompt written; test via `smoke_test.py` |
| F-14 | Never ask Gemini to invent requirements not supported by the files | MUST | S | prompt + verification |

### 7.3 Evidence verification (the trust guardrail)
| ID | Requirement | Priority | Owner | Starter status |
|---|---|---|---|---|
| F-20 | Text/PDF: check the quote appears in the source (whitespace and case normalized). PDF: locate the page with PyMuPDF `search_for` | MUST | S | [TESTED] |
| F-21 | Image: validate the box (4 ints, 0-1000, positive area) | MUST | S | [TESTED] |
| F-22 | A requirement with no verified evidence gets `verification_status="unverified"`, is shown with a warning, and is excluded from confirmed BRD sections | MUST | S + Y | [TESTED] |
| F-23 | Image second check: crop the boxed region and ask Gemini if it supports the requirement | COULD | S | [TODO] |

### 7.4 Conflicts and gaps
| ID | Requirement | Priority | Owner | Starter status |
|---|---|---|---|---|
| F-30 | After extraction, a Gemini call compares new requirements with stored ones and returns conflicts | SHOULD | S | [UNTESTED] |
| F-31 | Coverage checklist in Python (section 11.5) | SHOULD | S | [TESTED] |
| F-32 | Templated clarification question for each missing category | SHOULD | S | [TESTED] |
| F-33 | UI tab lists conflicts and shows an answer box per gap question (resolved checkbox and severity colors still to do) | SHOULD | Y | basic [TESTED]; polish [TODO] |
| F-34 | Re-run checks after the user answers a question | NEXT | | |

### 7.5 Persistence and project memory (BigQuery)
| ID | Requirement | Priority | Owner | Starter status |
|---|---|---|---|---|
| F-40 | Write runs, artifacts, requirements, evidence, conflicts, gaps to BigQuery (section 10.3) | MUST (requirements and evidence), SHOULD (rest) | S | [UNTESTED] |
| F-41 | Grounding loop: load past verified requirements for the project and pass them to F-30 | SHOULD | S | [UNTESTED] |
| F-42 | Be able to show a BigQuery console query as proof | MUST | S | manual step |

### 7.6 Review UI
| ID | Requirement | Priority | Owner | Starter status |
|---|---|---|---|---|
| F-50 | Requirements table: ID, requirement, type, sources, evidence status, review status | MUST | Y | [TESTED] |
| F-51 | Selecting a requirement opens the evidence viewer (section 12.3) | MUST | Y | [TESTED], polish needed |
| F-52 | Approve or reject each requirement (human review before sign-off) | SHOULD | Y | basic [TESTED] |
| F-53 | Progress messages while the pipeline runs | SHOULD | Y | [TESTED] |

### 7.7 Export
| ID | Requirement | Priority | Owner | Starter status |
|---|---|---|---|---|
| F-60 | Downloadable BRD. Markdown is the minimum; DOCX (python-docx) is a stretch | MUST (MD), COULD (DOCX) | Y | MD [TESTED]; DOCX [TODO] |
| F-61 | Every confirmed requirement line cites its verified source(s) | MUST | Y | [TESTED] |
| F-62 | Separate sections for unverified items, conflicts, open questions | SHOULD | Y | [TESTED] |

### 7.8 Demo mode and resilience
| ID | Requirement | Priority | Owner | Starter status |
|---|---|---|---|---|
| F-70 | Demo-mode toggle with a visible warning when active. Demo mode replays cached Gemini output; verification, gaps and export still run for real | MUST | Y + S | [TESTED] |
| F-71 | Every live run writes `demo/cache/run_<sha1 of sorted file names>.json`; demo mode replays the cache for that exact file set, else a built-in mock that matches `scripts/make_demo_data.py` | SHOULD | S | [UNTESTED] (live write); replay [TESTED] |
| F-72 | Errors from Gemini or Google Cloud are shown in plain language, not stack traces | SHOULD | Y + S | basic [TESTED] |

### 7.9 Roadmap items (do NOT build now)
Word export beyond basic, multi-project memory, team review workflow with several reviewers, Jira/Confluence export, BRD version history, interactive clarification re-run (F-34).

---

## 8. Workflow (what `run_pipeline` does, in order)

| # | Step | Code | Mode | Priority |
|---|---|---|---|---|
| 1 | Register artifacts (name, kind, mime, size) | `orchestrator.py` | both | MUST |
| 2 | Upload raw files to Cloud Storage | `storage.upload_files` | live | MUST |
| 3 | Extract: Gemini reads all files, returns requirements with evidence | `gemini_client.extract_requirements` (live) or `demo_extraction` (demo) | both | MUST |
| 4 | **Verify evidence** (always real) | `verify.verify_requirements` | both | MUST |
| 5 | **Gap check** (always real) | `gaps.coverage_gaps` | both | SHOULD |
| 6 | Load past requirements from BigQuery | `bq.load_active_requirements` | live | SHOULD |
| 7 | Detect conflicts against past requirements | `gemini_client.detect_conflicts` | live | SHOULD |
| 8 | Save run to BigQuery | `bq.save_run` | live | MUST |
| 9 | Save cache for demo mode | `gemini_client.save_cache` | live | SHOULD |
| 10 | Return `RunResult` | `orchestrator.py` | both | MUST |
| 11 | Human review, then export | `app.py`, `export.py` | both | MUST |

Mapping to the submitted deck's four steps: **Upload** = 1-2; **Understand** = 3-7; **Organize** = 4, 8; **Deliver** = 10-11.

---

## 9. Architecture

### 9.1 Components and their single jobs

| Component | Technology | Job |
|---|---|---|
| User interface | Streamlit | Upload, progress, review, evidence viewer, export |
| BRD Agent Orchestrator | Python (`orchestrator.py`) | Runs the workflow, applies verification and decision rules |
| Raw artifact storage | Cloud Storage (private bucket, IAM-controlled access) | Holds uploaded images, PDFs, text |
| Multimodal model execution | Vertex AI + Gemini via `google-genai` | Reads images and documents together, returns structured JSON |
| Normalization and validation | Pydantic (and Pandas for BigQuery loads) | Validates model output; builds tables |
| Structured storage and history | BigQuery | Requirements, evidence, runs, conflicts, gaps |
| Evidence tooling | PyMuPDF (`import pymupdf`), Pillow | Locate quotes in PDFs, render pages, draw image boxes |
| Export | Python | Builds the BRD Markdown |

Do **not** say Vertex AI "orchestrates the whole pipeline". Vertex AI runs Gemini; Python orchestrates.

### 9.2 Diagram

```
Streamlit app.py --> orchestrator.run_pipeline
                       |-> storage.py      -> Cloud Storage   (raw files)
                       |-> gemini_client   -> Vertex AI + Gemini (JSON with evidence)
                       |-> verify.py       (quotes and boxes, always real)
                       |-> gaps.py         (missing areas, always real)
                       |-> bq.py           -> BigQuery (save run, load history)
                       |-> gemini_client.detect_conflicts (history vs new)
                     <-- RunResult --> app.py + render.py + export.py
```

### 9.3 DFD alignment (submitted to the organizers)
Level 1 processes: **1.0 Upload** (Streamlit UI), **2.0 Understand** (Vertex AI + Gemini), **3.0 Organize** (Python + Pandas), **4.0 Deliver** (BRD with citations). Stores: **D1 Cloud Storage**, **D2 BigQuery**. External entity: Project Team. The dashed "past requirements (grounding loop)" flow is "if time allows". The implementation must not contradict the DFD.

---

## 10. Data model

### 10.1 Pydantic schemas
See section 6.3 (exact file). Do not duplicate or fork these classes.

### 10.2 Cloud Storage layout
`gs://{GCS_BUCKET}/projects/{project_id}/runs/{run_id}/{file_name}`. The bucket is private (uniform bucket-level access, public access prevention). Grant access with IAM.

### 10.3 BigQuery (dataset `brd_agent`; created by `bq.ensure_tables()`)

```sql
CREATE TABLE IF NOT EXISTS brd_agent.runs (
  run_id STRING,
  project_id STRING,
  mode STRING,
  model STRING,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS brd_agent.artifacts (
  run_id STRING,
  project_id STRING,
  file_name STRING,
  kind STRING,
  mime_type STRING,
  gcs_uri STRING,
  size_bytes INT64
);

CREATE TABLE IF NOT EXISTS brd_agent.requirements (
  project_id STRING,
  run_id STRING,
  display_id STRING,
  text STRING,
  type STRING,
  verification_status STRING,
  review_status STRING,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS brd_agent.evidence (
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

CREATE TABLE IF NOT EXISTS brd_agent.conflicts (
  project_id STRING,
  run_id STRING,
  requirement_ids ARRAY<STRING>,
  description STRING,
  severity STRING,
  resolved BOOL
);

CREATE TABLE IF NOT EXISTS brd_agent.gaps (
  project_id STRING,
  run_id STRING,
  category STRING,
  question STRING,
  answer STRING
);
```

ID rule: requirement display IDs (`FR-01`) restart in every run. When sending past requirements to the conflict check, the code uses `run_id:display_id` (for example `a1b2c3d4:FR-03`) so IDs never collide.

---

## 11. AI design

### 11.1 SDK and models (checked against current Vertex AI documentation)
- SDK: `pip install --upgrade google-genai`.
- Client: `genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)`.
- Files: `types.Part.from_uri(file_uri="gs://...", mime_type=...)`, or `Part.from_bytes(data=..., mime_type=...)` (the starter uses the Cloud Storage URI when it has one, else bytes). Text: `Part.from_text(text=...)`.
- Structured output: `types.GenerateContentConfig(response_mime_type="application/json", response_schema=list[ExtractedRequirement], temperature=0.1)`.
- Default model: `gemini-2.5-flash` (a current stable model on Vertex AI). Newer preview models exist; prefer stable for the demo. **[CONFIRM current model IDs in Model Garden on the day]**. Use `gemini-2.5-pro` only if flash quality is not enough.
- Vertex structured output supports a subset of JSON schema. If the SDK rejects a feature, simplify the schema, or drop `response_schema` and validate with Pydantic.

### 11.2 Extraction prompt (exact, from `gemini_client.py`)

```
You are a business analyst assistant. You receive project artifacts: images (whiteboard or wireframe photos), PDFs and text notes.
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
```

### 11.3 Conflict prompt (exact, from `gemini_client.py`)

```
Below are NEW requirements and EXISTING requirements (from earlier runs of the same project) as JSON.
Find groups that CONTRADICT each other (e.g. different numbers for the same setting, or opposite behavior). Duplicates are not conflicts.
Return JSON: a list of {requirement_ids, description, severity}. Use only the given requirements. If none, return [].
```

### 11.4 Verification algorithm (`verify.py`, [TESTED])
- **Text:** normalize (lowercase, collapse whitespace); the quote must appear in a line, or across lines. Records the line number.
- **PDF:** try the claimed page first, then all pages; `page.search_for(quote)`, else the first six words, else normalized page text. Records the page.
- **Image:** `box_2d` has four ints, each 0-1000, `ymin < ymax`, `xmin < xmax`.
- A requirement is `verified` if at least one evidence item is verified, otherwise `unverified`.
- **Never loosen matching until fake quotes pass.** `test_fake_quote_is_unverified` must keep passing.

### 11.5 Gap coverage checklist (`gaps.py`, [TESTED])
A category counts as covered if a **verified** requirement text contains one of its keywords as a **whole word** (an optional plural "s" is allowed). So "log" does not match "login", "load" does not match "download", and "oauth" still matches "oauth2.0".

| Category | Keywords | Clarification question |
|---|---|---|
| authentication | login, sign in, sign-in, oauth, password, sso | How should users authenticate (passwords, Google sign-in, SSO)? |
| authorization | role, permission, admin, access control | Which user roles exist and what can each role do? |
| data retention and privacy | retention, privacy, gdpr, personal data, delete | How long should user data be kept, and what privacy rules apply? |
| performance | concurrent, response time, latency, load, performance | What performance targets (users, response time) must the system meet? |
| availability | uptime, availability, downtime, backup | What availability or backup expectations exist? |
| audit and logging | audit, log, logging | What actions must be logged for audit? |
| security | encrypt, encryption, encrypted, security, session, timeout, tls | What security requirements apply (encryption, session rules)? |

### 11.6 Known model risks
- Gemini may return boxes that are slightly off or refuse boxes on messy images. Test on the real photo early. Fallback: show the image next to the quote without a box.
- Gemini may paraphrase a quote. Verification must catch it. Strengthen the prompt, do not weaken verification.
- Treat model output as untrusted until verified. A person reviews the BRD before sign-off.

---

## 12. UI specification (matches the starter `app/app.py`)

- **Sidebar:** title, project name, **Demo mode** toggle (default from `DEMO_MODE`) with a visible warning when ON, model caption, Reset button.
- **Tabs:** Upload, Requirements, Conflicts and gaps, BRD.
- **Upload:** uploader (jpg, jpeg, png, pdf, txt, multiple); in demo mode a checkbox "Use the sample demo files instead"; file list with sizes; **Process files** button (disabled with no files); a status box showing pipeline messages; errors shown with `st.error`.
- **Requirements:** table (ID, Requirement, Type, Sources, Evidence, Review); a selectbox "Open evidence for"; for each evidence item, `render.render_evidence` returns `{type, image, text, caption, verified}` shown with `st.image` or `st.code`, plus "Verified" or "Not verified: <note>"; unverified requirements show a warning; Approve and Reject buttons.
- **Conflicts and gaps:** each conflict as an error box with severity and IDs; a text box per gap question.
- **BRD:** Markdown preview and a "Download BRD (Markdown)" button.

### 12.1 Evidence viewer behavior
| Evidence kind | Shown |
|---|---|
| image | The image with a red rectangle (`box_2d` normalized 0-1000 converted to pixels) |
| pdf | The rendered page with the quote highlighted |
| text | The matching line with a few lines of context, marked `>>` |
| file missing | The caption and the quote text |

### 12.2 Known UI backlog (Yashwanth)
Evidence layout polish, severity colors, "resolved" checkbox for conflicts, show `result.notes` (timings), size-limit error, consistent styling, DOCX export (only after everything else).

### 12.3 UI honesty rules
- The Demo-mode warning must show whenever demo mode is on.
- Do not show features that are not implemented (for example "Jira export").
- Use the canonical status words only.

---

## 13. BRD output specification (matches `export.build_brd_markdown`)

```
# Business Requirements Document: {project_name}
Generated by BRD Agent | date | Run {run_id} | Mode: {live|demo}
## 1. Source artifacts
## 2. Functional requirements       (- **FR-01** text / Source: file (location))
## 3. Non-functional requirements
## 4. Constraints
## 5. Unverified items (not confirmed)
## 6. Conflicts
## 7. Open questions
```
Rules: a requirement appears in sections 2-4 only if `verification_status == "verified"` and `review_status != "rejected"` (and `approved` when `approved_only=True`). Citations list only verified evidence. Unverified items appear only in section 5.

---

## 14. Non-functional requirements

| Area | Requirement |
|---|---|
| Performance | Target a first result in about a minute for the three demo files. Measure before claiming. |
| Reliability | Demo mode replays cached output; errors shown plainly; retry Gemini calls up to 2 times with a short wait **[TODO]** |
| Security | Private bucket, IAM-controlled access, no secrets in Git, Application Default Credentials. Do not claim "secure by default". |
| Privacy | Demo data only, no real client data. |
| Cost | `gemini-2.5-flash`, compact prompts; confirm credits and quotas. |
| Observability | Pipeline messages shown in the UI; `RunResult.notes` holds timings and warnings. |
| Scalability | Design goal only (managed services). Not load-tested. Do not publish numbers. |
| Maintainability | Small modules, type hints, one config module. |

---

## 15. Tech stack, setup, environment

**Stack:** Python 3.10+, Streamlit, google-genai, google-cloud-storage, google-cloud-bigquery, pandas, pyarrow, db-dtypes, pydantic, pymupdf, pillow, python-docx (optional), python-dotenv.

**Environment variables (`.env`, never committed):**
```
GCP_PROJECT_ID=      GCP_LOCATION=us-central1     GCS_BUCKET=
BQ_DATASET=brd_agent GEMINI_MODEL=gemini-2.5-flash DEMO_MODE=true
```
Optional: `DEMO_DATA_DIR` (default `demo/data`), `DEMO_CACHE_DIR` (default `demo/cache`).

**Google Cloud setup (Sankirth, Wednesday night):** enable `aiplatform.googleapis.com`, `bigquery.googleapis.com`, `storage.googleapis.com`; `gcloud auth application-default login`; create a private bucket and the `brd_agent` dataset; IAM roles for each person who runs live mode: Vertex AI User, Storage Object Admin (on the bucket), BigQuery Data Editor, BigQuery Job User. Exact commands are in the Build Guide, steps 0.2 to 0.4.

**Run:** `pip install -r requirements.txt`, `python scripts/make_demo_data.py`, `python tests/test_core.py`, `streamlit run app/app.py` (from the repo root).

---

## 16. Repository structure and starter status

```
brd-agent/
  README.md  requirements.txt  .env.example  .gitignore
  app/
    app.py            Yashwanth   Streamlit UI                [TESTED]
    render.py         Yashwanth   evidence to image/text        [TESTED]
    export.py         Yashwanth   BRD Markdown                  [TESTED]
    orchestrator.py   Sankirth    run_pipeline                  demo [TESTED], live [UNTESTED]
    gemini_client.py  Sankirth    Gemini calls, prompts, cache  demo [TESTED], live [UNTESTED]
    storage.py        Sankirth    Cloud Storage                 [UNTESTED]
    bq.py             Sankirth    BigQuery                      [UNTESTED]
    verify.py         Sankirth    evidence verification         [TESTED]
    gaps.py           Sankirth    missing-area check            [TESTED]
    config.py         Sankirth    settings                      [TESTED]
    schemas.py        BOTH        the contract                  [TESTED]
  demo/data/   demo/cache/
  scripts/  make_demo_data.py [TESTED]  smoke_test.py [UNTESTED]  try_extract.py [UNTESTED]
  tests/    test_core.py (6 tests, all passing)
```

Tests in `tests/test_core.py`: demo pipeline end to end; fake quote is unverified; bad box rejected; unverified requirement excluded from the BRD; every evidence kind renders; gap keywords match whole words.

---

## 17. Build plan (3 days, 2 people)

Details and commands are in `BRD_Agent_Build_Guide.md`. Summary:

| When | Sankirth (backend) | Yashwanth (frontend) |
|---|---|---|
| Wed 14 Oct (setup) | GCP, auth, bucket, dataset, push starter, `.env` | Run starter in demo mode; draw the whiteboard sketch; write real demo files |
| Thu 15 | Smoke test, box check, tune prompt, BigQuery tables, run live end to end | UI pass 1, error handling, evening integration run |
| Fri 16 | Harden verification, prove BigQuery rows, conflicts with history, gap tuning | Evidence viewer final, approve/reject, BRD tab, conflicts and gaps polish, fresh-clone test |
| Sat 17 | Bug bash, freeze, build demo cache, offline test | Real screenshot for deck and README, backup video, rehearse |

**Feature freeze:** at least 6 hours before the demo slot **[CONFIRM slot time]**.

**Cut list (drop in this order if behind):** image second check, DOCX export, approve/reject, grounding loop and conflict detection, gap questions. **Never cut:** evidence viewer, evidence verification, BigQuery saving, demo mode.

---

## 18. Demo plan

**Three-minute script:**
1. One sentence on the problem (scattered files, no traceability).
2. Upload the three stage-1 files; show progress.
3. Show the requirements table. Click FR-01: show the box on the whiteboard and the highlighted PDF quote.
4. Say: "Anything without verified evidence is never shown as confirmed."
5. Upload `meeting_notes_v2.txt`: show the 15 vs 30 minute conflict, then the data retention question.
6. Show the BigQuery console with the stored rows.
7. Download the BRD and point to the citations.
8. Close: "The BRD that shows its work."

**Fallback:** Demo mode (say clearly it is running from a saved result), then the backup video.

**Likely judge questions:**
- *Why not just upload files to Gemini?* A single prompt cannot verify its own quotes or compare against past runs. We check every quote against the source, flag contradictions, and keep history in BigQuery.
- *How do you stop hallucinations?* We reduce unsupported requirements: no verified evidence, no confirmed requirement. Gemini can still misread an input, so a person reviews before sign-off.
- *Is it an autonomous agent?* It is a multi-step workflow with decisions. Vertex AI runs Gemini; our Python orchestrator runs the workflow.
- *Does it scale?* Built on managed Google Cloud services and designed to scale; not load-tested.
- *What is built vs planned?* Answer from the README status table; claim only what you ran.

---

## 19. Honesty and claims guardrails

| Do not say | Say instead |
|---|---|
| Prevents hallucinations | Reduces unsupported requirements by grounding outputs in source evidence and verifying quotes |
| 100% cited / accurate | Confirmed requirements require verified source evidence |
| Auto-scales | Built on managed Google Cloud services, designed to scale, not load-tested |
| Secure by default | Raw artifacts are stored in a private Cloud Storage bucket with IAM-controlled access |
| Vertex AI orchestrates the pipeline | Vertex AI runs Gemini; our Python orchestrator runs the workflow |
| Weeks to minutes | A design goal; quote a measured time only if you measured it |
| Production-ready | Hackathon prototype |

**Submitted deck:** it says "prevents hallucinations", "100% cited", "scales automatically", "secure by default" and "Vertex AI: secure API routing and orchestration across the whole pipeline", and shows the screenshot as a UI concept. In the pitch and Q&A use the wording above. Never claim: accuracy percentages, benchmarks, user studies, customer results, scalability numbers, or features that are not built.

---

## 20. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Gemini boxes unreliable on the whiteboard photo | Weak image evidence | Test Thursday morning; retake photo; try `gemini-2.5-pro`; fallback to image plus quote |
| Gemini paraphrases quotes | Many unverified items | Strong "verbatim" prompt; shorter quotes; never loosen verification silently |
| Credits, quota or network failure at the venue | Demo fails | Demo mode with cache; offline test; phone hotspot; backup video |
| IAM or API errors | Lost hours | Run `smoke_test.py` on Thursday morning; fix before anything else |
| Scope creep | Core demo not ready | Freeze 6 hours before; follow the cut list |
| Schema rejected by Vertex | Parse errors | Keep schemas flat; fall back to JSON mode plus Pydantic |
| Scanned PDF (no text layer) | Verification fails | Use a text-based PDF; mention OCR as next step |
| Contract drift between the two agents | Integration break | Contract rules (6.4); Decision log; tests in `tests/test_core.py` |
| Pre-written code not allowed | Disqualification risk | Section 21, question 1; keep the repo to docs until confirmed |

---

## 21. Open questions to confirm with the organizers

1. **Pre-written code:** may teams use code written before the event? The repo exists already. Until confirmed, keep it to docs and diagrams. **[CONFIRM, important]**
2. Round 3 judging criteria, weights and the demo format (live demo, time per team, Q&A). **[CONFIRM]**
3. Google Cloud credits or sandbox, allowed regions, model and quota limits. **[CONFIRM]**
4. Internet access at the venue, personal laptops, and whether outside APIs are allowed. **[CONFIRM]**
5. Whether the GitHub link is reviewed at Round 3 and whether commit history is checked.
6. That Track 4 is the BRD Generation Agent track (title slide says "TRACK NO :4").
7. Demo slot time (decides the feature-freeze time) and whether the demo day is Saturday or Sunday.
8. Current Gemini model IDs available in the team's Vertex region.

---

## 22. AI agent briefs (paste the matching brief into your assistant, with section 0.4 and the files it needs)

### 22.1 Frontend agent brief (for Yashwanth's assistant)
```
ROLE: You are the frontend engineer for BRD Agent (Streamlit). Your human is Yashwanth.
YOU MAY EDIT: app/app.py, app/render.py, app/export.py, demo/data/*.
YOU MUST NOT EDIT: app/schemas.py, app/orchestrator.py, app/gemini_client.py, app/storage.py, app/bq.py, app/verify.py, app/gaps.py, app/config.py.
IN app.py YOU MAY IMPORT ONLY: app.config, app.orchestrator (run_pipeline, set_review_status, load_demo_files), app.render (render_evidence), app.export (build_brd_markdown). Never import gemini_client, bq or storage.
DATA: you receive a RunResult (see PRD 6.3). File bytes are NOT inside it: keep uploaded files in st.session_state and pass files.get(ev.file_name) to render_evidence.
MUST SHOW: the Demo-mode warning whenever demo mode is on; a warning on unverified requirements; a citation on every confirmed line of the BRD.
NEVER: show features that are not implemented; use words other than verified/unverified and pending/approved/rejected; claim "prevents hallucinations" or "100% cited" in UI text.
BACKLOG (in order): 1) evidence viewer layout polish 2) friendly error messages 3) show result.notes 4) conflict severity colors and a resolved checkbox 5) size-limit validation 6) consistent styling 7) DOCX export (only after all MUST items).
DEFINITION OF DONE for any UI task: `python tests/test_core.py` passes; `streamlit run app/app.py` works in demo mode with the sample files; you list the exact clicks to verify the change.
```

### 22.2 Backend agent brief (for Sankirth's assistant)
```
ROLE: You are the backend engineer for BRD Agent (Gemini on Vertex AI, Cloud Storage, BigQuery). Your human is Sankirth.
YOU MAY EDIT: app/orchestrator.py (insides only), app/gemini_client.py, app/storage.py, app/bq.py, app/verify.py, app/gaps.py, app/config.py, scripts/*, tests/*.
YOU MUST NOT EDIT: app/app.py, app/render.py, app/export.py, demo/data/*. Do not change schemas.py or the function signatures in orchestrator.py without both humans agreeing and logging it (PRD section 23).
RULES: verification stays strict (never loosen matching until fake quotes pass). Requirement.verification_status is derived by code, never trusted from the model. Demo mode must always work: it replays demo/cache and still runs real verification and gap checks. Never commit .env or secrets. Every external call must be wrapped so errors become plain-language notes, not crashes.
LIVE CODE IS UNTESTED: storage.py, bq.py, gemini_client.extract_requirements/detect_conflicts and the live branch of run_pipeline have never run against Google Cloud. Test each with scripts/smoke_test.py and scripts/try_extract.py before relying on them.
BACKLOG (in order): 1) run scripts/smoke_test.py and fix auth/IAM 2) check box_2d on the real photo 3) tune EXTRACTION_PROMPT with scripts/try_extract.py 4) bq.ensure_tables and a live run 5) harden verification with real outputs, add a test per real failure 6) conflicts with history (A4) 7) gap keyword tuning (A5) 8) add Gemini retry (up to 2) 9) build demo cache from the final files.
DEFINITION OF DONE for any backend task: `python tests/test_core.py` passes; you give the exact command to run the change and the expected output; you label anything you could not run as [UNTESTED].
```

### 22.3 Shared prompt templates
**Task:** "Context: [paste the matching brief and section 0.4]. I am working on [F-xx / step ID]. Files you may edit: [list]. Current file contents: [paste]. Return full replacement files, the command to test, and the expected output. State assumptions instead of inventing details."

**Review:** "Review this diff against PRD v2.0: does it keep the contract, keep verification strict, avoid claims the code cannot back, and keep demo mode working? List problems first, then fixes. Diff: [paste]."

**Debug:** "Command: [cmd]. Full error: [paste]. File: [paste]. Give the 3 most likely causes in order and the exact check for each. Do not rewrite unrelated code."

---

## 23. Living logs (both humans and agents append here; newest at the bottom)

### 23.1 Decision log
| Date | Decision | Owner | Affects |
|---|---|---|---|
| 14 Oct | Workflow runner is plain Python ("BRD Agent Orchestrator"), not a Vertex AI agent | Both | Naming, pitch |
| 14 Oct | Default model `gemini-2.5-flash` (stable); change only after a smoke test | Sankirth | `config.py` |
| 14 Oct | Use `import pymupdf` (the `fitz` import is deprecated) | Sankirth | `verify.py`, `render.py` |
| 14 Oct | Demo mode replays cached Gemini output but verification and gap checks stay real | Both | Demo, trust |
| 14 Oct | History IDs sent to the conflict check are `run_id:display_id` | Sankirth | `bq.py`, prompts |
| 14 Oct | Frontend owns `render.py`, `export.py` and demo data (balances the two lanes) | Both | Ownership |
| | (add rows here) | | |

### 23.2 Contract changelog
| Version | Date | Change | Agreed by |
|---|---|---|---|
| contract-v1 | 14 Oct | Initial `schemas.py` and `orchestrator.py` signatures | Both |
| | | (add rows here; also tag `contract-vN` in Git) | |

---

## Appendix A: Submitted pitch deck (`stark_hacksprint.pptx`, 10 slides)
1 Title (Team Stark, Track No 4). 2 Solution (artifacts, BRD Agent, FR-01 to FR-03; four benefits). 3 Tech Stack and Architecture (five layers: Streamlit, Vertex AI, Gemini, Cloud Storage + BigQuery, Python + Pandas). 4 System Architecture (UI, Cloud Storage, Vertex AI + Gemini, Python + Pandas, BigQuery, BRD Export, grounding loop; three principles). 5 Agent Architecture (Orchestrator, "Enough context?", Knowledge, Skills/Planning/Insights, agent roles, key considerations). 6 Data Flow (Upload, Understand, Organize, Deliver). 7 Agent Workflow (six steps). 8 Prototype Pipeline (swimlane; MVP / If time allows / Next steps). 9 Project Screenshot (UI concept). 10 Impact and Feasibility.

## Appendix B: Already submitted to the organizers
Pitch deck; problem statement and solution text; DFD Level 0 and Level 1; screenshot (UI concept with caption); README for the GitHub repo. Keep the build consistent with them (names, example data, stack, DFD).

## Appendix C: Technical references (checked against current documentation)
Vertex AI structured output uses `response_mime_type="application/json"` with `response_schema` and supports a subset of the schema. The recommended SDK is `google-genai` (`genai.Client(vertexai=True, ...)`). Files from Cloud Storage use `Part.from_uri(file_uri="gs://...", mime_type=...)`. `gemini-2.5-flash` is listed as a stable model on Vertex AI. Image bounding boxes (`box_2d`, normalized 0-1000) must be tested on the real demo photo before relying on them.
