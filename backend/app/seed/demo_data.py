from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.persistence.models import Admission, Bed, Configuration, History, Nurse, Patient


def seed_demo_data(session: Session) -> None:
    patient = session.get(Patient, "P-1042")
    if patient is None:
        patient = Patient(patient_id="P-1042", display_name="Fictional Patient 1042")
        session.add(patient)
    else:
        patient.display_name = "Fictional Patient 1042"
    session.flush()
    values = [
        (Bed, "ICU-12", {"unit": "ICU", "patient_id": "P-1042"}),
        (Nurse, "N-SARAH", {"display_name": "Sarah Morgan", "available": True}),
        (History, "H-P-1042", {"patient_id": "P-1042", "summary": "Fictional demonstration history."}),
    ]
    for model, identifier, fields in values:
        key = "bed_id" if model is Bed else "nurse_id" if model is Nurse else "history_id"
        row = session.get(model, identifier)
        if row is None:
            session.add(model(**{key: identifier}, **fields))
        else:
            for field, value in fields.items():
                setattr(row, field, value)
    session.flush()
    admission = session.get(Admission, "A-P-1042")
    if admission is None:
        session.add(Admission(admission_id="A-P-1042", patient_id="P-1042", admitted_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
    else:
        admission.patient_id = "P-1042"
        admission.admitted_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for key, value in {"freshness_fresh_seconds": "15", "freshness_stale_seconds": "60", "refresh_intervals": "5,10,30,manual"}.items():
        configuration = session.get(Configuration, key)
        if configuration is None:
            session.add(Configuration(key=key, value=value))
        else:
            configuration.value = value
    session.commit()
