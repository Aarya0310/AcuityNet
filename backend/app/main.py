from collections.abc import Callable
from datetime import datetime, timezone
import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from backend.app.contracts.configuration import RefreshConfiguration
from backend.app.contracts.metadata import HealthResponse
from backend.app.contracts.patients import PatientSummary
from backend.app.contracts.vitals import (
    AdvanceRequest,
    SyntheticProvenance,
    VitalObservationResponse,
    resolve_freshness,
)
from backend.app.persistence.database import make_engine, migrate_database, session_factory
from backend.app.persistence.models import Alert, Bed, Patient, VitalObservation
from backend.app.transport.configuration import refresh_configuration
from backend.app.transport.health import health_response
from backend.app.seed.demo_data import seed_demo_data
from backend.app.vitals.scenario import P1042Scenario
from backend.app.vitals.service import ObservationService
from backend.app.safety.labels import (
    PROTOTYPE_LABEL,
    SYNTHETIC_SOURCE_KIND,
    SYNTHETIC_SOURCE_NAME,
)
from backend.app.transport.auth import auth_router
from backend.app.auth.policy import get_current_user, require_patient_access, require_roles, require_nurse_assignment
from backend.app.prediction.adapter import PredictionAdapter
from backend.app.transport.predictions import prediction_router
from backend.app.transport.admin import admin_router
from backend.app.alerts.service import AlertService
from backend.app.transport.alerts import alert_router
from backend.app.alerts.lifecycle import AlertLifecycleService
from backend.app.audit.service import AuditService
from backend.app.realtime.publisher import RealtimePublisher
from backend.app.transport.audit import audit_router
from backend.app.auth.service import load_token_user
from backend.app.transport.realtime import realtime_router
from backend.app.historian.service import HistorianService
from backend.app.transport.historian import historian_router
from backend.app.dispatch.service import DispatchService
from backend.app.transport.dispatch import dispatch_router


def create_app(
    database_url: str | None = None,
    clock: Callable[[], datetime] | None = None,
) -> FastAPI:
    database_url = database_url or os.environ.get("ACUITYNET_DATABASE_URL", "sqlite:///acuitynet.db")
    migrate_database(database_url)
    engine = make_engine(database_url)
    sessions = session_factory(engine)
    with sessions() as session:
        seed_demo_data(session)
    observation_service = ObservationService(P1042Scenario())
    now = clock or (lambda: datetime.now(timezone.utc))
    audit_service = AuditService(now)
    publisher = RealtimePublisher()
    alert_service = AlertService(PredictionAdapter(), now, audit_service, publisher)
    lifecycle_service = AlertLifecycleService(now, audit_service, publisher)
    dispatch_service = DispatchService(now, lifecycle_service, alert_service, audit_service)

    app = FastAPI(title="AcuityNet Research Prototype")
    app.include_router(auth_router(sessions))
    current_user = get_current_user(sessions)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    def audit_denial(request: Request, error: HTTPException):
        if error.status_code in {401, 403}:
            actor_id = None
            authorization = request.headers.get("authorization", "")
            if authorization.startswith("Bearer "):
                try:
                    with sessions() as lookup_session:
                        actor_id = load_token_user(lookup_session, authorization[7:]).user_id
                except Exception:
                    actor_id = None
            path_parts = request.url.path.strip("/").split("/")
            resource_id = next((part for part in path_parts if part.startswith("P-")), None)
            resource_type = "patient" if resource_id else "route"
            with sessions.begin() as audit_session:
                audit_service.record_denial(audit_session, actor_id=actor_id, action="access.denied", resource_type=resource_type, resource_id=resource_id, status_code=error.status_code)
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers=error.headers)

    def response_for(
        row: VitalObservation,
        patient: Patient,
        bed: Bed,
    ) -> VitalObservationResponse:
        observed_at = row.observed_at
        received_at = row.received_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=timezone.utc)
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
            observed_at=observed_at,
            received_at=received_at,
            spo2_percent=row.spo2_percent,
            heart_rate_bpm=row.heart_rate_bpm,
            respiratory_rate_bpm=row.respiratory_rate_bpm,
            systolic_bp_mmhg=row.systolic_bp_mmhg,
            diastolic_bp_mmhg=row.diastolic_bp_mmhg,
            temperature_c=row.temperature_c,
            provenance=SyntheticProvenance(
                source_kind=SYNTHETIC_SOURCE_KIND,
                source_name=SYNTHETIC_SOURCE_NAME,
                scenario_id=row.scenario_id,
                scenario_version=row.scenario_version,
                is_live_bedside_feed=False,
            ),
            freshness=resolve_freshness(row.received_at, now()),
            prototype_label=PROTOTYPE_LABEL,
        )

    app.include_router(prediction_router(sessions, current_user, response_for, PredictionAdapter()))
    app.include_router(admin_router(sessions, current_user, audit_service))
    app.include_router(alert_router(sessions, current_user, alert_service, lifecycle_service))
    app.include_router(audit_router(sessions, current_user))
    app.include_router(realtime_router(sessions, publisher))
    app.include_router(historian_router(sessions, current_user, HistorianService(now, alert_service, audit_service)))
    app.include_router(dispatch_router(sessions, current_user, dispatch_service, alert_service))
    app.state.realtime_publisher = publisher

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return health_response()

    @app.get(
        "/api/v1/configuration/refresh",
        response_model=RefreshConfiguration,
    )
    @app.get("/api/v1/configuration", response_model=RefreshConfiguration)
    def configuration():
        with sessions() as session:
            try:
                return refresh_configuration(session)
            except ValueError as error:
                raise HTTPException(status_code=500, detail=str(error)) from error

    @app.post("/api/v1/patients/{patient_id}/vitals/advance", response_model=VitalObservationResponse)
    def advance(patient_id: str, request: AdvanceRequest, user=Depends(current_user)):
        require_roles("admin")(user)
        require_patient_access(user, patient_id)
        with sessions.begin() as session:
            timestamp = now()
            tick = request.tick
            if tick is None:
                latest = session.scalar(
                    select(VitalObservation)
                    .where(VitalObservation.patient_id == patient_id)
                    .order_by(VitalObservation.sequence.desc())
                )
                tick = 0 if latest is None else latest.sequence + 1
            try:
                row = observation_service.advance(session, patient_id, tick, timestamp)
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
            patient = session.get(Patient, row.patient_id)
            bed = session.get(Bed, row.bed_id)
            if patient is None or bed is None:
                raise HTTPException(status_code=404, detail="Patient context unavailable")
            vitals = response_for(row, patient, bed)
            alert_service.evaluate_prediction(session, row, vitals)
            return vitals

    @app.get("/api/v1/patients/{patient_id}/vitals/current", response_model=VitalObservationResponse)
    def current(patient_id: str, user=Depends(current_user)):
        require_patient_access(user, patient_id)
        require_nurse_assignment(user, patient_id)
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
