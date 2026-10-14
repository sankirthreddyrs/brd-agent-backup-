# BRD Agent: Step-by-Step Build Guide

For: Team Stark (Sankirth Reddy: backend, Yashwanth: frontend) | Window: 3 days, Thursday 15 to Saturday 17 October 2026 | Setup tonight, Wednesday 14 October

This guide is written so that a human or ANY LLM (ChatGPT, Gemini, Claude, Copilot, etc.) can follow it with no other context. Every step has an owner, exact actions, and a "done when" check.

---

## 0. How to use this guide

**Humans:** work top to bottom. Do not skip a "Done when" check. Do not start a later step if an earlier one is red.

**LLMs / coding assistants:** at the start of every chat paste the **Master Context** (section 1). Then give the assistant ONE step at a time plus the files it names. Use the prompt templates in section 10. Rules for the assistant:

1. Only edit files owned by the person you are helping (section 4). Never change `app/schemas.py` or the signatures in `app/orchestrator.py` without being told the other person agreed.
2. Do not invent Google Cloud services, APIs, features, numbers or results. If unsure, say so and choose the simplest option.
3. Code marked UNTESTED has not been run against a real Google Cloud project. Test it before relying on it.
4. Never claim a feature works in the UI, README or pitch unless it has been run and checked.
5. Keep canonical names exactly (section 3).

**Starter code:** `brd-agent-starter.zip` (delivered with this guide). Its core logic is tested: 6 tests pass and the Streamlit app runs end to end in demo mode with no cloud account. Cloud parts (Cloud Storage, Gemini, BigQuery) are written but UNTESTED until you run `scripts/smoke_test.py`.

---

## 1. Master Context (copy and paste at the start of any LLM chat)

```
PROJECT: BRD Agent. A hackathon product (HackSprint 24-Hour Hackathon, MAHE, Round 3, Track 4: BRD Generation Agent, problem statement PS42).
PS42: Build a scalable, multi-modal AI system using Google Gemini AI and integrated Google Cloud tools (Vertex AI, Cloud Storage, BigQuery) that processes fragmented data (text, images, documents) and delivers accurate, context-aware, explainable decisions.
EVALUATION: innovation and relevance.
WHAT IT DOES: A user uploads a whiteboard/wireframe photo, client PDFs and meeting notes. The agent reads them together with Gemini, extracts structured requirements, VERIFIES the evidence for each requirement, flags contradictions and gaps, and exports a Business Requirements Document (BRD) where every requirement cites its source.
USP: "The BRD that shows its work." (1) Evidence viewer: click a requirement and see the exact evidence highlighted (box on the image, highlighted passage on the PDF page, highlighted line in the text). (2) No verified evidence = the requirement is never shown as confirmed. (3) Conflict and gap detection with clarification questions. (4) Project memory in BigQuery (past requirements checked against new uploads).
STACK: Python 3.10+, Streamlit (UI), google-genai SDK with Vertex AI and model gemini-2.5-flash, Google Cloud Storage (private bucket), BigQuery (dataset brd_agent), Pandas, Pydantic, PyMuPDF (import pymupdf), Pillow.
TEAM: 2 people. Sankirth = backend (orchestrator, Gemini, Cloud Storage, BigQuery, verification, gaps). Yashwanth = frontend (Streamlit app, evidence rendering, BRD export, demo data).
TIME: 3 days (Thu 15 to Sat 17 Oct 2026). Feature freeze before demo. Demo mode (cached Gemini output) must always work.
CONTRACT: app/schemas.py (data shapes) and app/orchestrator.py (run_pipeline, set_review_status, load_demo_files). Frontend calls only these.
CANONICAL EXAMPLE: files auth_wireframe.jpg, client_notes.pdf, meeting_notes.txt (and meeting_notes_v2.txt for the conflict). Requirements: FR-01 System must support OAuth2.0; FR-02 Admins can export audit logs; FR-03 Sessions expire after 15 minutes of inactivity; FR-04 Sessions expire after 30 minutes of inactivity (conflicts with FR-03).
HONESTY RULES: Do not claim "prevents hallucinations", "100% accurate", "auto-scales", "production-ready", or any number we have not measured. Say "reduces unsupported requirements by grounding outputs in source evidence and verifying quotes". The Gemini model can still misread inputs, so a person reviews the BRD before sign-off.
NEVER: add login/accounts, agent frameworks (LangChain/ADK), Docker/Cloud Run deployment, vector databases.
```

