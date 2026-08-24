from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.app.persistence.models import (
    Admission,
    Alert,
    AlertEvent,
    AuditEvent,
    Bed,
    Configuration,
    History,
    Nurse,
    Patient,
    PredictionEvidence,
    User,
    VitalObservation,
)


def reset_demo_data(session: Session) -> None:
    for model in (
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