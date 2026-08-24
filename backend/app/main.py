from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from backend.app.contracts.vitals import AdvanceRequest, Provenance, VitalObservationResponse
from backend.app.persistence.database import make_engine, migrate_database, session_factory
from backend.app.persistence.models import VitalObservation
from backend.app.seed.demo_data import seed_demo_data
from backend.app.vitals.scenario import P1042Scenario
from backend.app.vitals.service import ObservationService

PROTOTYPE_LABEL = "Research prototype: simulated ICU data, not clinical advice."


def create_app(database_url: str = "sqlite:///acuitynet.db") -> FastAPI:
    migrate_database(database_url)
    engine = make_engine(database_url)
    sessions = session_factory(engine)
    with sessions() as session:
        seed_demo_data(session)
    observation_service = ObservationService(P1042Scenario())

    app = FastAPI(title="AcuityNet Research Prototype")

    def response_for(row: VitalObservation) -> VitalObservationResponse:
        return VitalObservationResponse(
            patient_id=row.patient_id,
            bed_id=row.bed_id,
            sequence=row.sequence,
            observed_at=row.observed_at,
            received_at=row.received_at,
            spo2_percent=row.spo2_percent,
            heart_rate_bpm=row.heart_rate_bpm,
            respiratory_rate_bpm=row.respiratory_rate_bpm,
            systolic_bp_mmhg=row.systolic_bp_mmhg,
            diastolic_bp_mmhg=row.diastolic_bp_mmhg,
            temperature_c=row.temperature_c,
            provenance=Provenance(source_kind=row.source_kind, source_name=row.source_name, scenario_id=row.scenario_id, scenario_version=row.scenario_version, is_live_bedside_feed=False),
            freshness="fresh",
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
            now = datetime.now(timezone.utc)
            row = observation_service.advance(session, patient_id, request.tick, now)
            return response_for(row)

    @app.get("/api/v1/patients/{patient_id}/vitals/current", response_model=VitalObservationResponse)
    def current(patient_id: str):
        with sessions() as session:
            row = session.scalar(select(VitalObservation).where(VitalObservation.patient_id == patient_id).order_by(VitalObservation.sequence.desc()))
            if row is None:
                raise HTTPException(status_code=404, detail="No observation available")
            return response_for(row)

    return app


app = create_app()