---

## 2. Parameters and assumptions

| Item | Value |
|---|---|
| Event | HackSprint 24-Hour Hackathon, MAHE, organized with Commudle, 17-18 October |
| Round | Round 3, on-site at Manipal University Bengaluru, Karnataka |
| Build window assumed | Thu 15, Fri 16, Sat 17 October 2026. **[CONFIRM]** If the demo is Sunday 18, move Day 3 one day later and use the spare day as buffer. |
| Team | Stark. Sankirth Reddy (backend), Yashwanth (frontend) |
| Track | Track 4: BRD Generation Agent (PS42) |
| Required tools | Google Gemini plus integrated Google Cloud tools: Vertex AI, Cloud Storage, BigQuery |
| Already submitted | Pitch deck (`stark_hacksprint.pptx`), DFD, screenshot (UI concept), README, problem statement and solution text |
| Judging | Innovation and relevance known; Round 3 criteria and demo format **[CONFIRM]** |

**Open questions to send to the organizers tonight (copy and paste):**

> Hi, this is Team Stark (BRD Generation Agent, Track 4). Three quick questions before Round 3: (1) Are teams allowed to write code before the event starts, or must all code be written during the 24 hours? (2) Will Google Cloud credits or a sandbox project be provided, and are there model or quota limits? (3) What is the demo format (live demo, time per team, Q&A) and what are the judging criteria for Round 3? Thank you!

If the answer to (1) is "all code during the event", keep the repo to docs only until the official start and move the build window accordingly. Do not hide pre-built code.

---

## 3. Canonical names and demo data (use exactly)

| Thing | Value |
|---|---|
| Product | BRD Agent |
| Pitch line | The BRD that shows its work. |
| One-liner | From messy files to a verified, traceable BRD. |
| Stage-1 demo files | `auth_wireframe.jpg` (hand-drawn login sketch), `client_notes.pdf`, `meeting_notes.txt` |
| Stage-2 demo file | `meeting_notes_v2.txt` (contains the planted contradiction: session timeout 30 minutes vs 15) |
| Planted gap | No file mentions data retention or privacy, so the gap check must raise a clarification question |
| Requirement IDs | FR-01, FR-02, ... |
| Evidence statuses | `verified` / `unverified` |
| Review statuses | `pending` / `approved` / `rejected` |
| Build status words | MVP, If time allows, Next steps (use these in slides and README) |

---

## 4. Ownership and the contract

### 4.1 Who owns which file

| File | Owner | Job |
|---|---|---|
| `app/app.py` | Yashwanth | Streamlit screens: upload, requirements table, evidence viewer, conflicts and gaps, BRD tab |
| `app/render.py` | Yashwanth | Turns evidence into images or text the UI can show (already written and tested) |
| `app/export.py` | Yashwanth | Builds the BRD Markdown with citations (already written and tested) |
| `demo/data/*` | Yashwanth | The real demo files (whiteboard photo, PDF, notes) |
| `app/orchestrator.py` | Sankirth | `run_pipeline` runs the steps in order |
| `app/gemini_client.py` | Sankirth | All Gemini calls, prompts, demo cache |
| `app/storage.py` | Sankirth | Cloud Storage uploads |
| `app/bq.py` | Sankirth | BigQuery tables, saving a run, loading past requirements |
| `app/verify.py` | Sankirth | Evidence verification (already written and tested) |
| `app/gaps.py` | Sankirth | Missing-area check (already written and tested) |
| `app/config.py`, `.env` | Sankirth | Settings and secrets |
| `app/schemas.py` | **Both** | THE CONTRACT. Change only after both agree |
| `scripts/*`, `tests/*` | Sankirth | Smoke test, extraction tuning, tests |

### 4.2 The contract (do not change without agreement)

Frontend calls only these (all in `app/orchestrator.py`):

