from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

from backend.app.main import create_app
from backend.app.persistence.models import AuditEvent, PatientContextFact


def make_historian_client(tmp_path):
    now = [datetime(2026, 1, 2, tzinfo=timezone.utc)]
    app = create_app(f"sqlite:///{tmp_path / 'historian.db'}", clock=lambda: now[0])
    client = TestClient(app)

    def login(username, password):
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return f"sqlite:///{tmp_path / 'historian.db'}", client, login("admin", "admin-password"), login("doctor", "doctor-password"), login("sarah", "sarah-password")


def test_seeded_historian_returns_complete_context_and_named_rules(tmp_path):
    _database_url, client, admin, doctor, _nurse = make_historian_client(tmp_path)
    for tick in range(4):
        assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin).status_code == 200

    response = client.get("/api/v1/patients/P-1042/historian", headers=doctor)

    assert response.status_code == 200
    body = response.json()
    assert body["patient_id"] == "P-1042"
    assert {fact["category"] for fact in body["facts"]} == {"diagnosis", "medication", "lab", "icu_event"}
    assert {rule["rule_key"] for rule in body["rule_evaluations"]} == {
        "diagnosis.respiratory_history",
        "medication.respiratory_support",
        "lab.oxygenation",
        "icu_event.recent_deterioration",
    }
    assert body["contextual_status"] == "complete"
    assert body["missing_evidence"] == []
    assert body["prototype_label"] == "Research prototype: simulated ICU data, not clinical advice."
    assert body["contextual_score"] == round(body["baseline_score"] + 0.05 + 0.03 + 0.07 + 0.05, 6)
    assert body["timeline"]
    assert client.get("/api/v1/patients/P-1042/historian", headers=admin).status_code == 200
    assert client.get("/api/v1/patients/P-1042/historian", headers=_nurse).status_code == 403
    client.close()


def test_incomplete_context_is_baseline_only_and_annotation_does_not_change_score(tmp_path):
    database_url, client, admin, doctor, nurse = make_historian_client(tmp_path)
    for tick in range(4):
        client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin)
    complete = client.get("/api/v1/patients/P-1042/historian", headers=doctor).json()
    session = sessionmaker(bind=create_engine(database_url))()
    session.execute(delete(PatientContextFact).where(PatientContextFact.category == "lab"))
    session.commit()
    session.close()

    incomplete_response = client.get("/api/v1/patients/P-1042/historian", headers=doctor)
    assert incomplete_response.status_code == 200
    incomplete = incomplete_response.json()
    assert incomplete["contextual_status"] == "incomplete"
    assert incomplete["contextual_score"] is None
    assert incomplete["baseline_score"] == complete["baseline_score"]
    assert incomplete["missing_evidence"] == ["lab"]
    assert {rule["category"] for rule in incomplete["rule_evaluations"]} == {"diagnosis", "medication", "icu_event"}

    annotation = client.post("/api/v1/patients/P-1042/annotations", json={"text": "Doctor review note"}, headers=doctor)
    assert annotation.status_code == 201
    after_annotation = client.get("/api/v1/patients/P-1042/historian", headers=doctor).json()
    assert after_annotation["baseline_score"] == incomplete["baseline_score"]
    assert after_annotation["contextual_score"] is None
    assert after_annotation["annotations"][0]["text"] == "Doctor review note"
    assert client.post("/api/v1/patients/P-1042/annotations", json={"text": "admin must not write"}, headers=admin).status_code == 403
    assert client.post("/api/v1/patients/P-1042/annotations", json={"text": "nurse must not write"}, headers=nurse).status_code == 403
    assert client.post("/api/v1/patients/P-1042/annotations", json={"text": "x", "extra": "forbidden"}, headers=doctor).status_code == 422
    session = sessionmaker(bind=create_engine(database_url))()
    assert session.scalar(select(AuditEvent).where(AuditEvent.action == "annotation.created")) is not None
    session.close()
    client.close()


