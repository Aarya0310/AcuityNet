from datetime import datetime, timezone
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from backend.app.main import create_app
from backend.app.persistence.models import AuditEvent, DispatchDecision, DispatchEvaluation


def make_dispatch_client(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'dispatch.db'}"
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    app = create_app(database_url, clock=lambda: now[0])
    client = TestClient(app)

    def login(username, password):
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return database_url, client, now, login("admin", "admin-password"), login("doctor", "doctor-password"), login("sarah", "sarah-password")


def create_alert(client, admin):
    for tick in range(4):
        assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin).status_code == 200


def test_evaluation_is_ranked_and_confirm_delegates_to_lifecycle(tmp_path):
    database_url, client, _now, admin, doctor, _nurse = make_dispatch_client(tmp_path)
    create_alert(client, admin)

    evaluation = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor)
    assert evaluation.status_code == 200
    body = evaluation.json()
    assert body["status"] == "ready"
    assert body["recommendation_nurse_id"] == "N-SARAH"
    assert body["weights"] == {"acuity_compatibility": 0.1, "availability": 0.4, "proximity": 0.3, "workload": 0.2}
    candidate = body["candidates"][0]
    assert candidate["score"] == 0.93
    assert candidate["components"] == {"availability": 1.0, "proximity": 0.9, "workload": 0.75, "acuity_compatibility": 1.0}

    confirmed = client.post("/api/v1/patients/P-1042/dispatch/confirm", json={"evaluation_id": body["evaluation_id"], "nurse_id": "N-SARAH", "reason": "Doctor reviewed recommendation"}, headers=doctor)
    assert confirmed.status_code == 200
    assert confirmed.json()["state"] == "assigned"
    assert confirmed.json()["assignment_id"] == "N-SARAH"

    with sessionmaker(bind=create_engine(database_url))() as session:
        decision = session.scalar(select(DispatchDecision))
        assert decision is not None
        assert decision.decision_type == "confirmed"
        assignment = session.scalar(select(AuditEvent).where(AuditEvent.action == "lifecycle.assign"))
        assert assignment is not None
        assert len(assignment.details) <= 1000
        assert "password" not in assignment.details.lower()
        assert "evaluation_id" in assignment.details
    client.close()


def test_dispatch_tables_are_migrated_and_snapshots_are_immutable_rows(tmp_path):
    database_url, client, _now, admin, doctor, _nurse = make_dispatch_client(tmp_path)
    create_alert(client, admin)
    response = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor)
    assert response.status_code == 200
    engine = create_engine(database_url)
    assert {"dispatch_evaluations", "dispatch_decisions"}.issubset(inspect(engine).get_table_names())
    with sessionmaker(bind=engine)() as session:
        snapshot = session.scalar(select(DispatchEvaluation))
        assert snapshot is not None
        assert json.loads(snapshot.weights)["availability"] == 0.4
        assert snapshot.recommendation_nurse_id == "N-SARAH"
    client.close()
