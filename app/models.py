from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field

Stage = Literal[
    "Not Started",
    "Requirement Confirming",
    "UI Confirming",
    "API Integration",
    "SIT",
    "SIT Completed",
    "UAT",
    "UAT Completed",
    "Go-Live Preparation",
    "Production",
    "Suspended",
    "Closed",
]

RiskLevel = Literal["Low", "Medium", "High"]
ProgressStatus = Literal["Not Started", "In Progress", "Blocked", "Done"]


class IssuerCreateRequest(BaseModel):
    issuer_name: str = Field(..., examples=["Kpay"])
    issuer_oid: Optional[str] = None
    region: Optional[str] = None
    service_type: list[str] = Field(default_factory=lambda: ["ACS"])
    current_stage: Stage = "Not Started"
    progress_status: ProgressStatus = "Not Started"
    latest_progress: Optional[str] = None
    next_action: Optional[str] = None
    risk_level: RiskLevel = "Low"
    owner: Optional[str] = None
    go_live_date: Optional[date] = None


class ProgressUpdateRequest(BaseModel):
    current_stage: Optional[Stage] = None
    progress_status: Optional[ProgressStatus] = None
    latest_progress: str
    next_action: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    blocker: Optional[str] = None
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
    risk_level: Optional[str] = None
    blocker: Optional[str] = None
    owner: Optional[str] = None
    last_update: Optional[str] = None
    go_live_date: Optional[str] = None
