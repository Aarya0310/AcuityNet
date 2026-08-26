from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from backend.app.persistence.models import HistorianRuleDefinition, PatientContextFact
from backend.app.seed.demo_data import seed_demo_data
from backend.app.seed.reset import reset_demo_data


def upgrade(database_url):
    config = Config("backend/alembic.ini")
    config.set_main_option("script_location", "backend/app/migrations")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def test_phase4_schema_and_seed_are_exact_and_indexed(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'phase4.db'}"
    upgrade(database_url)
    engine = create_engine(database_url)
    inspector = inspect(engine)
    expected = {"patient_context_facts", "historian_rule_definitions", "historian_rule_evaluations", "timeline_annotations"}
    assert expected.issubset(inspector.get_table_names())
    assert {index["name"] for index in inspector.get_indexes("patient_context_facts")} >= {"ix_patient_context_facts_patient_effective"}
    assert {index["name"] for index in inspector.get_indexes("historian_rule_evaluations")} >= {"ix_historian_rule_evaluations_patient_evaluated"}
    sessions = sessionmaker(bind=engine)
    with sessions() as session:
        seed_demo_data(session)
        assert {fact.fact_id for fact in session.scalars(select(PatientContextFact))} == {"D-P1042-01", "M-P1042-01", "L-P1042-01", "E-P1042-01"}
        assert {rule.rule_key for rule in session.scalars(select(HistorianRuleDefinition))} == {"diagnosis.respiratory_history", "medication.respiratory_support", "lab.oxygenation", "icu_event.recent_deterioration"}
        reset_demo_data(session)
        session.commit()
        seed_demo_data(session)
        assert session.scalar(select(PatientContextFact)) is not None