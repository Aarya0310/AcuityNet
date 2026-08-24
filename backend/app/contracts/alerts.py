from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.contracts.vitals import SyntheticProvenance

AlertPriority = Literal["high", "critical"]
DeduplicationStatus = Literal["new_alert", "reused_active", "suppressed_cooldown", "rearmed"]


class AlertResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alert_id: int
    patient_id: str
    bed_id: str
    priority: AlertPriority
    state: Literal["generated", "assigned", "acknowledged", "responded", "resolved"]
    risk_score: float = Field(ge=0, le=1)
    risk_level: Literal["low", "moderate", "high", "critical"]
    event: str
    probability: float = Field(ge=0, le=1)
    horizon_minutes: int = Field(ge=0)
    observation_sequence: int
    timestamp: datetime
    provenance: SyntheticProvenance
    prototype_label: str
    prediction_source_kind: Literal["ml", "deterministic_fallback"]
    prediction_source_version: str
    fallback_reason: str | None
    prediction_contract_version: str
    effective_threshold: float
    rule_version: str
    deduplication_status: DeduplicationStatus
    created_at: datetime