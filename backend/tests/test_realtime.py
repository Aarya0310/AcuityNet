from fastapi.testclient import TestClient

from backend.app.auth.security import create_access_token
from backend.app.main import create_app


SECRET = "realtime-test-secret"


def make_app(tmp_path, monkeypatch):
    monkeypatch.setenv("ACUITYNET_JWT_SECRET", SECRET)
    return create_app(f"sqlite:///{tmp_path / 'acuitynet.db'}")


def test_authenticated_roles_receive_patient_scoped_post_commit_invalidation(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    for user_id in ("U-ADMIN", "U-DOCTOR", "U-SARAH"):
        token = create_access_token(user_id)
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/patients/P-1042/realtime?access_token={token}") as socket:
                publisher = app.state.realtime_publisher
                publisher.published.clear()
                publisher._subscribers["P-1042"]
                publisher.after_commit(type("Session", (), {"info": {"realtime_messages": [{"event": "alert.invalidated", "patient_id": "P-1042", "alert_id": 1, "audit_id": 2}]}})())
                assert socket.receive_json() == {"event": "alert.invalidated", "patient_id": "P-1042", "alert_id": 1, "audit_id": 2}


def test_realtime_rejects_missing_invalid_wrong_patient_and_unassigned_tokens(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    with TestClient(app) as client:
        for path in (
            "/api/v1/patients/P-1042/realtime",
            f"/api/v1/patients/P-9999/realtime?access_token={create_access_token('U-ADMIN')}",
            f"/api/v1/patients/P-1042/realtime?access_token=invalid",
        ):
            try:
                with client.websocket_connect(path):
                    assert False, "unauthorized websocket unexpectedly connected"
            except Exception:
                pass


def test_client_messages_are_not_a_mutation_api_and_disconnect_cleans_subscription(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    token = create_access_token("U-DOCTOR")
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/patients/P-1042/realtime?access_token={token}") as socket:
            socket.send_text('{"event":"alert.invalidated","patient_id":"P-1042"}')
            assert socket.receive() ["type"] == "websocket.close"
        assert not app.state.realtime_publisher._subscribers