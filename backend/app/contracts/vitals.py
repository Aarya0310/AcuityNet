from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.contracts.patients import PatientSummary


class FreshnessState(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    DISCONNECTED = "disconnected"
    UNAVAILABLE = "unavailable"


class Provenance(BaseModel):
    source_kind: Literal["synthetic", "retrospective", "replay"]
    source_name: str
    scenario_id: str | None
    scenario_version: str | None
    is_live_bedside_feed: Literal[False]


class SyntheticProvenance(BaseModel):
    source_kind: Literal["synthetic"]
    source_name: Literal["acuitynet-simulator"]
    scenario_id: str
    scenario_version: str
    is_live_bedside_feed: Literal[False]


class AdvanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tick: int | None = Field(default=None, ge=0, le=4)
    interval: int | str | None = None

    @model_validator(mode="after")
    def require_bounded_operation(self) -> "AdvanceRequest":
        supported = (5, 10, 30)
        if self.tick is None and self.interval not in supported:
            raise ValueError("Automatic advancement requires interval 5, 10, or 30")
        if self.tick is not None and self.interval not in (None, *supported):
            raise ValueError("Unsupported refresh interval")
        return self


class VitalObservationResponse(BaseModel):
    patient_id: str
    patient: PatientSummary
    bed_id: str
    unit: str
    sequence: int
    observed_at: datetime
    received_at: datetime
    spo2_percent: float = Field(ge=0, le=100)
    heart_rate_bpm: float = Field(ge=0, le=300)
    respiratory_rate_bpm: float = Field(ge=0, le=100)
    systolic_bp_mmhg: float = Field(ge=0, le=300)
    diastolic_bp_mmhg: float = Field(ge=0, le=300)
    temperature_c: float = Field(ge=20, le=45)
    provenance: SyntheticProvenance
    freshness: FreshnessState
    prototype_label: str


def resolve_freshness(
    received_at: datetime | None,
    now: datetime,
    *,
    transport_ok: bool = True,
) -> FreshnessState:
    if received_at is None:
        return FreshnessState.UNAVAILABLE
    if not transport_ok:
        return FreshnessState.DISCONNECTED
    if received_at.tzinfo is None:
        received_at = received_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    age_seconds = (now - received_at).total_seconds()
    if age_seconds <= 15:
        return FreshnessState.FRESH
    if age_seconds <= 60:
        return FreshnessState.STALE
    return FreshnessState.DISCONNECTED
