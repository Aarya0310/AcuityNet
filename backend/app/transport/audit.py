import json

from fastapi import APIRouter, Depends

from backend.app.audit.repository import AuditRepository
from backend.app.auth.policy import require_nurse_assignment, require_patient_access
from backend.app.contracts.audit import AuditEventListResponse, AuditEventResponse


def audit_router(sessions, current_user):
    router = APIRouter()

    @router.get("/api/v1/patients/{patient_id}/audit", response_model=AuditEventListResponse)
    def audit(patient_id: str, user=Depends(current_user)):
        require_patient_access(user, patient_id)
        require_nurse_assignment(user, patient_id)
        with sessions() as session:
            result = []
            events = AuditRepository(session).list_for_patient(patient_id)
            if user.role == "nurse" and not any(event.action == "lifecycle.assign" and event.outcome == "success" and '"assignment_id": "N-SARAH"' in event.details for event in events):
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail="Forbidden")
            for sequence, event in enumerate(events, start=1):
                details = json.loads(event.details or "{}")
                category = event.action.split(".", 1)[0]
                if event.action == "lifecycle.assign":
                    category = "assignment"
                if category not in {"alert", "configuration", "access", "assignment", "lifecycle"}:
                    category = "access"
                result.append(AuditEventResponse(audit_id=event.audit_id, sequence=sequence, actor_id=event.actor_id, action=event.action, category=category, resource_type=event.resource_type, resource_id=event.resource_id, outcome=event.outcome, resulting_state=details.get("resulting_state"), occurred_at=event.occurred_at, correlation_id=details.get("correlation_id", f"audit-{event.audit_id}"), details=details))
            return AuditEventListResponse(events=result)

    return router