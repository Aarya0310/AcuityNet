from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from backend.app.main import create_app
from backend.app.persistence.models import (
    Admission,
    Bed,
    Configuration,
    History,
    Nurse,
    Patient,
    VitalObservation,
)


def test_empty_database_migrates_and_writes_bounded_synthetic_observation(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/patients/P-1042/vitals/advance",
            json={"tick": 0},
        )
        assert response.status_code == 200

        observation = client.get("/api/v1/patients/P-1042/vitals/current")

    assert observation.status_code == 200
    payload = observation.json()
    assert payload["patient_id"] == "P-1042"
    assert payload["bed_id"] == "ICU-12"
    assert payload["sequence"] == 0
    assert payload["spo2_percent"] == 98
    assert payload["heart_rate_bpm"] == 82
    assert payload["respiratory_rate_bpm"] == 16
    assert payload["systolic_bp_mmhg"] == 122
    assert payload["diastolic_bp_mmhg"] == 78
    assert payload["temperature_c"] == 36.8
    assert payload["provenance"] == {
        "source_kind": "synthetic",
        "source_name": "acuitynet-simulator",
        "scenario_id": "p1042-deterioration-v1",
        "scenario_version": "1",
        "is_live_bedside_feed": False,
    }
    assert payload["freshness"] == "fresh"
    assert payload["prototype_label"] == (
        "Research prototype: simulated ICU data, not clinical advice."
    )
    datetime.fromisoformat(payload["observed_at"].replace("Z", "+00:00"))
    datetime.fromisoformat(payload["received_at"].replace("Z", "+00:00"))

    engine = create_engine(database_url)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Patient)) == 1
        assert session.scalar(select(func.count()).select_from(Admission)) == 1
        assert session.scalar(select(func.count()).select_from(Bed)) == 1
        assert session.scalar(select(func.count()).select_from(Nurse)) == 1
        assert session.scalar(select(func.count()).select_from(History)) == 1
        assert session.scalar(select(func.count()).select_from(Configuration)) == 1
        assert session.scalar(select(func.count()).select_from(VitalObservation)) == 1


def test_fixture_setup_is_idempotent(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url)

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/patients/P-1042/vitals/advance",
            json={"tick": 0},
        )
        second = client.post(
            "/api/v1/patients/P-1042/vitals/advance",
            json={"tick": 0},
        )

    assert first.status_code == 200
    assert second.status_code == 200
    engine = create_engine(database_url)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Patient)) == 1
        assert session.scalar(select(func.count()).select_from(VitalObservation)) == 1
