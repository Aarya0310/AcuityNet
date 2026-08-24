from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from backend.app.persistence.database import make_engine, migrate_database, session_factory
from backend.app.persistence.models import VitalObservation
from backend.app.seed.demo_data import seed_demo_data
from backend.app.vitals.scenario import P1042Scenario
from backend.app.vitals.service import ObservationService


EXPECTED_VALUES = (
    (98, 82, 16, 122, 78, 36.8),
    (97, 88, 18, 118, 76, 36.9),
    (95, 96, 22, 112, 72, 37.1),
    (92, 108, 27, 104, 68, 37.4),
    (88, 122, 32, 96, 62, 37.8),
)


def test_p1042_scenario_is_exact_and_bounded():
    scenario = P1042Scenario(seed="p1042-demo")

    assert tuple(scenario.values_for(tick) for tick in range(5)) == EXPECTED_VALUES
    assert scenario.reset() == 0
    with pytest.raises(ValueError):
        scenario.values_for(5)
    with pytest.raises(ValueError):
        scenario.values_for(-1)


def test_service_persists_injected_time_and_immutable_ticks(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    migrate_database(database_url)
    engine = make_engine(database_url)
    sessions = session_factory(engine)
    service = ObservationService(P1042Scenario(seed="p1042-demo"))
    timestamp = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    with sessions() as session:
        seed_demo_data(session)
    with sessions.begin() as session:
        first = service.advance(session, "P-1042", 0, timestamp)
        repeated = service.advance(session, "P-1042", 0, timestamp)
        second = service.advance(session, "P-1042", 1, timestamp)

    assert first is repeated
    assert first.sequence == 0
    assert second.sequence == 1
    assert second.observed_at == timestamp
    assert second.received_at == timestamp
    assert (second.spo2_percent, second.heart_rate_bpm) == (97, 88)

    with sessions() as session:
        observations = session.scalars(
            select(VitalObservation).order_by(VitalObservation.sequence)
        ).all()
        assert len(observations) == 2
        assert [observation.sequence for observation in observations] == [0, 1]
        assert observations[0].scenario_id == "p1042-deterioration-v1"
        assert observations[0].source_kind == "synthetic"