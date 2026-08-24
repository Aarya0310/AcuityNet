from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.main import create_app
from backend.app.persistence.models import Alert, AlertEvent, AuditEvent


def setup_client(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'lifecycle.db'}"
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    app = create_app(database_url, clock=lambda: now[0])
    client = TestClient(app)
    token = lambda username, password: client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()["access_token"]
    admin = {"Authorization": f"Bearer {token('admin', 'admin-password')}"}
    doctor = {"Authorization": f"Bearer {token('doctor', 'doctor-password')}"}
    nurse = {"Authorization": f"Bearer {token('sarah', 'sarah-password')}"}
    client.patch("/api/v1/admin/configuration/risk-thresholds", json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, headers=admin)
    for tick in range(4):
        assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin).status_code == 200
    return client, database_url, admin, doctor, nurse


def test_full_lifecycle_is_ordered_and_role_scoped(tmp_path):
    client, database_url, admin, doctor, nurse = setup_client(tmp_path)
    assert client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "assign", "assignment_id": "N-SARAH", "assignment_evidence": "manual assignment"}, headers=doctor).status_code == 200
    assert client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "acknowledge"}, headers=nurse).status_code == 200
    assert client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "respond", "note": "response recorded"}, headers=nurse).status_code == 200
    result = client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "resolve", "note": "resolved"}, headers=nurse)
    assert result.status_code == 200
    assert [item["state"] for item in client.get("/api/v1/patients/P-1042/alert/events", headers=doctor).json()] == ["generated", "assigned", "acknowledged", "responded", "resolved"]
    audit = client.get("/api/v1/patients/P-1042/audit", headers=doctor)
    assert audit.status_code == 200
    assert [item["sequence"] for item in audit.json()["events"]] == list(range(1, len(audit.json()["events"]) + 1))
    assert any(item["actor_id"] == "U-SARAH" and item["resulting_state"] == "resolved" for item in audit.json()["events"])
    client.close()


def test_invalid_transition_and_anonymous_denial_do_not_mutate_or_leak(tmp_path):
    client, database_url, admin, doctor, nurse = setup_client(tmp_path)
    invalid = client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "respond", "note": "skip"}, headers=doctor)
    assert invalid.status_code == 422
    assert client.get("/api/v1/patients/P-1042/alert", headers=doctor).json()["state"] == "generated"
    denied = client.get("/api/v1/patients/P-1042/alert", headers={"Authorization": "Bearer secret-token"})
    assert denied.status_code == 401
    client.close()
    with sessionmaker(bind=create_engine(database_url))() as session:
        events = session.scalars(select(AuditEvent)).all()
        assert any(item.outcome == "denied" and item.actor_id is None for item in events)
        assert all("secret-token" not in item.details and "Authorization" not in item.details for item in events)
        assert session.scalar(select(Alert).where(Alert.patient_id == "P-1042")).state == "generated"


def test_audit_and_lifecycle_rows_are_atomic(tmp_path):
    client, database_url, admin, doctor, nurse = setup_client(tmp_path)
    assert client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "assign", "assignment_id": "N-SARAH", "assignment_evidence": "manual assignment"}, headers=doctor).status_code == 200
    client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "acknowledge"}, headers=nurse)
    client.close()
    with sessionmaker(bind=create_engine(database_url))() as session:
        alert = session.scalar(select(Alert).where(Alert.patient_id == "P-1042"))
        assert alert.state == "acknowledged"
        assert len(session.scalars(select(AlertEvent).where(AlertEvent.alert_id == alert.alert_id)).all()) == 3