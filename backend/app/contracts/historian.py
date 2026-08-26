from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.contracts.alerts import AlertResponse
from backend.app.contracts.predictions import PredictionResponse


class HistorianFact(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    fact_id: str
    category: Literal["diagnosis", "medication", "lab", "icu_event"]
    label: str
    value: str | None
    unit: str | None
    effective_at: datetime
    source_kind: Literal["synthetic"]
    source_name: str


class RuleEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_key: str
    rule_name: str
    rule_version: str
    category: Literal["diagnosis", "medication", "lab", "icu_event"]
    fact_id: str
    delta: float = Field(ge=-1, le=1)
    explanation: str
    evaluated_at: datetime


class TimelineEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entry_id: str
    entry_type: Literal["fact", "prediction", "alert", "audit", "annotation"]
    occurred_at: datetime
    title: str
    detail: str


class AnnotationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=500)


class AnnotationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    annotation_id: int
    author_id: str
    text: str
    created_at: datetime
    source_label: str


class HistorianResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patient_id: str
    patient_name: str
    admission_id: str
    admitted_at: datetime
    bed_id: str
    unit: str
    current_prediction: PredictionResponse
    baseline_score: float = Field(ge=0, le=1)
    contextual_status: Literal["complete", "incomplete"]
    contextual_score: float | None = Field(default=None, ge=0, le=1)
    facts: list[HistorianFact]
    rule_evaluations: list[RuleEvaluation]
    missing_evidence: list[str]
    annotations: list[AnnotationResponse]
    alert: AlertResponse | None
    timeline: list[TimelineEntry]
    prototype_label: str
    provenance: Literal["synthetic", "research-prototype"]