from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app.auth.security import create_access_token
from backend.app.main import create_app


SECRET = "test-only-secret"


def test_login_me_logout_has_password_free_session(tmp_path, monkeypatch):
    monkeypatch.setenv("ACUITYNET_JWT_SECRET", SECRET)
    app = create_app(f"sqlite:///{tmp_path / 'acuitynet.db'}")
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-password"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert "password" not in response.json()
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json() == {"user_id": "U-ADMIN", "username": "admin", "display_name": "AcuityNet Admin", "role": "admin"}
        assert client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}).status_code == 204


def test_invalid_expired_disabled_unknown_subject_and_role_are_generic_401(tmp_path, monkeypatch):
    monkeypatch.setenv("ACUITYNET_JWT_SECRET", SECRET)
    app = create_app(f"sqlite:///{tmp_path / 'acuitynet.db'}")
    with TestClient(app) as client:
        for credentials in ({"username": "admin", "password": "wrong"}, {"username": "missing", "password": "wrong"}):
            response = client.post("/api/v1/auth/login", json=credentials)
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"
        expired = create_access_token("U-ADMIN", expires_delta=timedelta(seconds=-1))
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication"