```python
load_demo_files() -> dict[str, bytes]
run_pipeline(project_id: str, files: dict[str, bytes], demo_mode: bool, on_progress: Callable[[str], None] | None) -> RunResult
set_review_status(result: RunResult, requirement_id: str, status: str) -> RunResult
```

Data shapes (`app/schemas.py`, exact file):

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

Rule: **file bytes never travel inside `RunResult`.** The UI keeps the uploaded `files` dict in `st.session_state` and passes the matching bytes to `render_evidence(ev, files.get(ev.file_name))`.

### 4.3 How the pieces connect

```
Streamlit app.py  --calls-->  orchestrator.run_pipeline()
    1. storage.py      uploads raw files to Cloud Storage (live mode only)
    2. gemini_client   sends files + prompt to Gemini on Vertex AI, gets JSON (live) or cached JSON (demo)
    3. verify.py       checks every quote and box; marks requirements verified/unverified (always real)
    4. gaps.py         finds missing areas -> clarification questions (always real)
    5. gemini_client   detect_conflicts() against past requirements (live, if time allows)
    6. bq.py           saves runs, artifacts, requirements, evidence, conflicts, gaps (live)
    7. returns RunResult  -->  app.py shows table + render.render_evidence() + export.build_brd_markdown()
```

---

## 5. The plan, step by step

Step template: **ID | Owner | Goal | Do | Done when | If it fails**.

### PHASE 0: Wednesday 14 Oct (tonight, 2 to 3 hours): setup only, no feature code

**0.1 | Both | Agree the plan**
- Do: read sections 0 to 4. Send the organizer message in section 2.
- Done when: both say "contract v1 accepted" in your chat.

**0.2 | Sankirth | Google Cloud project, credits, APIs**
- Do:
  1. Open the Google Cloud console, select or create the project; confirm credits/billing with the organizers.
  2. Run:
  ```
  gcloud config set project YOUR_PROJECT_ID
  gcloud services enable aiplatform.googleapis.com bigquery.googleapis.com storage.googleapis.com
  ```
- Done when: both commands finish without errors.
- If it fails: "billing not enabled" -> link a billing account or credits; "permission denied" -> you need Owner or Editor on the project.

**0.3 | Sankirth | Authenticate from your laptop**
- Do:
  ```
  gcloud auth application-default login
  gcloud auth application-default set-quota-project YOUR_PROJECT_ID
  ```
- Done when: the browser login finishes and the second command prints success.

**0.4 | Sankirth | Bucket, dataset, settings**
- Do:
  ```
  gcloud storage buckets create gs://YOUR_UNIQUE_BUCKET --location=us-central1 --uniform-bucket-level-access --public-access-prevention
  bq --location=US mk --dataset YOUR_PROJECT_ID:brd_agent
  ```
  Then copy `.env.example` to `.env` and fill in `GCP_PROJECT_ID`, `GCS_BUCKET`. Set `DEMO_MODE=false` only when you test live.
- Done when: both commands succeed and `.env` is filled (never commit `.env`).
- If it fails: bucket names are global, so try another name; if the `--public-access-prevention` flag is rejected, set it in the console (Bucket > Permissions > Public access prevention).

**0.5 | Sankirth | Put the starter repo on GitHub**
- Do: unzip `brd-agent-starter.zip`, create the repo content from it, push to `main`, add Yashwanth as collaborator.
  ```
  cd brd-agent && git init && git add . && git commit -m "starter" && git branch -M main
  git remote add origin YOUR_REPO_URL && git push -u origin main
  ```
- Done when: Yashwanth can clone it.
- Note: if the organizers say pre-written code is not allowed (section 2), push only docs and keep the code local until the start.

**0.6 | Yashwanth | Run the starter in demo mode (no cloud needed)**
- Do:
  ```
  git clone YOUR_REPO_URL && cd brd-agent
  python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  cp .env.example .env                                  # Windows: copy .env.example .env
  python scripts/make_demo_data.py
  python tests/test_core.py
  streamlit run app/app.py
  ```
  In the app: tick "Use the sample demo files instead", press "Process files", open the Requirements tab, pick FR-01.
