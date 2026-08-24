from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8765"
EXPECTED_LABEL = "Research prototype: simulated ICU data, not clinical advice."
EXPECTED_PROVENANCE = {
    "source_kind": "synthetic",
    "source_name": "acuitynet-simulator",
    "scenario_id": "p1042-deterioration-v1",
    "scenario_version": "1",
    "is_live_bedside_feed": False,
}
SUPPORTED_FRESHNESS = {"fresh", "stale", "disconnected", "unavailable"}


def get_json(path: str) -> dict:
    request = Request(f"{BASE_URL}{path}", headers={"Accept": "application/json"})
    with urlopen(request, timeout=3) as response:
        if response.status != 200:
            raise AssertionError(f"{path} returned HTTP {response.status}")
        return json.load(response)


def post_json(path: str, payload: dict) -> dict:
    request = Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=3) as response:
        if response.status != 200:
            raise AssertionError(f"{path} returned HTTP {response.status}")
        return json.load(response)


def wait_for_health() -> None:
    deadline = time.monotonic() + 20
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            get_json("/health")
            return
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = error
            time.sleep(0.25)
    raise RuntimeError(f"Uvicorn did not become ready: {last_error}")


def main() -> int:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_health()
        health = get_json("/health")
        post_json("/api/v1/patients/P-1042/vitals/advance", {"tick": 0})
        current = get_json("/api/v1/patients/P-1042/vitals/current")

        assert health == {
            "status": "ok",
            "metadata": {
                "prototype_label": EXPECTED_LABEL,
                "source_kind": "synthetic",
                "source_name": "acuitynet-simulator",
                "is_live_bedside_feed": False,
            },
        }
        assert current["provenance"] == EXPECTED_PROVENANCE
        assert current["prototype_label"] == EXPECTED_LABEL
        assert current["freshness"] in SUPPORTED_FRESHNESS
        print("Phase 1 smoke passed: /health and P-1042 current vitals are synthetic and labeled.")
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