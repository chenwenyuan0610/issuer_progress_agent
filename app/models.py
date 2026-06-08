from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field

Stage = Literal[
    "Discovery",
    "Planning",
    "Implementation",
    "Testing",
    "Go-Live",
    "Post Go-Live",
]

ProgressStatus = Literal["Not started", "In progress", "Blocked", "Done"]


class IssuerCreateRequest(BaseModel):
    issuer_name: str = Field(..., examples=["Kpay"])
    issuer_oid: Optional[str] = None
    region: Optional[str] = None
    service_type: list[str] = Field(default_factory=lambda: ["Onboarding"])
    current_stage: Stage = "Discovery"
    progress_status: ProgressStatus = "Not started"
    latest_progress: Optional[str] = None
    next_action: Optional[str] = None
    owner: Optional[str] = None
    go_live_date: Optional[date] = None


class ProgressUpdateRequest(BaseModel):
    current_stage: Optional[Stage] = None
    progress_status: Optional[ProgressStatus] = None
    latest_progress: str
    next_action: Optional[str] = None
    blocker: Optional[str] = None
    owner: Optional[str] = None
    updated_by: str = "AI Agent"


class NoteCreateRequest(BaseModel):
    note_type: Literal["Meeting", "Email", "Issue", "Requirement", "Other"] = "Other"
    title: str
    content: str
    source_date: Optional[date] = None
    created_by: str = "AI Agent"


class IssuerProgress(BaseModel):
    page_id: str
    issuer_name: str
    issuer_oid: Optional[str] = None
    region: Optional[str] = None
    service_type: list[str] = []
    current_stage: Optional[str] = None
    progress_status: Optional[str] = None
    latest_progress: Optional[str] = None
    next_action: Optional[str] = None
    blocker: Optional[str] = None
    owner: Optional[str] = None
    last_update: Optional[str] = None
    go_live_date: Optional[str] = None