- Done when: 6 tests print PASS, the table shows FR-01 to FR-04, the evidence viewer shows a red box on the image and a highlighted PDF page, and the Conflicts tab shows one conflict.

**0.7 | Yashwanth | Create the real demo files**
- Do:
  1. Draw a login screen on a whiteboard or paper with a dark marker: logo, Email field, Password field, "Sign in" button, a line "or", a button "Continue with Google". Keep handwriting big and neat.
  2. Photograph it straight on in daylight, no glare, file under 4 MB, save as `demo/data/auth_wireframe.jpg` (same name).
  3. Write `client_notes.pdf` as a **text-based PDF** (export from Word or Google Docs, not a scan). Include these three sentences exactly: "Users should be able to sign in with their Google accounts." "Admins need to export audit logs as CSV." "The system should support 500 concurrent users."
  4. Keep `meeting_notes.txt` (line 3: "Sessions expire after 15 minutes of inactivity.") and `meeting_notes_v2.txt` (line 3: "Session timeout is now 30 minutes."). Do not mention data retention or privacy anywhere (that is the planted gap).
- Done when: the four files exist in `demo/data/`.
- Important: the built-in demo output was written for the placeholder files. After you replace the files, the box position and quotes may no longer match. This is expected: Sankirth regenerates the demo cache from real Gemini output in step 3.3. Until then, use the placeholder files for UI work.

**0.8 | Both | Freeze the contract**
- Do: `git tag contract-v1 && git push --tags`.
- Done when: the tag exists on GitHub.

---

### DAY 1: Thursday 15 Oct. Goal: real Gemini end to end

**1.1 | Sankirth | Run the cloud smoke test**
- Do: `python scripts/smoke_test.py`
- Done when: all four lines print PASS (Cloud Storage, Gemini text, Gemini image box, BigQuery).
- If it fails: see section 9. Do not move on until this is green.

**1.2 | Sankirth | Check the image box on the real photo**
- Do: replace `demo/data/auth_wireframe.jpg` with Yashwanth's real photo (he pushes it first), run `python scripts/smoke_test.py`, open `smoke_box.png`.
- Done when: the red box sits on the "Continue with Google" button.
- If the box is off: (a) retake a clearer photo, (b) try `GEMINI_MODEL=gemini-2.5-pro` in `.env`, (c) as fallback, make the UI show the image next to the quote without a box. Tell Yashwanth by the end of the day.

**1.3 | Sankirth | Tune the extraction prompt**
- Do: `python scripts/try_extract.py` and edit `EXTRACTION_PROMPT` in `app/gemini_client.py` until the three demo files give FR-01 to FR-03 style requirements and the evidence shows "OK".
- Done when: at least 3 requirements, and every printed evidence line for them says OK. Any "NOT VERIFIED" line is a prompt problem to fix (usually the quote is paraphrased: strengthen the "verbatim" rule).

**1.4 | Sankirth | Create BigQuery tables**
- Do: `python -c "from app import bq; bq.ensure_tables()"`
- Done when: six tables (`runs`, `artifacts`, `requirements`, `evidence`, `conflicts`, `gaps`) appear in the `brd_agent` dataset in the console.

**1.5 | Sankirth | Run the pipeline live**
- Do: set `DEMO_MODE=false` in `.env`, run the app, upload the three stage-1 files, press "Process files".
- Done when: the table shows requirements from real Gemini output and the BigQuery `requirements` and `evidence` tables contain rows.

**1.6 | Yashwanth | UI pass 1 (all in demo mode)**
- Do: improve `app/app.py`: clear file list, progress messages, requirements table, evidence viewer layout (side by side), Demo-mode badge, friendly errors. Keep all calls going through the contract. Do not import `gemini_client`, `bq` or `storage`.
- Done when: a person who has never seen the app can upload, process and open an evidence view without help.

**1.7 | Both | Integration run 1 (evening, one laptop)**
- Do: pull both sets of changes, run live mode with the three real files, open FR-01's evidence. Then `git tag day1-ok && git push --tags`.
- Done when: acceptance tests A1 and A2 (section 6) pass.

---

### DAY 2: Friday 16 Oct. Goal: trust features and persistence

