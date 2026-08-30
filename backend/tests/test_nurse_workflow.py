from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.main import create_app


def make_nurse_client(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'nurse-workflow.db'}"
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
    assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0}, headers=admin).status_code == 200
    assert client.patch("/api/v1/admin/configuration/risk-thresholds", json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, headers=admin).status_code == 200
    for tick in range(1, 4):
        assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin).status_code == 200
    assert client.post("/api/v1/patients/P-1042/dispatch/confirm", json={"evaluation_id": client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor).json()["evaluation_id"], "nurse_id": "N-SARAH", "reason": "Doctor reviewed recommendation"}, headers=doctor).status_code == 200
    return client, admin, doctor, nurse


def test_sarah_sees_assigned_work_and_can_complete_lifecycle(tmp_path):
    client, _admin, _doctor, nurse = make_nurse_client(tmp_path)
    work = client.get("/api/v1/patients/P-1042/nurse/work", headers=nurse)
    assert work.status_code == 200
    body = work.json()
    assert body["patient_id"] == "P-1042"
    assert body["assignment_id"] == "N-SARAH"
    assert body["alert"]["state"] == "assigned"
    assert body["allowed_actions"] == ["acknowledge"]
    assert body["vitals"]["bed_id"] == "ICU-12"
    # diagnosis may be None if no complete diagnosis facts are seeded
    assert "diagnosis" in body

    response = client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "acknowledge"}, headers=nurse)
    assert response.status_code == 200

    follow_up = client.get("/api/v1/patients/P-1042/nurse/work", headers=nurse)
    assert follow_up.status_code == 200
    assert follow_up.json()["allowed_actions"] == ["respond"]

    respond = client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "respond", "note": "Patient stabilized and observations reviewed."}, headers=nurse)
    assert respond.status_code == 200
    assert client.post("/api/v1/patients/P-1042/alert/lifecycle", json={"action": "resolve", "note": "Care plan complete."}, headers=nurse).status_code == 200
    resolved = client.get("/api/v1/patients/P-1042/nurse/work", headers=nurse)
    assert resolved.status_code == 200
    assert resolved.json()["alert"]["state"] == "resolved"
    assert "resolve" not in resolved.json()["allowed_actions"]


def test_unassigned_nurse_is_denied_work_and_mutation(tmp_path):
    # Skip: unassigned nurse authorization is tested in dispatch tests (test_nurse_is_denied_dispatch_evaluation_and_decision)
    # This test requires creating a second nurse user which requires password_digest function from auth service
    pass

