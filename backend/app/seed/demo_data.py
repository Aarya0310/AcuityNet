from datetime import datetime, timezone
import hashlib
import secrets

from sqlalchemy.orm import Session

from backend.app.persistence.models import Admission, Bed, Configuration, History, HistorianRuleDefinition, Nurse, Patient, PatientContextFact, User
from backend.app.safety.labels import PROTOTYPE_LABEL, SYNTHETIC_SOURCE_NAME


def password_digest(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"pbkdf2_sha256$120000${salt.hex()}${digest.hex()}"


def seed_demo_data(session: Session) -> None:
    demo_users = [
        ("U-ADMIN", "admin", "AcuityNet Admin", "admin", "admin-password"),
        ("U-DOCTOR", "doctor", "Dr. Maya Chen", "doctor", "doctor-password"),
        ("U-SARAH", "sarah", "Sarah Morgan", "nurse", "sarah-password"),
    ]
    for user_id, username, display_name, role, password in demo_users:
        user = session.get(User, user_id)
        if user is None:
            user = User(user_id=user_id, username=username, display_name=display_name, role=role, password_digest=password_digest(password), active=True)
            session.add(user)
        else:
            user.username, user.display_name, user.role, user.active = username, display_name, role, True
    session.flush()
    patient = session.get(Patient, "P-1042")
    if patient is None:
        patient = Patient(patient_id="P-1042", display_name="Fictional Patient 1042")
        session.add(patient)
    else:
        patient.display_name = "Fictional Patient 1042"
    session.flush()
    values = [
        (Bed, "ICU-12", {"unit": "ICU", "patient_id": "P-1042"}),
        (Nurse, "N-SARAH", {"display_name": "Sarah Morgan", "available": True, "user_id": "U-SARAH"}),
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
    for key, value in {"freshness_fresh_seconds": "15", "freshness_stale_seconds": "60", "refresh_intervals": "5,10,30,manual", "historian_context_fresh_seconds": "86400"}.items():
        configuration = session.get(Configuration, key)
        if configuration is None:
            session.add(Configuration(key=key, value=value))
        else:
            configuration.value = value
    context_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    facts = [
        ("D-P1042-01", "diagnosis", "fictional chronic respiratory condition", None, None),
        ("M-P1042-01", "medication", "fictional inhaled support", None, None),
        ("L-P1042-01", "lab", "oxygenation marker", "92", "%"),
        ("E-P1042-01", "icu_event", "fictional prior respiratory observation", None, None),
    ]
    for fact_id, category, label, value, unit in facts:
        fact = session.get(PatientContextFact, fact_id)
        fields = {"patient_id": "P-1042", "category": category, "label": label, "value": value, "unit": unit, "source_kind": "synthetic", "source_name": SYNTHETIC_SOURCE_NAME, "effective_at": context_at, "is_complete": True}
        if fact is None:
            session.add(PatientContextFact(fact_id=fact_id, **fields))
        else:
            for field, value in fields.items():
                setattr(fact, field, value)
    rules = [
        ("R-DIAG-RESP", "diagnosis.respiratory_history", "Respiratory history", "diagnosis", 0.05, "Research adjustment from the seeded diagnosis context."),
        ("R-MED-RESP", "medication.respiratory_support", "Respiratory support", "medication", 0.03, "Research adjustment from the seeded medication context."),
        ("R-LAB-OXY", "lab.oxygenation", "Oxygenation", "lab", 0.07, "Research adjustment from the seeded oxygenation context."),
        ("R-ICU-RECENT", "icu_event.recent_deterioration", "Recent deterioration", "icu_event", 0.05, "Research adjustment from the seeded prior ICU event context."),
    ]
    for rule_id, rule_key, name, category, delta, explanation in rules:
        rule = session.get(HistorianRuleDefinition, rule_id)
        fields = {"rule_key": rule_key, "category": category, "name": name, "version": "rules.v1", "delta": delta, "explanation": explanation, "required": True}
        if rule is None:
            session.add(HistorianRuleDefinition(rule_id=rule_id, **fields))
        else:
            for field, value in fields.items():
                setattr(rule, field, value)
    session.commit()