**2.1 | Sankirth | Harden verification**
- Do: run the live pipeline on the real files five times. For every unverified item, look at `verify_note`. Add a test in `tests/test_core.py` for each real failure you see. Allowed change: normalizing whitespace or punctuation. **Not allowed:** loosening matching until fake quotes pass. `test_fake_quote_is_unverified` must keep passing.
- Done when: `python tests/test_core.py` is green and real runs give mostly verified items.

**2.2 | Sankirth | Prove BigQuery persistence**
- Do: in the BigQuery console run this query (replace PROJECT with your project ID), then save a screenshot for the demo:
  ```sql
  SELECT display_id, text, verification_status
  FROM `PROJECT.brd_agent.requirements`
  ORDER BY created_at DESC LIMIT 20
  ```
- Done when: the query shows your latest run (acceptance A6).

**2.3 | Sankirth | Conflict detection with history**
- Do: run stage 1 live (three files), then stage 2 live with only `meeting_notes_v2.txt` in the same project name. The orchestrator loads past requirements from BigQuery and calls `gemini_client.detect_conflicts`.
- Done when: the Conflicts tab shows the 15 vs 30 minute contradiction (acceptance A4).
- If it fails: print the JSON sent to the conflict prompt; check that `bq.load_active_requirements` returned the stage-1 rows (they must have `verification_status='verified'`).

**2.4 | Sankirth | Gap questions**
- Do: confirm the data-retention question appears for the demo files. Tune keywords in `app/gaps.py` if a category is wrongly marked as covered.
- Done when: acceptance A5 passes.

**2.5 | Yashwanth | Evidence viewer final**
- Do: check each evidence kind with REAL output: image box, PDF page highlight, text line. Show a clear warning for unverified items. Add approve/reject and show review status in the table.
- Done when: acceptance A2 passes with real data.

**2.6 | Yashwanth | BRD tab and export**
- Do: check the Markdown BRD against section 13 of the PRD structure: every confirmed line has a source, unverified items sit in their own section, conflicts and open questions are listed. Only after that works, optionally add DOCX with `python-docx`.
- Done when: acceptance A7 passes.

**2.7 | Yashwanth | Conflicts and gaps tab polish**
- Do: show severity colors, resolved checkbox, answer boxes for gap questions.
- Done when: both tabs read clearly on a projector-size screen.

**2.8 | Both | Integration run 2 (evening)**
- Do: Yashwanth does a **fresh clone** on his laptop and runs demo mode. Sankirth runs live mode on his. Fix anything that differs. `git tag day2-ok && git push --tags`.
- **Cut decision (end of Friday):** if acceptance A1 to A3 and A6 to A7 are not all green, drop everything in section 8 from the top, and fix only those.

---

### DAY 3: Saturday 17 Oct. Goal: freeze, cache, rehearse

**3.1 | Both | Bug bash (one hour)**
- Do: try to break the app: wrong file types, empty upload, huge file, a PDF with no text, no network. Fix only crashes and wrong output. No new features.

**3.2 | Both | FEATURE FREEZE**
- Do: freeze at least 6 hours before your slot (or by noon, whichever is earlier). **[CONFIRM] slot time.** After the freeze only fix bugs that break the demo.

**3.3 | Sankirth | Build the demo cache from the final files**
- Do: with the final files, run live in the demo order: first the three stage-1 files, then only `meeting_notes_v2.txt`. Each live run writes `demo/cache/run_<hash>.json`. Commit and push the cache files.
- Done when: switching to demo mode and repeating both runs gives the same results with the network off.

**3.4 | Yashwanth | Replace the concept screenshot with a real one**
- Do: take a real screenshot of the app showing upload, requirements and an evidence view. Update `docs/Screenshot...png`, the README, and the screenshot slide in the deck. Keep wording honest: "working prototype" only for what truly works.

**3.5 | Both | Offline test**
- Do: turn off Wi-Fi on both laptops, run demo mode end to end.
- Done when: acceptance A8 passes on both laptops.

**3.6 | Yashwanth | Backup video**
- Do: screen-record the full 3-minute demo (section 7) with narration. Save it on both laptops and a phone.

