from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from backend.app.contracts.patients import PatientSummary
from backend.app.contracts.vitals import (
    AdvanceRequest,
    SyntheticProvenance,
    VitalObservationResponse,
    resolve_freshness,
)
from backend.app.persistence.database import make_engine, migrate_database, session_factory
from backend.app.persistence.models import Bed, Patient, VitalObservation
from backend.app.seed.demo_data import seed_demo_data
from backend.app.vitals.scenario import P1042Scenario
from backend.app.vitals.service import ObservationService

PROTOTYPE_LABEL = "Research prototype: simulated ICU data, not clinical advice."


def create_app(
    database_url: str = "sqlite:///acuitynet.db",
    clock: Callable[[], datetime] | None = None,
) -> FastAPI:
    migrate_database(database_url)
    engine = make_engine(database_url)
    sessions = session_factory(engine)
    with sessions() as session:
        seed_demo_data(session)
    observation_service = ObservationService(P1042Scenario())
    now = clock or (lambda: datetime.now(timezone.utc))

    app = FastAPI(title="AcuityNet Research Prototype")

    def response_for(
        row: VitalObservation,
        patient: Patient,
        bed: Bed,
    ) -> VitalObservationResponse:
        return VitalObservationResponse(
            patient_id=row.patient_id,
            patient=PatientSummary(
                patient_id=patient.patient_id,
                display_name=patient.display_name,
                bed_id=bed.bed_id,
                unit=bed.unit,
            ),
            bed_id=row.bed_id,
            unit=bed.unit,
            sequence=row.sequence,
            observed_at=row.observed_at,
            received_at=row.received_at,
            spo2_percent=row.spo2_percent,
            heart_rate_bpm=row.heart_rate_bpm,
            respiratory_rate_bpm=row.respiratory_rate_bpm,
            systolic_bp_mmhg=row.systolic_bp_mmhg,
            diastolic_bp_mmhg=row.diastolic_bp_mmhg,
            temperature_c=row.temperature_c,
            provenance=SyntheticProvenance(
                source_kind=row.source_kind,
                source_name=row.source_name,
                scenario_id=row.scenario_id,
                scenario_version=row.scenario_version,
                is_live_bedside_feed=False,
            ),
            freshness=resolve_freshness(row.received_at, now()),
            prototype_label=PROTOTYPE_LABEL,
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/v1/patients/{patient_id}/vitals/advance", response_model=VitalObservationResponse)
    def advance(patient_id: str, request: AdvanceRequest):
        if patient_id != "P-1042":
            raise HTTPException(status_code=404, detail="Patient not found")
        with sessions.begin() as session:
            timestamp = now()
            row = observation_service.advance(session, patient_id, request.tick, timestamp)
            patient = session.get(Patient, row.patient_id)
            bed = session.get(Bed, row.bed_id)
            if patient is None or bed is None:
                raise HTTPException(status_code=404, detail="Patient context unavailable")
            return response_for(row, patient, bed)

    @app.get("/api/v1/patients/{patient_id}/vitals/current", response_model=VitalObservationResponse)
    def current(patient_id: str):
        with sessions() as session:
            row = session.scalar(select(VitalObservation).where(VitalObservation.patient_id == patient_id).order_by(VitalObservation.sequence.desc()))
            if row is None:
                raise HTTPException(status_code=404, detail="No observation available")
            patient = session.get(Patient, row.patient_id)
            bed = session.get(Bed, row.bed_id)
            if patient is None or bed is None:
                raise HTTPException(status_code=404, detail="Patient context unavailable")
            return response_for(row, patient, bed)

    return app


app = create_app()
