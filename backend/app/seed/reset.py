from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.app.persistence.models import (
    Admission,
    Alert,
    AlertEvent,
    AuditEvent,
    Bed,
    Configuration,
    DispatchDecision,
    DispatchEvaluation,
    History,
    HistorianRuleEvaluation,
    HistorianRuleDefinition,
    Nurse,
    Patient,
    PatientContextFact,
    PredictionEvidence,
    TimelineAnnotation,
    User,
    VitalObservation,
)


def reset_demo_data(session: Session) -> None:
    for model in (
        TimelineAnnotation,
        DispatchDecision,
        DispatchEvaluation,
        HistorianRuleEvaluation,
        HistorianRuleDefinition,
        PatientContextFact,
        AlertEvent,
        AuditEvent,
        Alert,
        PredictionEvidence,
        VitalObservation,
        Admission,
        History,
        Bed,
        Nurse,
        User,
        Configuration,
        Patient,
    ):
        session.execute(delete(model))
    session.flush()