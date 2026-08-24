class RealtimePublisher:
    """Best-effort in-process notifications; REST state remains authoritative."""

    def __init__(self):
        self.published = []
        self._subscribers = {}

    def subscribe(self, patient_id, loop, queue):
        self._subscribers.setdefault(patient_id, set()).add((loop, queue))

    def unsubscribe(self, patient_id, loop, queue):
        subscribers = self._subscribers.get(patient_id)
        if subscribers is None:
            return
        subscribers.discard((loop, queue))
        if not subscribers:
            self._subscribers.pop(patient_id, None)

    def publish_after_commit(self, session, message):
        from sqlalchemy import event

        if not session.info.get("realtime_listeners"):
            event.listen(session, "after_commit", self.after_commit, once=True)
            event.listen(session, "after_rollback", self.discard_on_rollback, once=True)
            session.info["realtime_listeners"] = True
        session.info.setdefault("realtime_messages", []).append(dict(message))

    def after_commit(self, session):
        messages = session.info.pop("realtime_messages", [])
        self.published.extend(messages)
        for message in messages:
            for loop, queue in tuple(self._subscribers.get(message.get("patient_id"), ())):
                loop.call_soon_threadsafe(queue.put_nowait, dict(message))
        session.info.pop("realtime_listeners", None)

    def discard_on_rollback(self, session):
        session.info.pop("realtime_messages", None)
        session.info.pop("realtime_listeners", None)

    def commit(self, session):
        self.after_commit(session)

    def rollback(self, session):
        self.discard_on_rollback(session)