from sqlalchemy import func, select

from backend.app.persistence.database import make_engine, migrate_database, session_factory
from backend.app.persistence.models import Nurse, User
from backend.app.seed.demo_data import seed_demo_data
from backend.app.seed.reset import reset_demo_data


def test_seed_creates_exactly_three_demo_accounts_and_assigned_sarah(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    migrate_database(database_url)
    sessions = session_factory(make_engine(database_url))
    with sessions() as session:
        seed_demo_data(session)
        users = session.scalars(select(User).order_by(User.user_id)).all()
        assert [(user.user_id, user.role) for user in users] == [
            ("U-ADMIN", "admin"), ("U-DOCTOR", "doctor"), ("U-SARAH", "nurse"),
        ]
        assert session.get(Nurse, "N-SARAH").user_id == "U-SARAH"
        assert session.scalar(select(func.count()).select_from(User)) == 3


def test_reset_reseed_restores_identity_graph(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    migrate_database(database_url)
    sessions = session_factory(make_engine(database_url))
    with sessions() as session:
        seed_demo_data(session)
        reset_demo_data(session)
        seed_demo_data(session)
        assert session.get(User, "U-ADMIN") is not None
        assert session.get(User, "U-DOCTOR") is not None
        assert session.get(User, "U-SARAH") is not None
        assert session.get(Nurse, "N-SARAH").user_id == "U-SARAH"
