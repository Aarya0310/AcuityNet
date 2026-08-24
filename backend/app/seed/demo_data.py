from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.persistence.models import Admission, Bed, Configuration, History, Nurse, Patient


def seed_demo_data(session: Session) -> None:
    if session.get(Patient, "P-1042") is None:
        session.add(Patient(patient_id="P-1042", display_name="Fictional Patient 1042"))
    session.flush()
    values = [
        (Bed, "ICU-12", {"unit": "ICU", "patient_id": "P-1042"}),
        (Nurse, "N-SARAH", {"display_name": "Sarah Morgan", "available": True}),
        (History, "H-P-1042", {"patient_id": "P-1042", "summary": "Fictional demonstration history."}),
    ]
    for model, identifier, fields in values:
        key = "bed_id" if model is Bed else "nurse_id" if model is Nurse else "history_id"
        if session.get(model, identifier) is None:
            session.add(model(**{key: identifier}, **fields))
    session.flush()
    if session.query(Admission).filter_by(admission_id="A-P-1042").first() is None:
        session.add(Admission(admission_id="A-P-1042", patient_id="P-1042", admitted_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
    for key, value in {"freshness_fresh_seconds": "15", "freshness_stale_seconds": "60", "refresh_intervals": "5,10,30,manual"}.items():
        if session.get(Configuration, key) is None:
            session.add(Configuration(key=key, value=value))
    session.commit()
