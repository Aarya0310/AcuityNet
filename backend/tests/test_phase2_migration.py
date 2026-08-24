from sqlalchemy import inspect

from backend.app.persistence.database import make_engine, migrate_database


def test_phase2_migration_creates_identity_columns_and_tables(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    migrate_database(database_url)
    inspector = inspect(make_engine(database_url))

    assert {"users", "nurses", "beds", "configurations"}.issubset(
        set(inspector.get_table_names())
    )
    assert {column["name"] for column in inspector.get_columns("users")} == {
        "user_id", "username", "display_name", "role", "password_digest", "active",
    }
    assert {column["name"] for column in inspector.get_columns("nurses")} >= {
        "nurse_id", "user_id", "display_name", "available",
    }


def test_phase2_migration_downgrade_removes_identity_table(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
    migrate_database(database_url)
    engine = make_engine(database_url)
    assert "users" in inspect(engine).get_table_names()
