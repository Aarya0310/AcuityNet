from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from backend.app.contracts.patients import PatientSummary
from backend.app.contracts.vitals import (
    AdvanceRequest,
    FreshnessState,
    SyntheticProvenance,
    VitalObservationResponse,
    resolve_freshness,
)


def test_current_contract_contains_typed_patient_vitals_and_synthetic_provenance():
    response = VitalObservationResponse(
        patient_id="P-1042",
        patient=PatientSummary(
            patient_id="P-1042", display_name="Fictional Patient 1042", bed_id="ICU-12", unit="ICU"
        ),
        bed_id="ICU-12",
        unit="ICU",
        sequence=0,
        observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        spo2_percent=98,
        heart_rate_bpm=82,
        respiratory_rate_bpm=16,
        systolic_bp_mmhg=122,
        diastolic_bp_mmhg=78,
        temperature_c=36.8,
        provenance=SyntheticProvenance(
            source_kind="synthetic",
            source_name="acuitynet-simulator",
            scenario_id="p1042-deterioration-v1",
            scenario_version="1",
            is_live_bedside_feed=False,
        ),
        freshness=FreshnessState.FRESH,
        prototype_label="Research prototype: simulated ICU data, not clinical advice.",
    )

    assert response.patient.bed_id == response.bed_id == "ICU-12"
    assert response.unit == "ICU"
    assert response.provenance.is_live_bedside_feed is False


def test_freshness_policy_resolves_boundaries_and_transport_failure():
    received_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert resolve_freshness(received_at, received_at + timedelta(seconds=15)) == FreshnessState.FRESH
    assert resolve_freshness(received_at, received_at + timedelta(seconds=15, microseconds=1)) == FreshnessState.STALE
    assert resolve_freshness(received_at, received_at + timedelta(seconds=60)) == FreshnessState.STALE
    assert resolve_freshness(received_at, received_at + timedelta(seconds=60, microseconds=1)) == FreshnessState.DISCONNECTED
    assert resolve_freshness(received_at, received_at, transport_ok=False) == FreshnessState.DISCONNECTED
    assert resolve_freshness(None, received_at) == FreshnessState.UNAVAILABLE


def test_phase_one_contract_rejects_retrospective_provenance_and_unbounded_advancement():
    with pytest.raises(ValidationError):
        SyntheticProvenance(
            source_kind="retrospective",
            source_name="mimic-iv",
            scenario_id=None,
            scenario_version=None,
            is_live_bedside_feed=False,
        )

    with pytest.raises(ValidationError):
        AdvanceRequest(tick=5)
    with pytest.raises(ValidationError):
        AdvanceRequest(tick=-1)