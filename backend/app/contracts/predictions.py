from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from backend.app.contracts.vitals import SyntheticProvenance, VitalObservationResponse


class PredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patient_id: str
    bed_id: str
    event: str
    probability: float
    score: float
    level: Literal["low", "moderate", "high", "critical"]
    horizon_minutes: int
    timestamp: datetime
    current_vitals: VitalObservationResponse
    provenance: SyntheticProvenance
    prototype_label: str
    contract_version: str
    source_kind: Literal["ml", "deterministic_fallback"]
    source_version: str
    fallback_reason: str | None = None