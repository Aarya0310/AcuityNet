from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect


def test_phase3_schema_has_alert_tables_and_constraints(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'phase3.db'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("script_location", "backend/app/migrations")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    inspector = inspect(create_engine(database_url))
    assert {"prediction_evidence", "alerts", "alert_events", "audit_events"}.issubset(inspector.get_table_names())
    assert any(item["name"] == "uq_alert_patient_episode" for item in inspector.get_unique_constraints("alerts"))