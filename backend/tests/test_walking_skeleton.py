from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from backend.app.main import create_app
from backend.app.persistence.database import make_engine, session_factory
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


def test_empty_database_migrates_and_writes_bounded_synthetic_observation(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url)

    with TestClient(app) as client:
        admin_token = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin-password"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.post(
            "/api/v1/patients/P-1042/vitals/advance",
            json={"tick": 0},
            headers=headers,
        )
        assert response.status_code == 200

        observation = client.get("/api/v1/patients/P-1042/vitals/current", headers=headers)

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
        assert session.scalar(select(func.count()).select_from(Configuration)) == 8
        assert session.scalar(select(func.count()).select_from(VitalObservation)) == 1


def test_fixture_setup_is_idempotent(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url)

    with TestClient(app) as client:
        admin_token = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin-password"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        first = client.post(
            "/api/v1/patients/P-1042/vitals/advance",
            json={"tick": 0},
            headers=headers,
        )
        second = client.post(
            "/api/v1/patients/P-1042/vitals/advance",
            json={"tick": 0},
            headers=headers,
        )

    assert first.status_code == 200
    assert second.status_code == 200
    engine = create_engine(database_url)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Patient)) == 1
        assert session.scalar(select(func.count()).select_from(VitalObservation)) == 1


def test_direct_seed_setup_is_idempotent_and_has_resolved_configuration(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url)
    del app
    engine = make_engine(database_url)
    sessions = session_factory(engine)

    with sessions() as session:
        seed_demo_data(session)
        seed_demo_data(session)

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Patient)) == 1
        assert session.scalar(select(func.count()).select_from(Admission)) == 1
        assert session.scalar(select(func.count()).select_from(Bed)) == 1
        assert session.scalar(select(func.count()).select_from(Nurse)) == 1
        assert session.scalar(select(func.count()).select_from(History)) == 1
        configurations = dict(session.execute(select(Configuration.key, Configuration.value)).all())
        assert configurations == {
            "freshness_fresh_seconds": "15",
            "freshness_stale_seconds": "60",
            "refresh_intervals": "5,10,30,manual",
            "historian_context_fresh_seconds": "86400",
            "dispatch_status_fresh_seconds": "60",
            "dispatch_workload_fresh_seconds": "60",
            "dispatch_proximity_fresh_seconds": "300",
            "dispatch_alert_fresh_seconds": "300",
        }
