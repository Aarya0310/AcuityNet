from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth.policy import require_patient_access, require_roles
from backend.app.contracts.alerts import AlertResponse
from backend.app.contracts.dispatch import DispatchDecisionRequest, DispatchEvaluationResponse
from backend.app.dispatch.service import DispatchConflict


def dispatch_router(sessions, current_user, dispatch_service, alert_service):
    router = APIRouter()

    def authorize(user, patient_id):
        require_patient_access(user, patient_id)
        require_roles("admin", "doctor")(user)

    def evaluate(patient_id, user, retry):
        authorize(user, patient_id)
        with sessions.begin() as session:
            try:
                return dispatch_service.evaluate(session, patient_id, actor=user, retry=retry)
            except LookupError as error:
                raise HTTPException(status_code=404, detail=str(error)) from error

    @router.get("/api/v1/patients/{patient_id}/dispatch/evaluation", response_model=DispatchEvaluationResponse)
    def evaluation(patient_id: str, retry: bool = False, user=Depends(current_user)):
        return evaluate(patient_id, user, retry)

    @router.post("/api/v1/patients/{patient_id}/dispatch/retry", response_model=DispatchEvaluationResponse)
    def retry(patient_id: str, user=Depends(current_user)):
        return evaluate(patient_id, user, True)

    def decide(patient_id, request, user, decision_type):
        authorize(user, patient_id)
        with sessions.begin() as session:
            try:
                alert = dispatch_service.decide(session, patient_id, request, user, decision_type)
                return alert_service.to_response(session, alert, "new_alert")
            except PermissionError as error:
                raise HTTPException(status_code=403, detail=str(error)) from error
            except LookupError as error:
                raise HTTPException(status_code=404, detail=str(error)) from error
            except DispatchConflict as error:
                raise HTTPException(status_code=409, detail=str(error)) from error
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error

    @router.post("/api/v1/patients/{patient_id}/dispatch/confirm", response_model=AlertResponse)
    def confirm(patient_id: str, request: DispatchDecisionRequest, user=Depends(current_user)):
        return decide(patient_id, request, user, "confirmed")

    @router.post("/api/v1/patients/{patient_id}/dispatch/override", response_model=AlertResponse)
    def override(patient_id: str, request: DispatchDecisionRequest, user=Depends(current_user)):
        return decide(patient_id, request, user, "overridden")

    return router