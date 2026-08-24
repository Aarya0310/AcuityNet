class RealtimePublisher:
    """Best-effort in-process notifications; REST state remains authoritative."""

    def __init__(self):
        self.published = []

    def publish_after_commit(self, session, message):
        from sqlalchemy import event

        if not session.info.get("realtime_listeners"):
            event.listen(session, "after_commit", self.after_commit, once=True)
            event.listen(session, "after_rollback", self.discard_on_rollback, once=True)
            session.info["realtime_listeners"] = True
        session.info.setdefault("realtime_messages", []).append(dict(message))

    def after_commit(self, session):
        self.published.extend(session.info.pop("realtime_messages", []))
        session.info.pop("realtime_listeners", None)

    def discard_on_rollback(self, session):
        session.info.pop("realtime_messages", None)
        session.info.pop("realtime_listeners", None)

    def commit(self, session):
        self.after_commit(session)

    def rollback(self, session):
        self.discard_on_rollback(session)