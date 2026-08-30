from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_current_vitals_exposes_patient_context_and_server_owned_provenance(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url, clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))

    with TestClient(app) as client:
        admin_token = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin-password"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0}, headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient"] == {
        "patient_id": "P-1042",
        "display_name": "Fictional Patient 1042",
        "bed_id": "ICU-12",
        "unit": "ICU",
    }
    assert payload["unit"] == "ICU"
    assert payload["provenance"]["source_kind"] == "synthetic"
    assert payload["provenance"]["is_live_bedside_feed"] is False


def test_current_vitals_resolves_freshness_and_unavailable_state(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    app = create_app(database_url, clock=lambda: now[0])

    with TestClient(app) as client:
        admin_token = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin-password"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        assert client.get("/api/v1/patients/P-1042/vitals/current", headers=headers).status_code == 404
        assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0}, headers=headers).status_code == 200
        assert client.get("/api/v1/patients/P-1042/vitals/current", headers=headers).json()["freshness"] == "fresh"
        now[0] = now[0].replace(second=16)
        assert client.get("/api/v1/patients/P-1042/vitals/current", headers=headers).json()["freshness"] == "stale"
        now[0] = now[0].replace(second=1, minute=1)
        assert client.get("/api/v1/patients/P-1042/vitals/current", headers=headers).json()["freshness"] == "disconnected"


def test_refresh_configuration_publishes_supported_intervals_and_default(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url)

    with TestClient(app) as client:
        response = client.get("/api/v1/configuration/refresh")

    assert response.status_code == 200
    assert response.json() == {
        "supported_intervals": [5, 10, 30, "manual"],
        "default_interval": 10,
    }


def test_automatic_advance_is_bounded_backend_owned_and_authoritative(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url)

    with TestClient(app) as client:
        admin_token = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin-password"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        first = client.post(
            "/api/v1/patients/P-1042/vitals/advance", json={"interval": 10}, headers=headers
        )
        current_after_first = client.get("/api/v1/patients/P-1042/vitals/current", headers=headers)
        second = client.post(
            "/api/v1/patients/P-1042/vitals/advance", json={"interval": 10}, headers=headers
        )
        current_after_second = client.get("/api/v1/patients/P-1042/vitals/current", headers=headers)

    assert first.status_code == 200
    assert first.json()["sequence"] == 0
    assert current_after_first.json() == first.json()
    assert second.status_code == 200
    assert second.json()["sequence"] == 1
    assert current_after_second.json() == second.json()


def test_advance_rejects_unsupported_intervals_and_unbounded_inputs(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url)

    with TestClient(app) as client:
        admin_token = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin-password"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        unsupported = client.post(
            "/api/v1/patients/P-1042/vitals/advance", json={"interval": 7}, headers=headers
        )
        unbounded = client.post(
            "/api/v1/patients/P-1042/vitals/advance", json={"interval": 10, "count": 1000}, headers=headers
        )

    assert unsupported.status_code == 422
    assert unbounded.status_code == 422