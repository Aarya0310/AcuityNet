class AuditService:
    def __init__(self, clock):
        self.clock = clock

    def record(self, session, *, actor_id, action, resource_type, resource_id, outcome, details=None, occurred_at=None):
        from backend.app.audit.repository import AuditRepository

        return AuditRepository(session).append(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            occurred_at=occurred_at or self.clock(),
            details=details,
        )

    def record_denial(self, session, *, actor_id, action, resource_type, resource_id, status_code):
        return self.record(
            session,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome="denied",
            details={"denial_status": status_code},
        )