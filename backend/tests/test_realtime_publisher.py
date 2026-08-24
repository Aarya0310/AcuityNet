from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.realtime.publisher import RealtimePublisher


def test_publisher_commits_and_discards_session_messages(tmp_path):
    session = sessionmaker(bind=create_engine(f"sqlite:///{tmp_path / 'publisher.db'}"))()
    publisher = RealtimePublisher()
    publisher.publish_after_commit(session, {"event": "alert.invalidated", "patient_id": "P-1042"})
    assert publisher.published == []
    session.commit()
    assert publisher.published == [{"event": "alert.invalidated", "patient_id": "P-1042"}]
    publisher.publish_after_commit(session, {"event": "discarded"})
    session.rollback()
    assert publisher.published == [{"event": "alert.invalidated", "patient_id": "P-1042"}]
    session.close()