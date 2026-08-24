from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from backend.app.main import create_app
from backend.app.persistence.models import Alert, PredictionEvidence


def app_client(tmp_path, now):
    app = create_app(f"sqlite:///{tmp_path / 'alerts.db'}", clock=lambda: now[0])
    client = TestClient(app)
    token = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-password"}).json()["access_token"]
    return client, {"Authorization": f"Bearer {token}"}


def test_threshold_crossing_persists_complete_evidence_and_current_alert(tmp_path):
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    client, headers = app_client(tmp_path, now)
    assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0}, headers=headers).status_code == 200
    assert client.patch("/api/v1/admin/configuration/risk-thresholds", json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, headers=headers).status_code == 200
    for tick in (1, 2, 3):
        assert client.post(f"/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=headers).status_code == 200
    alert = client.get("/api/v1/patients/P-1042/alert", headers=headers)
    assert alert.status_code == 200
    assert alert.json()["deduplication_status"] == "new_alert"
    assert alert.json()["prediction_source_kind"] == "deterministic_fallback"
    client.close()

    engine = create_engine(f"sqlite:///{tmp_path / 'alerts.db'}")
    sessions = sessionmaker(bind=engine)
    with sessions() as session:
        evidence = session.scalars(select(PredictionEvidence).order_by(PredictionEvidence.observation_sequence)).all()
        assert len(evidence) == 4
        assert all(item.prototype_label for item in evidence)
        assert all(item.synthetic_source_kind == "synthetic" for item in evidence)
        assert session.scalar(select(func.count(Alert.alert_id))) == 1


def test_repeated_tick_reuses_active_alert_and_invalid_configuration_is_rejected(tmp_path):
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    client, headers = app_client(tmp_path, now)
    client.patch("/api/v1/admin/configuration/risk-thresholds", json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, headers=headers)
    for tick in (0, 1, 2, 3):
        client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=headers)
    repeated = client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 3}, headers=headers)
    assert repeated.status_code == 200
    assert client.get("/api/v1/patients/P-1042/alert", headers=headers).json()["deduplication_status"] == "reused_active"
    invalid = client.patch("/api/v1/admin/configuration/risk-thresholds", json={"critical_risk_threshold": 0.1, "high_risk_threshold": 0.2}, headers=headers)
    assert invalid.status_code == 422
    client.close()


def test_alert_route_requires_authentication(tmp_path):
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    client, _ = app_client(tmp_path, now)
    assert client.get("/api/v1/patients/P-1042/alert").status_code == 401
    client.close()