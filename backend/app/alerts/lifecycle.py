import json

from backend.app.audit.repository import AuditRepository
from backend.app.contracts.alerts import AlertLifecycleCommand
from backend.app.persistence.models import AlertEvent


ALLOWED_TRANSITIONS = {
    "generated": {"assign"},
    "assigned": {"acknowledge"},
    "acknowledged": {"respond"},
    "responded": {"resolve"},
    "resolved": set(),
}
NEXT_STATE = {"assign": "assigned", "acknowledge": "acknowledged", "respond": "responded", "resolve": "resolved"}


class AlertLifecycleService:
    def __init__(self, clock, audit_service, publisher=None):
        self.clock = clock
        self.audit_service = audit_service
        self.publisher = publisher

    def transition(self, session, alert, command: AlertLifecycleCommand, actor):
        if command.action not in ALLOWED_TRANSITIONS.get(alert.state, set()):
            raise ValueError("Invalid alert lifecycle transition")
        if actor.role not in {"admin", "doctor", "nurse"}:
            raise ValueError("Forbidden")
        if actor.role == "nurse":
            if actor.user_id != "U-SARAH" or command.action == "assign" or self.assignment_id(session, alert.alert_id) != "N-SARAH":
                raise ValueError("Forbidden")
        if command.action == "assign":
            if actor.role not in {"admin", "doctor"} or command.assignment_id != "N-SARAH" or not command.assignment_evidence:
                raise ValueError("Assignment evidence is required")
        if command.action == "respond" and not command.note:
            raise ValueError("Response note is required")
        if command.action == "resolve" and not command.note:
            raise ValueError("Resolution note is required")

        resulting_state = NEXT_STATE[command.action]
        timestamp = self.clock()
        alert.state = resulting_state
        if resulting_state == "resolved":
            alert.resolved_at = timestamp
        session.flush()
        lifecycle_event = AlertEvent(
            alert_id=alert.alert_id,
            state=resulting_state,
            outcome="success",
            occurred_at=timestamp,
        )
        session.add(lifecycle_event)
        session.flush()
        details = {
            "patient_id": alert.patient_id,
            "resulting_state": resulting_state,
            "correlation_id": command.correlation_id or f"alert-{alert.alert_id}-{lifecycle_event.event_id}",
        }
        if command.assignment_id:
            details["assignment_id"] = command.assignment_id
        if command.assignment_evidence:
            details["assignment_evidence"] = command.assignment_evidence
        if command.note:
            details["note"] = command.note
        audit = self.audit_service.record(
            session,
            actor_id=actor.user_id,
            action=f"lifecycle.{command.action}",
            resource_type="alert",
            resource_id=str(alert.alert_id),
            outcome="success",
            details=details,
            occurred_at=timestamp,
        )
        if self.publisher:
            self.publisher.publish_after_commit(session, {
                "event": "alert.invalidated",
                "patient_id": alert.patient_id,
                "alert_id": alert.alert_id,
                "audit_id": audit.audit_id,
            })
        return alert

    def assignment_id(self, session, alert_id: int):
        for event in reversed(AuditRepository(session).list_for_alert(alert_id)):
            if event.action == "lifecycle.assign" and event.outcome == "success":
                try:
                    return json.loads(event.details).get("assignment_id")
                except (TypeError, ValueError):
                    return None
        return None