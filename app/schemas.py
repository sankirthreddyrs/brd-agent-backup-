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
