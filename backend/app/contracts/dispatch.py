from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.contracts.alerts import AlertResponse


class DispatchCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nurse_id: str
    display_name: str
    eligible: bool
    exclusion_reasons: list[str] = Field(default_factory=list)
    rank: int | None = None
    score: float | None = Field(default=None, ge=0, le=1)
    components: dict[str, float] = Field(default_factory=dict)
    contributions: dict[str, float] = Field(default_factory=dict)
    proximity_km: float | None = None
    workload_active: int | None = None
    workload_capacity: int | None = None
    acuity_compatibility: float | None = None
    freshness: dict[str, datetime | None] = Field(default_factory=dict)


class DispatchEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evaluation_id: str
    patient_id: str
    alert_id: int
    evidence_id: int
    created_at: datetime
    alert_fresh_at: datetime
    candidate_fresh_at: datetime
    status: Literal["ready", "blocked", "no_eligible_candidate"]
    recommendation_nurse_id: str | None
    weights: dict[str, float]
    candidates: list[DispatchCandidate]
    exclusions: list[DispatchCandidate]
    recommendation_context: str
    prototype_label: str


class DispatchDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evaluation_id: str = Field(min_length=1, max_length=40)
    nurse_id: str = Field(min_length=1, max_length=32)
    reason: str = Field(min_length=3, max_length=240)
