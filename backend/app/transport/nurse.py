import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from backend.app.alerts.lifecycle import ALLOWED_TRANSITIONS
from backend.app.audit.repository import AuditRepository
from backend.app.auth.policy import require_nurse_assignment, require_patient_access
from backend.app.contracts.vitals import resolve_freshness
from backend.app.persistence.models import Alert, Bed, Patient, PatientContextFact, VitalObservation
from backend.app.safety.labels import PROTOTYPE_LABEL


def nurse_router(sessions, current_user, alert_service, lifecycle_service=None):
    router = APIRouter()

    def assignment_id_for_alert(session, alert_id: int):
        for event in reversed(AuditRepository(session).list_for_alert(alert_id)):
            if event.action == "lifecycle.assign" and event.outcome == "success":
                try:
                    return json.loads(event.details or "{}").get("assignment_id")
                except (TypeError, ValueError):
                    return None
        return None

    def allowed_actions_for(alert):
        return sorted(ALLOWED_TRANSITIONS.get(alert.state, set()))

    @router.get("/api/v1/patients/{patient_id}/nurse/work")
    def nurse_work(patient_id: str, user=Depends(current_user)):
        require_patient_access(user, patient_id)
        require_nurse_assignment(user, patient_id)

        with sessions() as session:
            patient = session.get(Patient, patient_id)
            bed = session.scalar(select(Bed).where(Bed.patient_id == patient_id))
            if patient is None or bed is None:
                raise HTTPException(status_code=404, detail="Patient context unavailable")

            alert = session.scalar(select(Alert).where(Alert.patient_id == patient_id).order_by(Alert.alert_id.desc()))
            if alert is None:
                raise HTTPException(status_code=404, detail="Assigned work unavailable")

            if user.role == "nurse":
                assigned = any(
                    event.action == "lifecycle.assign"
                    and event.outcome == "success"
                    and json.loads(event.details or "{}").get("assignment_id") == "N-SARAH"
                    for event in AuditRepository(session).list_for_alert(alert.alert_id)
                )
                if not assigned:
                    raise HTTPException(status_code=403, detail="Forbidden")

            observation = session.scalar(
                select(VitalObservation)
                .where(VitalObservation.patient_id == patient_id)
                .order_by(VitalObservation.sequence.desc())
            )
            if observation is None:
                raise HTTPException(status_code=404, detail="No observation available")

            facts = list(session.scalars(
                select(PatientContextFact)
                .where(PatientContextFact.patient_id == patient_id)
                .order_by(PatientContextFact.effective_at.asc(), PatientContextFact.fact_id.asc())
            ))
            diagnosis = next((fact.label for fact in facts if fact.category == "diagnosis" and fact.value is not None and fact.is_complete), None)
            prior_events = [fact.label for fact in facts if fact.category == "icu_event" and fact.is_complete]
            timeline = [
                {
                    "entry_id": f"audit:{event.audit_id}",
                    "entry_type": "audit",
                    "occurred_at": event.occurred_at,
                    "title": event.action,
                    "detail": event.outcome,
                }
                for event in AuditRepository(session).list_for_patient(patient_id)
            ]
            if alert is not None:
                timeline.append({
                    "entry_id": f"alert:{alert.alert_id}",
                    "entry_type": "alert",
                    "occurred_at": alert.created_at,
                    "title": "Alert generated",
                    "detail": alert.priority,
                })
            timeline.sort(key=lambda entry: (entry["occurred_at"], entry["entry_id"]))

            assignment_id = assignment_id_for_alert(session, alert.alert_id)
            issue = alert_service.to_response(session, alert, alert.deduplication_status)
            return {
                "patient_id": patient_id,
                "display_name": patient.display_name,
                "bed_id": bed.bed_id,
                "unit": bed.unit,
                "assignment_id": assignment_id,
                "alert": issue,
                "vitals": {
                    "patient_id": observation.patient_id,
                    "patient": {"patient_id": patient.patient_id, "display_name": patient.display_name, "bed_id": bed.bed_id, "unit": bed.unit},
                    "bed_id": observation.bed_id,
                    "unit": bed.unit,
                    "sequence": observation.sequence,
                    "observed_at": observation.observed_at,
                    "received_at": observation.received_at,
                    "spo2_percent": observation.spo2_percent,
                    "heart_rate_bpm": observation.heart_rate_bpm,
                    "respiratory_rate_bpm": observation.respiratory_rate_bpm,
                    "systolic_bp_mmhg": observation.systolic_bp_mmhg,
                    "diastolic_bp_mmhg": observation.diastolic_bp_mmhg,
                    "temperature_c": observation.temperature_c,
                    "provenance": {
                        "source_kind": "synthetic",
                        "source_name": "acuitynet-simulator",
                        "scenario_id": observation.scenario_id,
                        "scenario_version": observation.scenario_version,
                        "is_live_bedside_feed": False,
                    },
                    "freshness": resolve_freshness(observation.received_at, __import__("datetime").datetime.now(__import__("datetime").timezone.utc)),
                    "prototype_label": PROTOTYPE_LABEL,
                },
                "diagnosis": diagnosis,
                "prior_events": prior_events,
                "timeline": timeline,
                "allowed_actions": allowed_actions_for(alert),
            }

    return router
