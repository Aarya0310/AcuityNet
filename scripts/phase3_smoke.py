from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8766"
SECRET = os.environ.get("ACUITYNET_JWT_SECRET")


def request_json(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None) -> dict:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(f"{BASE_URL}{path}", headers=headers, data=data, method=method)
    with urlopen(request, timeout=3) as response:
        if response.status != 200:
            raise AssertionError(f"{method} {path} returned HTTP {response.status}")
        return json.load(response)


def wait_for_health() -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            request_json("/health")
            return
        except (HTTPError, URLError, TimeoutError, OSError):
            time.sleep(0.25)
    raise RuntimeError("Uvicorn did not become ready")


def main() -> int:
    if not SECRET:
        print("ACUITYNET_JWT_SECRET is required for Phase 3 smoke verification", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="acuitynet-phase3-") as directory:
        database_url = f"sqlite:///{Path(directory, 'phase3.db').as_posix()}"
        environment = os.environ.copy()
        environment["ACUITYNET_JWT_SECRET"] = SECRET
        environment["ACUITYNET_DATABASE_URL"] = database_url
        environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
        process = subprocess.Popen(
            [sys.executable, "-c", "import uvicorn; from backend.app.main import app; uvicorn.run(app, host='127.0.0.1', port=8766)"],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_for_health()
            login = lambda username, password: request_json("/api/v1/auth/login", "POST", {"username": username, "password": password})["access_token"]
            admin = login("admin", "admin-password")
            doctor = login("doctor", "doctor-password")
            nurse = login("sarah", "sarah-password")
            request_json("/api/v1/admin/configuration/risk-thresholds", "PATCH", {"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, admin)
            for tick in (0, 1, 2, 3):
                request_json("/api/v1/patients/P-1042/vitals/advance", "POST", {"tick": tick}, admin)
            alert = request_json("/api/v1/patients/P-1042/alert", token=doctor)
            assert alert["deduplication_status"] == "new_alert"
            assert alert["prediction_source_kind"] == "deterministic_fallback"
            assert request_json("/api/v1/patients/P-1042/alert/lifecycle", "POST", {"action": "assign", "assignment_id": "N-SARAH", "assignment_evidence": "smoke"}, doctor)["state"] == "assigned"
            assert request_json("/api/v1/patients/P-1042/alert/lifecycle", "POST", {"action": "acknowledge"}, nurse)["state"] == "acknowledged"
            assert request_json("/api/v1/patients/P-1042/alert/events", token=doctor)[-1]["state"] == "acknowledged"
            recovered = request_json("/api/v1/patients/P-1042/alert", token=doctor)
            assert recovered["state"] == "acknowledged"
            print("Phase 3 smoke passed: threshold, fallback provenance, deduplication, lifecycle, and REST recovery verified; WebSocket recovery is covered by integration tests.")
            return 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())