from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.persistence.database import make_engine, migrate_database, session_factory
from backend.app.persistence.models import (
    Admission,
    Bed,
    Configuration,
    History,
    Nurse,
    Patient,
    VitalObservation,
)
from backend.app.seed.demo_data import seed_demo_data
from backend.app.seed.reset import reset_demo_data


def aggregate_counts(session: Session) -> dict[str, int]:
    return {
        model.__tablename__: session.scalar(select(func.count()).select_from(model))
        for model in (Patient, Admission, Bed, Nurse, History, Configuration, VitalObservation)
    }


def test_full_seed_has_stable_p1042_aggregate(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    migrate_database(database_url)
    engine = make_engine(database_url)
    sessions = session_factory(engine)

    with sessions() as session:
        seed_demo_data(session)
        patient = session.get(Patient, "P-1042")
        assert patient.display_name == "Fictional Patient 1042"
        assert session.get(Bed, "ICU-12").patient_id == "P-1042"
        assert session.get(Admission, "A-P-1042").patient_id == "P-1042"
        assert session.get(Nurse, "N-SARAH").available is True
        assert session.get(History, "H-P-1042").patient_id == "P-1042"
        assert dict(session.execute(select(Configuration.key, Configuration.value)).all()) == {
            "freshness_fresh_seconds": "15",
            "freshness_stale_seconds": "60",
            "refresh_intervals": "5,10,30,manual",
        }
        assert aggregate_counts(session) == {
            "patients": 1,
            "admissions": 1,
            "beds": 1,
            "nurses": 1,
            "histories": 1,
            "configurations": 3,
            "vital_observations": 0,
        }


def test_reset_then_reseed_and_repeated_seed_preserve_graph(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    migrate_database(database_url)
    engine = make_engine(database_url)
    sessions = session_factory(engine)

    with sessions() as session:
        seed_demo_data(session)
        first_ids = {
            "patient": session.get(Patient, "P-1042").patient_id,
            "bed": session.get(Bed, "ICU-12").bed_id,
            "admission": session.get(Admission, "A-P-1042").admission_id,
            "nurse": session.get(Nurse, "N-SARAH").nurse_id,
            "history": session.get(History, "H-P-1042").history_id,
        }
        reset_demo_data(session)
        seed_demo_data(session)
        seed_demo_data(session)
        assert aggregate_counts(session) == {
            "patients": 1,
            "admissions": 1,
            "beds": 1,
            "nurses": 1,
            "histories": 1,
            "configurations": 3,
            "vital_observations": 0,
        }
        assert {
            "patient": session.get(Patient, "P-1042").patient_id,
            "bed": session.get(Bed, "ICU-12").bed_id,
            "admission": session.get(Admission, "A-P-1042").admission_id,
            "nurse": session.get(Nurse, "N-SARAH").nurse_id,
            "history": session.get(History, "H-P-1042").history_id,
        } == first_ids