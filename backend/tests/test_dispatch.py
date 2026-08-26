from datetime import datetime, timedelta, timezone
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from backend.app.main import create_app
from backend.app.persistence.models import AuditEvent, DispatchDecision, DispatchEvaluation, Nurse
from backend.app.seed.reset import reset_demo_data


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


def test_nurse_is_denied_dispatch_evaluation_and_decision(tmp_path):
    _database_url, client, _now, _admin, _doctor, nurse = make_dispatch_client(tmp_path)
    create_alert(client, nurse)

    evaluation = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=nurse)
    assert evaluation.status_code == 403
    decision = client.post(
        "/api/v1/patients/P-1042/dispatch/confirm",
        json={"evaluation_id": "DPE-missing", "nurse_id": "N-SARAH", "reason": "Attempt"},
        headers=nurse,
    )
    assert decision.status_code == 403
    assert client.get("/api/v1/patients/P-1042/alert", headers=nurse).json()["state"] == "generated"
    client.close()


def test_ineligible_candidates_are_excluded_without_fabricated_scores(tmp_path):
    database_url, client, _now, admin, doctor, _nurse = make_dispatch_client(tmp_path)
    create_alert(client, admin)
    engine = create_engine(database_url)
    with sessionmaker(bind=engine).begin() as session:
        session.add(Nurse(nurse_id="N-EMPTY", display_name="Incomplete Nurse", available=True, user_id=None))

    body = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor).json()
    excluded = next(item for item in body["exclusions"] if item["nurse_id"] == "N-EMPTY")
    assert excluded["eligible"] is False
    assert excluded["score"] is None
    assert excluded["components"] == {}
    assert "missing active nurse identity" in excluded["exclusion_reasons"]
    assert body["recommendation_nurse_id"] == "N-SARAH"
    client.close()


def test_no_candidate_evaluation_and_retry_preserve_generated_alert(tmp_path):
    database_url, client, _now, admin, doctor, _nurse = make_dispatch_client(tmp_path)
    create_alert(client, admin)
    with sessionmaker(bind=create_engine(database_url)).begin() as session:
        session.scalar(select(Nurse).where(Nurse.nurse_id == "N-SARAH")).available = False

    body = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor).json()
    assert body["status"] == "no_eligible_candidate"
    assert body["recommendation_nurse_id"] is None
    assert body["candidates"] == []
    assert body["exclusions"][0]["score"] is None

    retry = client.post("/api/v1/patients/P-1042/dispatch/retry", headers=doctor)
    assert retry.status_code == 200
    assert retry.json()["status"] == "no_eligible_candidate"
    assert client.get("/api/v1/patients/P-1042/alert", headers=doctor).json()["state"] == "generated"
    with sessionmaker(bind=create_engine(database_url))() as session:
        retry_audit = session.scalar(select(AuditEvent).where(AuditEvent.action == "dispatch.retry"))
        assert retry_audit is not None
        assert retry_audit.actor_id == "U-DOCTOR"
        assert json.loads(retry_audit.details)["retry"] is True
    client.close()


def test_decision_rejects_stale_candidate_and_short_reason(tmp_path):
    database_url, client, now, admin, doctor, _nurse = make_dispatch_client(tmp_path)
    create_alert(client, admin)
    evaluation = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor).json()

    with sessionmaker(bind=create_engine(database_url)).begin() as session:
        session.scalar(select(Nurse).where(Nurse.nurse_id == "N-SARAH")).workload_active = 2
    stale = client.post(
        "/api/v1/patients/P-1042/dispatch/override",
        json={"evaluation_id": evaluation["evaluation_id"], "nurse_id": "N-SARAH", "reason": "Use alternate review"},
        headers=doctor,
    )
    assert stale.status_code == 409
    assert client.get("/api/v1/patients/P-1042/alert", headers=doctor).json()["state"] == "generated"

    fresh = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor).json()
    short_reason = client.post(
        "/api/v1/patients/P-1042/dispatch/confirm",
        json={"evaluation_id": fresh["evaluation_id"], "nurse_id": "N-SARAH", "reason": " x "},
        headers=doctor,
    )
    assert short_reason.status_code == 422
    now[0] += timedelta(seconds=301)
    expired = client.post(
        "/api/v1/patients/P-1042/dispatch/confirm",
        json={"evaluation_id": fresh["evaluation_id"], "nurse_id": "N-SARAH", "reason": "Doctor reviewed recommendation"},
        headers=doctor,
    )
    assert expired.status_code == 409
    client.close()


def test_reset_removes_dispatch_snapshots_and_decisions(tmp_path):
    database_url, client, _now, admin, doctor, _nurse = make_dispatch_client(tmp_path)
    create_alert(client, admin)
    evaluation = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor).json()
    confirmed = client.post(
        "/api/v1/patients/P-1042/dispatch/confirm",
        json={"evaluation_id": evaluation["evaluation_id"], "nurse_id": "N-SARAH", "reason": "Doctor reviewed recommendation"},
        headers=doctor,
    )
    assert confirmed.status_code == 200
    with sessionmaker(bind=create_engine(database_url)).begin() as session:
        reset_demo_data(session)
    with sessionmaker(bind=create_engine(database_url))() as session:
        assert session.scalars(select(DispatchEvaluation)).all() == []
        assert session.scalars(select(DispatchDecision)).all() == []
        assert session.scalars(select(AuditEvent)).all() == []
    client.close()
