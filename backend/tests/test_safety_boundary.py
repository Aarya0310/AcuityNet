from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.contracts.metadata import HealthResponse, SafetyMetadata
from backend.app.contracts.vitals import SyntheticProvenance
from backend.app.main import create_app


def test_health_and_current_vitals_publish_centralized_safety_metadata(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    app = create_app(database_url, clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))

    with TestClient(app) as client:
        health = client.get("/health")
        client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0})
        current = client.get("/api/v1/patients/P-1042/vitals/current")

    expected = {
        "prototype_label": "Research prototype: simulated ICU data, not clinical advice.",
        "source_kind": "synthetic",
        "source_name": "acuitynet-simulator",
        "is_live_bedside_feed": False,
    }
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "metadata": expected}
    assert current.status_code == 200
    assert current.json()["prototype_label"] == expected["prototype_label"]
    assert current.json()["provenance"] == {
        "source_kind": expected["source_kind"],
        "source_name": expected["source_name"],
        "scenario_id": "p1042-deterioration-v1",
        "scenario_version": "1",
        "is_live_bedside_feed": False,
    }


def test_safety_contract_rejects_retrospective_or_bedside_metadata():
    with pytest.raises(ValidationError):
        SafetyMetadata(
            prototype_label="Research prototype: simulated ICU data, not clinical advice.",
            source_kind="retrospective",
            source_name="mimic-iv",
            is_live_bedside_feed=False,
        )

    with pytest.raises(ValidationError):
        SafetyMetadata(
            prototype_label="Research prototype: simulated ICU data, not clinical advice.",
            source_kind="synthetic",
            source_name="acuitynet-simulator",
            is_live_bedside_feed=True,
        )

    with pytest.raises(ValidationError):
        SyntheticProvenance(
            source_kind="retrospective",
            source_name="mimic-iv",
            scenario_id=None,
            scenario_version=None,
            is_live_bedside_feed=False,
        )


def test_health_response_requires_safety_metadata():
    response = HealthResponse(
        status="ok",
        metadata=SafetyMetadata(
            prototype_label="Research prototype: simulated ICU data, not clinical advice.",
            source_kind="synthetic",
            source_name="acuitynet-simulator",
            is_live_bedside_feed=False,
        ),
    )
    assert response.metadata.is_live_bedside_feed is False