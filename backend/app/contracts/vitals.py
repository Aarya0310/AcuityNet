from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Provenance(BaseModel):
    source_kind: Literal["synthetic", "retrospective", "replay"]
    source_name: str
    scenario_id: str | None
    scenario_version: str | None
    is_live_bedside_feed: Literal[False]


class AdvanceRequest(BaseModel):
    tick: int = Field(ge=0, le=4)


class VitalObservationResponse(BaseModel):
    patient_id: str
    bed_id: str
    sequence: int
    observed_at: datetime
    received_at: datetime
    spo2_percent: float = Field(ge=0, le=100)
    heart_rate_bpm: float = Field(ge=0, le=300)
    respiratory_rate_bpm: float = Field(ge=0, le=100)
    systolic_bp_mmhg: float = Field(ge=0, le=300)
    diastolic_bp_mmhg: float = Field(ge=0, le=300)
    temperature_c: float = Field(ge=20, le=45)
    provenance: Provenance
    freshness: Literal["fresh", "stale", "disconnected", "unavailable"]
    prototype_label: str
