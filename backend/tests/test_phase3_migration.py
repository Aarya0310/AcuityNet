from datetime import datetime, timezone

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import sessionmaker

from backend.app.persistence.models import Alert, AlertEvent, AuditEvent, PredictionEvidence, User, VitalObservation
from backend.app.seed.demo_data import seed_demo_data
from backend.app.seed.reset import reset_demo_data


def test_phase3_schema_has_alert_tables_and_constraints(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'phase3.db'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("script_location", "backend/app/migrations")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    inspector = inspect(create_engine(database_url))
    assert {"prediction_evidence", "alerts", "alert_events", "audit_events"}.issubset(inspector.get_table_names())
    assert any(item["name"] == "uq_alert_patient_episode" for item in inspector.get_unique_constraints("alerts"))


def test_reset_deletes_phase3_children_before_reseed(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'phase3-reset.db'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("script_location", "backend/app/migrations")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    sessions = sessionmaker(bind=create_engine(database_url))
    observed_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with sessions() as session:
        seed_demo_data(session)
        session.add(VitalObservation(
            patient_id="P-1042", bed_id="ICU-12", sequence=0,
            observed_at=observed_at, received_at=observed_at,
            spo2_percent=98, heart_rate_bpm=82, respiratory_rate_bpm=16,
            systolic_bp_mmhg=122, diastolic_bp_mmhg=78, temperature_c=36.8,
            source_kind="synthetic", source_name="scenario",
            scenario_id="p1042-deterioration-v1", scenario_version="1",
        ))
        session.commit()
        session.add(PredictionEvidence(
            patient_id="P-1042", observation_id=1, observation_sequence=0,
            score=0.1, event="test", level="low", probability=0.1,
            horizon_minutes=30, source_kind="deterministic_fallback", source_version="rules.v1",
            fallback_reason="test", fallback_metadata="{}", prediction_contract_version="prediction.v1",
            synthetic_source_kind="synthetic", synthetic_source_name="scenario",
            synthetic_scenario_id="p1042-deterioration-v1", synthetic_scenario_version="1",
            prototype_label="test", effective_threshold=0.7, rule_version="rules.v1",
            server_timestamp=observed_at,
        ))
        session.flush()
        session.add(Alert(
            patient_id="P-1042", bed_id="ICU-12", episode_key="P-1042:0", state="generated",
            priority="high", evidence_id=1, deduplication_status="new_alert",
            created_at=observed_at,
        ))
        session.flush()
        session.add(AlertEvent(alert_id=1, state="generated", outcome="new_alert", occurred_at=observed_at))
        session.add(AuditEvent(actor_id=None, action="alert.generated", resource_type="patient", resource_id="P-1042", outcome="success", occurred_at=observed_at, details="{}"))
        session.flush()
        reset_demo_data(session)
        session.commit()
        seed_demo_data(session)
        assert session.scalar(select(Alert)) is None
        assert session.scalar(select(AlertEvent)) is None
        assert session.scalar(select(AuditEvent)) is None
        assert session.scalar(select(PredictionEvidence)) is None
        assert session.scalar(select(func.count()).select_from(VitalObservation)) == 0
        assert session.scalar(select(func.count()).select_from(User)) == 3