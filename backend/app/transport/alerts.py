from fastapi import APIRouter, Depends
from sqlalchemy import select

from backend.app.auth.policy import require_nurse_assignment, require_patient_access
from backend.app.contracts.alerts import AlertResponse
from backend.app.persistence.models import Alert


def alert_router(sessions, current_user, alert_service):
    router = APIRouter()

    @router.get("/api/v1/patients/{patient_id}/alert", response_model=AlertResponse | None)
    def current_alert(patient_id: str, user=Depends(current_user)):
        require_patient_access(user, patient_id)
        require_nurse_assignment(user, patient_id)
        with sessions() as session:
            alert = session.scalar(select(Alert).where(Alert.patient_id == patient_id, Alert.state != "resolved").order_by(Alert.alert_id.desc()))
            return None if alert is None else alert_service.to_response(session, alert, alert.deduplication_status)

    return router