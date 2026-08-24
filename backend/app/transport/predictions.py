from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from backend.app.auth.policy import require_patient_access, require_nurse_assignment
from backend.app.contracts.predictions import PredictionResponse
from backend.app.persistence.models import Bed, Patient, VitalObservation


def prediction_router(sessions, current_user, vitals_response, adapter) -> APIRouter:
    router = APIRouter()

    @router.get("/api/v1/patients/{patient_id}/prediction", response_model=PredictionResponse)
    def prediction(patient_id: str, user=Depends(current_user)):
        require_patient_access(user, patient_id)
        require_nurse_assignment(user, patient_id)
        with sessions() as session:
            row = session.scalar(select(VitalObservation).where(VitalObservation.patient_id == patient_id).order_by(VitalObservation.sequence.desc()))
            if row is None:
                raise HTTPException(status_code=404, detail="No observation available")
            patient, bed = session.get(Patient, patient_id), session.get(Bed, row.bed_id)
            vitals = vitals_response(row, patient, bed)
            return adapter.predict(row, vitals)

    return router