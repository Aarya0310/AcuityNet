from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"
    patient_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)


class Bed(Base):
    __tablename__ = "beds"
    bed_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), unique=True)


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    password_digest: Mapped[str] = mapped_column(String(256), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    nurse: Mapped["Nurse | None"] = relationship(back_populates="user", uselist=False)


class Admission(Base):
    __tablename__ = "admissions"
    admission_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), unique=True)
    admitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Nurse(Base):
    __tablename__ = "nurses"
    nurse_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), unique=True)
    status_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    workload_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    proximity_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acuity_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    proximity_km: Mapped[float | None] = mapped_column(Float)
    workload_active: Mapped[int | None] = mapped_column(Integer)
    workload_capacity: Mapped[int | None] = mapped_column(Integer)
    acuity_compatibility: Mapped[float | None] = mapped_column(Float)
    user: Mapped[User | None] = relationship(back_populates="nurse")


class History(Base):
    __tablename__ = "histories"
    history_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), unique=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)


class Configuration(Base):
    __tablename__ = "configurations"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(String(200), nullable=False)


class VitalObservation(Base):
    __tablename__ = "vital_observations"
    __table_args__ = (UniqueConstraint("patient_id", "sequence", name="uq_observation_patient_sequence"),)
    observation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), nullable=False)
    bed_id: Mapped[str] = mapped_column(ForeignKey("beds.bed_id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    spo2_percent: Mapped[float] = mapped_column(Float, nullable=False)
    heart_rate_bpm: Mapped[float] = mapped_column(Float, nullable=False)
    respiratory_rate_bpm: Mapped[float] = mapped_column(Float, nullable=False)
    systolic_bp_mmhg: Mapped[float] = mapped_column(Float, nullable=False)
    diastolic_bp_mmhg: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(80), nullable=False)
    scenario_version: Mapped[str] = mapped_column(String(20), nullable=False)


class PredictionEvidence(Base):
    __tablename__ = "prediction_evidence"
    evidence_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), nullable=False)
    observation_id: Mapped[int] = mapped_column(ForeignKey("vital_observations.observation_id"), nullable=False, unique=True)
    observation_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    event: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    horizon_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_version: Mapped[str] = mapped_column(String(40), nullable=False)
    fallback_reason: Mapped[str | None] = mapped_column(String(200))
    fallback_metadata: Mapped[str] = mapped_column(String(500), nullable=False, default="{}")
    prediction_contract_version: Mapped[str] = mapped_column(String(40), nullable=False)
    synthetic_source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    synthetic_source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    synthetic_scenario_id: Mapped[str] = mapped_column(String(80), nullable=False)
    synthetic_scenario_version: Mapped[str] = mapped_column(String(20), nullable=False)
    prototype_label: Mapped[str] = mapped_column(String(160), nullable=False)
    effective_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    rule_version: Mapped[str] = mapped_column(String(40), nullable=False)
    server_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("patient_id", "episode_key", name="uq_alert_patient_episode"),)
    alert_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), nullable=False)
    bed_id: Mapped[str] = mapped_column(ForeignKey("beds.bed_id"), nullable=False)
    episode_key: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="generated")
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("prediction_evidence.evidence_id"), nullable=False)
    deduplication_status: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AlertEvent(Base):
    __tablename__ = "alert_events"
    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.alert_id"), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome: Mapped[str] = mapped_column(String(24), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(80))
    outcome: Mapped[str] = mapped_column(String(24), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    details: Mapped[str] = mapped_column(String(1000), nullable=False, default="{}")


class PatientContextFact(Base):
    __tablename__ = "patient_context_facts"
    fact_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    value: Mapped[str | None] = mapped_column(String(120))
    unit: Mapped[str | None] = mapped_column(String(32))
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class HistorianRuleDefinition(Base):
    __tablename__ = "historian_rule_definitions"
    rule_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    rule_key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(String(240), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class HistorianRuleEvaluation(Base):
    __tablename__ = "historian_rule_evaluations"
    evaluation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), nullable=False)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("prediction_evidence.evidence_id"), nullable=False)
    rule_id: Mapped[str] = mapped_column(ForeignKey("historian_rule_definitions.rule_id"), nullable=False)
    fact_id: Mapped[str | None] = mapped_column(ForeignKey("patient_context_facts.fact_id"))
    rule_key: Mapped[str] = mapped_column(String(80), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(40), nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(String(240), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TimelineAnnotation(Base):
    __tablename__ = "timeline_annotations"
    annotation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), nullable=False)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_label: Mapped[str] = mapped_column(String(80), nullable=False)


class DispatchEvaluation(Base):
    __tablename__ = "dispatch_evaluations"
    evaluation_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), nullable=False)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.alert_id"), nullable=False)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("prediction_evidence.evidence_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    alert_fresh_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    candidate_fresh_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    recommendation_nurse_id: Mapped[str | None] = mapped_column(String(32))
    weights: Mapped[str] = mapped_column(Text, nullable=False)
    candidates: Mapped[str] = mapped_column(Text, nullable=False)
    exclusions: Mapped[str] = mapped_column(Text, nullable=False)
    source_fingerprint: Mapped[str] = mapped_column(String(120), nullable=False)
    recommendation_context: Mapped[str] = mapped_column(String(240), nullable=False)
    prototype_label: Mapped[str] = mapped_column(String(160), nullable=False)


class DispatchDecision(Base):
    __tablename__ = "dispatch_decisions"
    decision_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[str] = mapped_column(ForeignKey("dispatch_evaluations.evaluation_id"), nullable=False)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.alert_id"), nullable=False)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    decision_type: Mapped[str] = mapped_column(String(16), nullable=False)
    selected_nurse_id: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(240), nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
