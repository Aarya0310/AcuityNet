from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth.policy import require_patient_access, require_roles
from backend.app.contracts.historian import AnnotationCreate, AnnotationResponse, HistorianResponse


def historian_router(sessions, current_user, historian_service):
    router = APIRouter()

    @router.get("/api/v1/patients/{patient_id}/historian", response_model=HistorianResponse)
    def historian(patient_id: str, user=Depends(current_user)):
        require_patient_access(user, patient_id)
        require_roles("admin", "doctor")(user)
        with sessions.begin() as session:
            try:
                return historian_service.project(session, patient_id)
            except LookupError as error:
                raise HTTPException(status_code=404, detail=str(error)) from error

    @router.post("/api/v1/patients/{patient_id}/annotations", response_model=AnnotationResponse, status_code=201)
    def annotate(patient_id: str, request: AnnotationCreate, user=Depends(current_user)):
        require_patient_access(user, patient_id)
        require_roles("doctor")(user)
        with sessions.begin() as session:
            try:
                return historian_service.annotate(session, patient_id, user, request.text)
            except LookupError as error:
                raise HTTPException(status_code=404, detail=str(error)) from error

    return router