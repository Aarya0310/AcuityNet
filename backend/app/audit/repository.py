import json

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.persistence.models import AuditEvent


class AuditRepository:
    def __init__(self, session: Session):
        self.session = session

    def append(self, *, actor_id, action, resource_type, resource_id, outcome, occurred_at, details=None):
        event = AuditEvent(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            occurred_at=occurred_at,
            details=json.dumps(details or {}, sort_keys=True),
        )
        self.session.add(event)
        self.session.flush()
        return event

    def list_for_alert(self, alert_id: int):
        return list(self.session.scalars(
            select(AuditEvent)
            .where(AuditEvent.resource_type == "alert", AuditEvent.resource_id == str(alert_id))
            .order_by(AuditEvent.occurred_at.asc(), AuditEvent.audit_id.asc())
        ))

    def list_for_patient(self, patient_id: str):
        return list(self.session.scalars(
            select(AuditEvent)
            .where(
                or_(
                    (AuditEvent.resource_type == "patient") & (AuditEvent.resource_id == patient_id),
                    AuditEvent.resource_type == "configuration",
                    AuditEvent.details.like(f'%"patient_id": "{patient_id}"%'),
                )
            )
            .order_by(AuditEvent.occurred_at.asc(), AuditEvent.audit_id.asc())
        ))