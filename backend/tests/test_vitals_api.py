from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_current_vitals_exposes_patient_context_and_server_owned_provenance(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url, clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))

    with TestClient(app) as client:
        response = client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0})

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
        assert client.get("/api/v1/patients/P-1042/vitals/current").status_code == 404
        assert client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0}).status_code == 200
        assert client.get("/api/v1/patients/P-1042/vitals/current").json()["freshness"] == "fresh"
        now[0] = now[0].replace(second=16)
        assert client.get("/api/v1/patients/P-1042/vitals/current").json()["freshness"] == "stale"
        now[0] = now[0].replace(second=1, minute=1)
        assert client.get("/api/v1/patients/P-1042/vitals/current").json()["freshness"] == "disconnected"