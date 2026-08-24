from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.app.persistence.models import (
    Admission,
    Bed,
    Configuration,
    History,
    Nurse,
    Patient,
    VitalObservation,
)


def reset_demo_data(session: Session) -> None:
    for model in (VitalObservation, Admission, History, Bed, Nurse, Configuration, Patient):
        session.execute(delete(model))
    session.flush()