from datetime import datetime, timezone
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from backend.app.main import create_app
from backend.app.persistence.models import Alert, AlertEvent, AuditEvent, PredictionEvidence, User
from backend.app.seed.demo_data import password_digest


def make_journey(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'phase3.db'}"
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    app = create_app(database_url, clock=lambda: now[0])
    sessions = sessionmaker(bind=create_engine(database_url))
    with sessions.begin() as session:
        session.add(User(user_id="U-ALEX", username="alex", display_name="Alex Reed", role="nurse", password_digest=password_digest("alex-password"), active=True))
    client = TestClient(app)

    def login(username, password):
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    roles = {
        "admin": login("admin", "admin-password"),
        "doctor": login("doctor", "doctor-password"),
        "sarah": login("sarah", "sarah-password"),
        "alex": login("alex", "alex-password"),
    }
    return client, database_url, now, roles


def test_complete_phase3_journey_is_reconstructable_and_role_scoped(tmp_path):
    client, database_url, now, roles = make_journey(tmp_path)
    admin, doctor, sarah, alex = (roles[name] for name in ("admin", "doctor", "sarah", "alex"))

    configuration = client.patch("/api/v1/admin/configuration/risk-thresholds", json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, headers=admin)
    assert configuration.status_code == 200
    for tick in (0, 1, 2, 3):
        assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin).status_code == 200

    prediction = client.get("/api/v1/patients/P-1042/prediction", headers=doctor)
    assert prediction.status_code == 200
    assert prediction.json()["source_kind"] == "deterministic_fallback"
    alert = client.get("/api/v1/patients/P-1042/alert", headers=doctor)
    assert alert.status_code == 200
    assert alert.json()["deduplication_status"] == "new_alert"
    assert alert.json()["fallback_reason"] == "ML provider unavailable"
    assert alert.json()["provenance"]["source_kind"] == "synthetic"
    assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 3}, headers=admin).status_code == 200
    assert client.get("/api/v1/patients/P-1042/alert", headers=doctor).json()["deduplication_status"] == "reused_active"

    assert client.get("/api/v1/patients/P-1042/alert", headers=sarah).status_code == 403
    assert client.get("/api/v1/patients/P-1042/alert", headers=alex).status_code == 403
    assert client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "assign", "assignment_id": "N-SARAH", "assignment_evidence": "mentor review"}, headers=doctor).status_code == 200
    assert client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "acknowledge"}, headers=sarah).status_code == 200
    assert client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "respond", "note": "response recorded"}, headers=sarah).status_code == 200
    assert client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "resolve", "note": "resolved"}, headers=sarah).status_code == 200

    events = client.get("/api/v1/patients/P-1042/alert/events", headers=doctor)
    assert [item["state"] for item in events.json()] == ["generated", "assigned", "acknowledged", "responded", "resolved"]
    audit = client.get("/api/v1/patients/P-1042/audit", headers=doctor)
    assert audit.status_code == 200
    audit_events = audit.json()["events"]
    assert [item["sequence"] for item in audit_events] == list(range(1, len(audit_events) + 1))
    assert {item["category"] for item in audit_events} >= {"configuration", "alert", "assignment", "lifecycle", "access"}
    assert any(item["outcome"] == "denied" and item["actor_id"] == "U-SARAH" for item in audit_events)
    assert any(item["outcome"] == "denied" and item["actor_id"] == "U-ALEX" for item in audit_events)
    assert all("password" not in json.dumps(item).lower() and "bearer" not in json.dumps(item).lower() for item in audit_events)

    kpis = client.get("/api/v1/admin/kpis", headers=admin)
    assert kpis.status_code == 200
    assert kpis.json()["alerts"]["status"] == "known"
    assert kpis.json()["alerts"]["value"] == 1
    assert kpis.json()["response_time"]["status"] == "not_yet_available"
    assert kpis.json()["acknowledgement_rate"]["status"] == "not_yet_available"

    token = client.post("/api/v1/auth/login", json={"username": "doctor", "password": "doctor-password"}).json()["access_token"]
    with client.websocket_connect(f"/api/v1/patients/P-1042/realtime?access_token={token}") as socket:
        socket.send_text("not-json")
        assert socket.receive()["type"] == "websocket.close"
    assert client.get("/api/v1/patients/P-1042/alert", headers=doctor).status_code == 200
    client.close()

    with sessionmaker(bind=create_engine(database_url))() as session:
        assert session.scalar(select(func.count()).select_from(PredictionEvidence)) == 4
        assert session.scalar(select(func.count()).select_from(Alert)) == 1
        assert session.scalar(select(func.count()).select_from(AlertEvent)) == 5
        assert session.scalar(select(func.count()).select_from(AuditEvent)) >= 8
        assert all("password" not in event.details.lower() and "authorization" not in event.details.lower() for event in session.scalars(select(AuditEvent)))


def test_equal_clock_order_and_invalid_transition_are_stable(tmp_path):
    client, database_url, _now, roles = make_journey(tmp_path)
    admin, doctor, sarah = roles["admin"], roles["doctor"], roles["sarah"]
    client.patch("/api/v1/admin/configuration/risk-thresholds", json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, headers=admin)
    for tick in range(4):
        client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin)
    invalid = client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "respond", "note": "skip"}, headers=doctor)
    assert invalid.status_code == 422
    assert client.get("/api/v1/patients/P-1042/alert", headers=doctor).json()["state"] == "generated"
    client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "assign", "assignment_id": "N-SARAH", "assignment_evidence": "evidence"}, headers=doctor)
    client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "acknowledge"}, headers=sarah)
    audit = client.get("/api/v1/patients/P-1042/audit", headers=doctor).json()["events"]
    assert [item["audit_id"] for item in audit] == sorted(item["audit_id"] for item in audit)
    client.close()