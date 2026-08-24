import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError

from backend.app.persistence.database import make_engine, migrate_database, session_factory
from backend.app.persistence.models import Patient, VitalObservation
from backend.app.seed.demo_data import seed_demo_data
from backend.app.seed.reset import reset_demo_data


def test_fresh_database_migrates_without_seed_rows(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'fresh.db'}"
    migrate_database(database_url)
    engine = make_engine(database_url)

    with session_factory(engine)() as session:
        assert session.scalar(select(Patient)) is None
        assert session.scalar(select(VitalObservation)) is None


def test_sqlite_foreign_keys_reject_orphan_observations(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'foreign-keys.db'}"
    migrate_database(database_url)
    engine = make_engine(database_url)

    with session_factory(engine)() as session:
        session.add(
            VitalObservation(
                patient_id="P-MISSING",
                bed_id="BED-MISSING",
                sequence=0,
                observed_at="2026-01-01T00:00:00+00:00",
                received_at="2026-01-01T00:00:00+00:00",
                spo2_percent=98,
                heart_rate_bpm=82,
                respiratory_rate_bpm=16,
                systolic_bp_mmhg=122,
                diastolic_bp_mmhg=78,
                temperature_c=36.8,
                source_kind="synthetic",
                source_name="acuitynet-simulator",
                scenario_id="p1042-deterioration-v1",
                scenario_version="1",
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()


def test_reset_requires_seeded_fixture_and_removes_observations_first(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'reset.db'}"
    migrate_database(database_url)
    engine = make_engine(database_url)
    sessions = session_factory(engine)

    with sessions.begin() as session:
        seed_demo_data(session)
        session.add(
            VitalObservation(
                patient_id="P-1042",
                bed_id="ICU-12",
                sequence=0,
                observed_at="2026-01-01T00:00:00+00:00",
                received_at="2026-01-01T00:00:00+00:00",
                spo2_percent=98,
                heart_rate_bpm=82,
                respiratory_rate_bpm=16,
                systolic_bp_mmhg=122,
                diastolic_bp_mmhg=78,
                temperature_c=36.8,
                source_kind="synthetic",
                source_name="acuitynet-simulator",
                scenario_id="p1042-deterioration-v1",
                scenario_version="1",
            )
        )
        session.flush()
        reset_demo_data(session)
        assert session.scalar(select(VitalObservation)) is None
        assert session.scalar(select(Patient)) is None