**3.7 | Both | Rehearse three times**
- Do: time the demo; decide who talks and who clicks; prepare answers to section 7.3.

**3.8 | Both | Final checklist (before leaving)**
- Chargers, hotspot, both laptops charged. `gcloud auth application-default login` done recently (tokens can expire). `.env` correct. Repo pushed, `git tag final`. Deck updated. Backup video on a phone.

---

## 6. Acceptance tests (the product is demo-ready when all MUST items pass)

| ID | Priority | Test | Pass condition |
|---|---|---|---|
| A1 | MUST | Upload the 3 stage-1 files in live mode | 3 or more requirements appear, each with evidence, in about a minute (measure it; do not promise a number) |
| A2 | MUST | Click FR-01 | Box on the whiteboard image and highlighted passage on the PDF page both show |
| A3 | MUST | Add a fake quote to a test requirement | It becomes `unverified` and is excluded from the confirmed BRD sections (test exists: `test_unverified_requirement_excluded_from_brd`) |
| A4 | SHOULD | Run stage 2 (`meeting_notes_v2.txt`) after stage 1 | The 15 vs 30 minute conflict is flagged |
| A5 | SHOULD | Check gaps | A data-retention/privacy question appears |
| A6 | MUST | BigQuery console query | Shows requirements and evidence rows from the run |
| A7 | MUST | Download the BRD | Markdown has a citation on every confirmed line and separate sections for unverified items, conflicts, open questions |
| A8 | MUST | Network off, demo mode on | Whole demo runs from the cache with the "Demo mode" badge visible |

---

## 7. Demo plan

### 7.1 Three-minute script
1. One sentence on the problem: scattered files, nobody can say where a requirement came from.
2. Upload the three stage-1 files. Show progress.
3. Show the requirements table. Click FR-01: show the box on the whiteboard and the highlighted PDF quote.
4. Say: "Anything without verified evidence is never shown as confirmed."
5. Upload `meeting_notes_v2.txt`: show the flagged 15 vs 30 minute conflict, then the data-retention question.
6. Show the BigQuery console with the stored rows.
7. Download the BRD and point to the citations.
8. Close: "The BRD that shows its work."

### 7.2 Fallback
If anything fails live, switch on Demo mode and say clearly: "this is running from a saved result". Then play the backup video if the app itself fails.

### 7.3 Likely judge questions and honest answers
- **Why not just upload the files to Gemini?** A single prompt cannot verify its own quotes or compare against past runs. We check every quote against the source, flag contradictions, and keep history in BigQuery.
- **How do you stop hallucinations?** We reduce unsupported requirements: no verified evidence, no confirmed requirement. Gemini can still misread an input, so a person reviews before sign-off.
- **Is it an autonomous agent?** It is a multi-step workflow with decisions (drop unverified, flag conflicts, ask questions). Vertex AI runs Gemini; our Python orchestrator runs the workflow.
- **Does it scale?** It is built on managed Google Cloud services and designed to scale. We have not load-tested it.
- **What did you build in the hackathon vs plan?** Answer from the build status in your README. Only claim what you ran.
- **What about scanned PDFs?** Not supported yet; OCR is a next step.

---

## 8. Cut list (drop in this order if behind)

1. Image second check (crop and re-ask Gemini).
2. DOCX export.
3. Approve/reject per requirement.
4. Grounding loop and conflict detection.
5. Gap questions.

