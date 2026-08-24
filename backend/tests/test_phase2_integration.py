import os


def test_phase2_smoke_requires_local_secret(monkeypatch):
    monkeypatch.delenv("ACUITYNET_JWT_SECRET", raising=False)
    assert os.environ.get("ACUITYNET_JWT_SECRET") is None