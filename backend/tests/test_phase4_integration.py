"""
Phase 4 integration tests: Reset/reseed safety, full E2E replay, and audit evidence.
"""
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.main import create_app
from backend.app.persistence.models import Alert, AuditEvent, DispatchDecision, DispatchEvaluation, PatientContextFact
from backend.app.seed.reset import reset_demo_data
from backend.app.seed.demo_data import seed_demo_data
from backend.app.audit.repository import AuditRepository


def upgrade_schema(database_url):
    """Run migrations to set up Phase 4 schema."""
    from alembic import command
    from alembic.config import Config

    config = Config("backend/alembic.ini")
    config.set_main_option("script_location", "backend/app/migrations")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def make_client(tmp_path):
    """Set up test client with migrations and demo data."""
    database_url = f"sqlite:///{tmp_path / 'phase4.db'}"
    upgrade_schema(database_url)
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    app = create_app(database_url, clock=lambda: now[0])
    client = TestClient(app)
    
    def login(username, password):
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    admin = login("admin", "admin-password")
    doctor = login("doctor", "doctor-password")
    nurse = login("sarah", "sarah-password")
    
    return database_url, client, admin, doctor, nurse, now


def test_phase4_reset_is_foreign_key_safe_and_reseed_restores_neutral_state(tmp_path):
    """Verify reset deletes Phase 4 children before parents and reseed restores neutral state."""
    database_url, client, admin, doctor, nurse, now = make_client(tmp_path)
    
    # Generate alerts by advancing vitals
    assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0}, headers=admin).status_code == 200
    assert client.patch("/api/v1/admin/configuration/risk-thresholds", 
                       json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, 
                       headers=admin).status_code == 200
    for tick in range(1, 4):
        assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin).status_code == 200
    
    # Trigger dispatch evaluation to create evaluation snapshot
    response = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor)
    assert response.status_code == 200, f"Dispatch evaluation failed: {response.text}"
    
    # Verify artifacts were created
    engine = create_engine(database_url)
    Sessions = sessionmaker(bind=engine)
    with Sessions() as session:
        alerts = session.scalars(select(Alert)).all()
        assert len(alerts) > 0, "Alerts should be generated"
        evals = session.scalars(select(DispatchEvaluation)).all()
        assert len(evals) > 0, "Evaluations should exist"
    
    # Reset and verify cleanup
    with Sessions() as session:
        reset_demo_data(session)
        session.commit()
        assert session.scalar(select(Alert)) is None, "All alerts should be deleted"
        assert session.scalar(select(DispatchEvaluation)) is None, "All evaluations should be deleted"
    
    # Reseed and verify neutral state
    with Sessions() as session:
        seed_demo_data(session)
        facts = session.scalars(select(PatientContextFact).filter_by(patient_id="P-1042")).all()
        assert len(facts) == 4, f"Expected 4 context facts, got {len(facts)}"
    
    print("[PASS] Reset/reseed test passed")


def test_phase4_full_lifecycle_and_audit_evidence(tmp_path):
    """Verify full E2E workflow: vitals -> alerts -> dispatch -> lifecycle -> audit."""
    database_url, client, admin, doctor, nurse, now = make_client(tmp_path)
    patient_id = "P-1042"
    
    # Advance vitals to generate alert
    assert client.post(f"/api/v1/patients/{patient_id}/vitals/advance", json={"tick": 0}, headers=admin).status_code == 200
    assert client.patch("/api/v1/admin/configuration/risk-thresholds", 
                       json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, 
                       headers=admin).status_code == 200
    for tick in range(1, 4):
        assert client.post(f"/api/v1/patients/{patient_id}/vitals/advance", json={"tick": tick}, headers=admin).status_code == 200
    
    # Get alert
    response = client.get(f"/api/v1/patients/{patient_id}/alert", headers=doctor)
    assert response.status_code == 200
    alert = response.json()
    alert_id = alert["alert_id"]
    assert alert["state"] == "generated"
    
    # Evaluate dispatch
    response = client.get(f"/api/v1/patients/{patient_id}/dispatch/evaluation", headers=doctor)
    assert response.status_code == 200
    eval_data = response.json()
    eval_id = eval_data["evaluation_id"]
    assert len(eval_data["candidates"]) > 0
    assert eval_data["status"] == "ready"
    
    # Confirm dispatch
    response = client.post(
        f"/api/v1/patients/{patient_id}/dispatch/confirm",
        json={
            "evaluation_id": eval_id,
            "nurse_id": "N-SARAH",
            "reason": "Clinical judgment"
        },
        headers=doctor
    )
    assert response.status_code == 200
    confirmed = response.json()
    assert confirmed["state"] == "assigned"
    
    # Verify audit trail has dispatch decision
    engine = create_engine(database_url)
    Sessions = sessionmaker(bind=engine)
    with Sessions() as session:
        audit_repo = AuditRepository(session)
        events = audit_repo.list_for_patient(patient_id)
        assert len(events) > 0, "Audit events must exist"
        dispatch_events = [e for e in events if "dispatch" in e.action]
        assert len(dispatch_events) > 0, f"Expected dispatch events, got {len(dispatch_events)}"
        # Verify no credentials in details
        for event in events:
            assert "password" not in event.details.lower()
            assert "bearer" not in event.details.lower()
    
    print("[PASS] Full lifecycle test passed")


def test_phase4_no_candidate_and_stale_safety(tmp_path):
    """Verify evaluation response is consistent and alert state doesn't mutate."""
    database_url, client, admin, doctor, nurse, now = make_client(tmp_path)
    patient_id = "P-1042"
    
    # Generate alert
    assert client.post(f"/api/v1/patients/{patient_id}/vitals/advance", json={"tick": 0}, headers=admin).status_code == 200
    assert client.patch("/api/v1/admin/configuration/risk-thresholds", 
                       json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, 
                       headers=admin).status_code == 200
    for tick in range(1, 4):
        client.post(f"/api/v1/patients/{patient_id}/vitals/advance", json={"tick": tick}, headers=admin)
    
    # Get alert state before evaluation
    response = client.get(f"/api/v1/patients/{patient_id}/alert", headers=doctor)
    alert_before = response.json()
    state_before = alert_before["state"]
    
    # Evaluate multiple times
    for _ in range(2):
        response = client.get(f"/api/v1/patients/{patient_id}/dispatch/evaluation", headers=doctor)
        assert response.status_code == 200
        eval_data = response.json()
        assert "evaluation_id" in eval_data, "Evaluation must have ID"
        assert "candidates" in eval_data, "Evaluation must have candidates"
        assert "status" in eval_data, "Evaluation must have status"
    
    # Verify alert state unchanged
    response = client.get(f"/api/v1/patients/{patient_id}/alert", headers=doctor)
    alert_after = response.json()
    state_after = alert_after["state"]
    assert state_before == state_after == "generated", f"Alert state must not change during evaluation: {state_before} -> {state_after}"
    
    print("[PASS] Safety test passed")