**Never cut:** evidence viewer, evidence verification, BigQuery saving, demo mode. Anything cut is described in the pitch as "planned", never shown half-working.

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `DefaultCredentialsError` | Not logged in | `gcloud auth application-default login` |
| `403 PERMISSION_DENIED` on Vertex AI | Missing role or API | Enable `aiplatform.googleapis.com`; grant `Vertex AI User` to your account |
| `403` on Storage | Missing role or wrong bucket name | Grant `Storage Object Admin` on the bucket; check `GCS_BUCKET` |
| BigQuery `403` / `Access Denied` | Missing roles | Grant `BigQuery Data Editor` and `BigQuery Job User` |
| `404 model not found` | Model ID or region | Check Model Garden for current IDs; set `GEMINI_MODEL`; try `us-central1` |
| `429` / quota errors | Rate limit | Wait, reduce calls, use cached demo mode |
| Structured output error / schema rejected | Vertex supports a subset of JSON schema | Keep schemas flat; fall back to `response_mime_type="application/json"` without `response_schema` and validate with Pydantic |
| Quotes always `unverified` | Gemini paraphrases, or the PDF is scanned | Strengthen the "verbatim" prompt rule; use a text-based PDF |
| Box misplaced | Photo quality or model | Retake photo; try `gemini-2.5-pro`; fall back to image + quote |
| `ModuleNotFoundError: app` | Wrong working directory | Run commands from the repo root; use `streamlit run app/app.py` |
| BigQuery load error with pandas | Missing packages | `pip install pyarrow db-dtypes` |
| Streamlit state lost | Streamlit reruns on every click | Keep results in `st.session_state` (the starter already does) |

---

## 10. Prompt templates for LLM assistants

**Step prompt (fill the brackets):**
```
[Paste the Master Context from section 1]

I am [Sankirth | Yashwanth]. I am working on step [ID] of the build guide: [paste that step's text].
Files you may edit: [list from section 4.1].
Files you must NOT change: app/schemas.py and the function signatures in app/orchestrator.py.
Here are the current contents of the files: [paste files].
Task: complete this step. Return full replacement code for each changed file, a command to test it, and the expected output. If something is unclear, state your assumption instead of inventing details.
```

**Review prompt:**
```
[Master Context]
Review this change against the guide. Check: (1) does it keep the contract in schemas.py and orchestrator.py unchanged, (2) does verification still reject fake quotes, (3) are there any claims or features the code does not actually implement, (4) what is the simplest way to test it. Here is the diff: [paste diff]
```

**Debug prompt:**
```
[Master Context]
Step [ID] fails. Command run: [command]. Full error: [paste]. The relevant file: [paste]. List the 3 most likely causes in order, and the exact check for each. Do not rewrite unrelated code.
```

---

## 11. Honesty guardrails (for the pitch, README and slides)

| Do not say | Say instead |
|---|---|
| Prevents hallucinations | Reduces unsupported requirements by grounding outputs in source evidence and verifying quotes |
| 100% cited / accurate | Confirmed requirements require verified source evidence |
| Auto-scales | Built on managed Google Cloud services, designed to scale, not load-tested |
| Secure by default | Raw artifacts are stored in a private Cloud Storage bucket with IAM-controlled access |
| Vertex AI orchestrates the pipeline | Vertex AI runs Gemini; our Python orchestrator runs the workflow |
| Weeks to minutes | Design goal; we measured [your measured time] on the demo files (only if you measured it) |
| Production-ready | Hackathon prototype |

Use the status words MVP, If time allows, Next steps. Label the README and deck honestly according to what you actually ran.

---

## 12. Command cheat sheet

```
# setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/make_demo_data.py

# check
python tests/test_core.py
python scripts/smoke_test.py          # cloud checks (needs .env + gcloud login)
python scripts/try_extract.py         # tune the Gemini prompt (live)

# run
streamlit run app/app.py

# git
git pull --rebase && git add . && git commit -m "message" && git push
git tag day1-ok && git push --tags
```

## 13. File tree

```
brd-agent/
  README.md  requirements.txt  .env.example  .gitignore
  app/
    app.py            (Yashwanth)  Streamlit UI
    render.py         (Yashwanth)  evidence -> image/text for the UI
    export.py         (Yashwanth)  BRD Markdown
    orchestrator.py   (Sankirth)   run_pipeline = the workflow
    gemini_client.py  (Sankirth)   Gemini calls, prompts, demo cache
    storage.py        (Sankirth)   Cloud Storage
    bq.py             (Sankirth)   BigQuery
    verify.py         (Sankirth)   evidence verification
    gaps.py           (Sankirth)   missing-area check
    config.py         (Sankirth)   settings
    schemas.py        (BOTH)       the contract
  demo/data/   demo/cache/
  scripts/  make_demo_data.py  smoke_test.py  try_extract.py
  tests/    test_core.py
```
