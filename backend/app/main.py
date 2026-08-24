from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from backend.app.contracts.vitals import AdvanceRequest, Provenance, VitalObservationResponse
from backend.app.persistence.database import make_engine, migrate_database, session_factory
from backend.app.persistence.models import VitalObservation
from backend.app.seed.demo_data import seed_demo_data

SCENARIO = ((98, 82, 16, 122, 78, 36.8), (97, 88, 18, 118, 76, 36.9), (95, 96, 22, 112, 72, 37.1), (92, 108, 27, 104, 68, 37.4), (88, 122, 32, 96, 62, 37.8))
PROTOTYPE_LABEL = "Research prototype: simulated ICU data, not clinical advice."


def create_app(database_url: str = "sqlite:///acuitynet.db") -> FastAPI:
    migrate_database(database_url)
    engine = make_engine(database_url)
    sessions = session_factory(engine)
    with sessions() as session:
        seed_demo_data(session)

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
            existing = session.scalar(select(VitalObservation).where(VitalObservation.patient_id == patient_id, VitalObservation.sequence == request.tick))
            if existing is not None:
                return response_for(existing)
            now = datetime.now(timezone.utc)
            values = SCENARIO[request.tick]
            row = VitalObservation(patient_id=patient_id, bed_id="ICU-12", sequence=request.tick, observed_at=now, received_at=now, spo2_percent=values[0], heart_rate_bpm=values[1], respiratory_rate_bpm=values[2], systolic_bp_mmhg=values[3], diastolic_bp_mmhg=values[4], temperature_c=values[5], source_kind="synthetic", source_name="acuitynet-simulator", scenario_id="p1042-deterioration-v1", scenario_version="1")
            session.add(row)
            session.flush()
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
