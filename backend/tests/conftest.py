"""
Shared pytest fixtures for backend tests and E2E tests.

Provides:
- temp_database: Isolated SQLite database with migrations and seeding
- auth_headers: JWT tokens for all roles
- advance_time: Fixture to advance mutable datetime
"""
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import create_app
from backend.app.persistence.database import migrate_database
from backend.app.seed.demo_data import seed_demo_data

os.environ.setdefault("ACUITYNET_JWT_SECRET", "test-secret-key-at-least-32-chars-long!!!")


@pytest.fixture(scope="function")
def temp_database() -> Generator[str, None, None]:
    """
    Create isolated temp SQLite database for this test.
    Runs migrations and seeds demo data.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database_url = f"sqlite:///{db_path}"
        
        # Run migrations
        migrate_database(database_url)
        
        # Seed demo data
        engine = create_engine(database_url)
        Sessions = sessionmaker(bind=engine)
        with Sessions() as session:
            seed_demo_data(session)
            session.commit()
        
        yield database_url


@pytest.fixture(scope="function")
def auth_headers(temp_database) -> dict[str, dict[str, str]]:
    """
    Generate JWT Bearer tokens for each role.
    
    Returns:
        {"admin": {"Authorization": "Bearer ..."}, "doctor": {...}, "nurse": {...}}
    """
    database_url = temp_database
    
    # Set JWT secret for testing
    os.environ["ACUITYNET_JWT_SECRET"] = "test-secret-key-at-least-32-chars-long!!!"
    
    app = create_app(database_url)
    client = TestClient(app)
    
    # Login with each role
    tokens = {}
    credentials = {
        "admin": {"username": "admin", "password": "admin-password"},
        "doctor": {"username": "doctor", "password": "doctor-password"},
        "nurse": {"username": "sarah", "password": "sarah-password"},
    }
    
    for role, creds in credentials.items():
        response = client.post("/api/v1/auth/login", json=creds)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            tokens[role] = {"Authorization": f"Bearer {access_token}"}
        else:
            raise RuntimeError(f"Failed to login as {role}: {response.text}")
    
    return tokens


@pytest.fixture(scope="function")
def app_with_mutable_clock(temp_database) -> tuple[TestClient, list[datetime]]:
    """
    Create app and test client with mutable datetime for testing.
    
    Returns:
        (client, now_ref) where now_ref is a list with one mutable datetime element
    """
    database_url = temp_database
    now_ref = [datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)]
    
    app = create_app(database_url, clock=lambda: now_ref[0])
    client = TestClient(app)
    
    return client, now_ref


@pytest.fixture(scope="function")
def advance_time():
    """
    Fixture factory to advance mutable datetime.
    Usage: advance_time(lambda_now_ref, seconds)
    """
    def _advance(now_ref: list[datetime], seconds: int):
        """Advance time by N seconds."""
        now_ref[0] = datetime.fromtimestamp(
            now_ref[0].timestamp() + seconds,
            tz=timezone.utc
        )
    
    return _advance
