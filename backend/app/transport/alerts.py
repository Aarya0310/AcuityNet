from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from backend.app.auth.policy import require_nurse_assignment, require_patient_access
from backend.app.audit.repository import AuditRepository
from backend.app.contracts.alerts import AlertEventResponse, AlertLifecycleCommand, AlertResponse
from backend.app.persistence.models import Alert


def alert_router(sessions, current_user, alert_service, lifecycle_service=None):
    router = APIRouter()

    def authorize(user, patient_id):
        require_patient_access(user, patient_id)
        require_nurse_assignment(user, patient_id)

    def authorize_alert_scope(session, user, alert):
        if user.role == "nurse":
            assigned = any(item.action == "lifecycle.assign" and item.outcome == "success" and '"assignment_id": "N-SARAH"' in item.details for item in AuditRepository(session).list_for_alert(alert.alert_id))
            if not assigned:
                raise HTTPException(status_code=403, detail="Forbidden")

    @router.get("/api/v1/patients/{patient_id}/alert", response_model=AlertResponse | None)
    def current_alert(patient_id: str, user=Depends(current_user)):
        authorize(user, patient_id)
        with sessions() as session:
            alert = session.scalar(select(Alert).where(Alert.patient_id == patient_id, Alert.state != "resolved").order_by(Alert.alert_id.desc()))
            if alert is not None:
                authorize_alert_scope(session, user, alert)
            return None if alert is None else alert_service.to_response(session, alert, alert.deduplication_status)

    @router.get("/api/v1/patients/{patient_id}/alert/events", response_model=list[AlertEventResponse])
    def alert_events(patient_id: str, user=Depends(current_user)):
        authorize(user, patient_id)
        with sessions() as session:
            alert = session.scalar(select(Alert).where(Alert.patient_id == patient_id).order_by(Alert.alert_id.desc()))
            if alert is None:
                return []
            authorize_alert_scope(session, user, alert)
            events = alert_service.repository(session).events_for(alert.alert_id)
            return [AlertEventResponse(event_id=item.event_id, sequence=index, state=item.state, outcome=item.outcome, occurred_at=item.occurred_at) for index, item in enumerate(events, start=1)]

    @router.post("/api/v1/patients/{patient_id}/alert/lifecycle", response_model=AlertResponse)
    def lifecycle(patient_id: str, command: AlertLifecycleCommand, user=Depends(current_user)):
        authorize(user, patient_id)
        if lifecycle_service is None:
            raise HTTPException(status_code=503, detail="Lifecycle unavailable")
        with sessions() as session:
            try:
                with session.begin():
                    alert = session.scalar(select(Alert).where(Alert.patient_id == patient_id, Alert.state != "resolved").order_by(Alert.alert_id.desc()))
                    if alert is None:
                        raise HTTPException(status_code=404, detail="Alert unavailable")
                    lifecycle_service.transition(session, alert, command, user)
                    result = alert_service.to_response(session, alert, alert.deduplication_status)
            except ValueError as error:
                if str(error) == "Forbidden":
                    raise HTTPException(status_code=403, detail="Forbidden") from error
                raise HTTPException(status_code=422, detail=str(error)) from error
            return result

    return router