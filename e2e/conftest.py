"""
Pytest fixtures for Playwright end-to-end tests.

Provides:
- browser_context: Isolated Chromium browser context
- app_server: Subprocess Uvicorn with temp SQLite, migrations, and demo data
- auth_tokens: JWT tokens for admin, doctor, and nurse roles
- page_with_auth: Pre-authenticated Playwright page
"""
import asyncio
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("ACUITYNET_JWT_SECRET", "test-secret-key-at-least-32-chars-long!!!")

# Import app creation and fixtures from backend
from backend.app.main import create_app
from backend.app.persistence.models import User
from backend.app.seed.demo_data import seed_demo_data
from backend.app.persistence.database import migrate_database


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def browser() -> AsyncGenerator[Browser, None]:
    """Start isolated Chromium browser for the session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
def temp_database() -> Generator[str, None, None]:
    """Create isolated temp SQLite database for this test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "e2e_test.db"
        database_url = f"sqlite:///{db_path}"
        
        # Run migrations
        migrate_database(database_url)
        
        # Seed demo data
        engine = create_engine(database_url)
        Sessions = sessionmaker(bind=engine)
        with Sessions() as session:
            seed_demo_data(session)
            session.commit()
        engine.dispose()
        
        yield database_url


@pytest.fixture(scope="function")
def app_server(temp_database) -> Generator[tuple[str, datetime], None, None]:
    """
    Start isolated Uvicorn subprocess with temp SQLite.
    Yields (base_url, now_ref) where now_ref is a mutable datetime for clock injection.
    """
    database_url = temp_database
    now = [datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)]
    
    # No local app instance is needed here; the subprocess owns the database lifecycle.
    # Start Uvicorn subprocess on random port
    port = 8001
    env = os.environ.copy()
    env["ACUITYNET_DATABASE_URL"] = database_url
    env["ACUITYNET_JWT_SECRET"] = "test-secret-key-at-least-32-chars-long!!!"
    
    # Create a script file to start the server
    script_path = Path(tempfile.gettempdir()) / "start_uvicorn.py"
    script_content = f"""
import uvicorn
from backend.app.main import create_app
from datetime import datetime, timezone

now = [datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)]
app = create_app("{database_url}", clock=lambda: now[0])
uvicorn.run(app, host="127.0.0.1", port={port}, log_level="info")
"""
    script_path.write_text(script_content)
    
    # Start subprocess
    proc = subprocess.Popen(
        ["python", str(script_path)],
        cwd="c:\\Users\\ADMIN\\Downloads\\AcuityNet",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to start
    time.sleep(3)
    
    base_url = f"http://127.0.0.1:{port}"
    
    try:
        yield base_url, now
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        script_path.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def auth_headers(app_server, temp_database) -> dict[str, dict[str, str]]:
    """
    Generate JWT Bearer tokens for each role.
    Returns: {"admin": {"Authorization": "Bearer ..."}, "doctor": {...}, "nurse": {...}}
    """
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    database_url = temp_database
    os.environ.setdefault("ACUITYNET_JWT_SECRET", "test-secret-key-at-least-32-chars-long!!!")
    app = create_app(database_url)
    with TestClient(app) as client:
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
    app.state.engine.dispose()
    
    return tokens


@pytest_asyncio.fixture(scope="function")
async def browser_context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """Create isolated browser context for this test."""
    context = await browser.new_context(
        ignore_https_errors=True,
        record_video_dir=None,
    )
    yield context
    await context.close()


@pytest_asyncio.fixture(scope="function")
async def page_with_auth(
    browser_context: BrowserContext,
    app_server: tuple[str, list],
) -> AsyncGenerator[tuple[Page, str], None]:
    """
    Create authenticated Playwright page with pre-login.
    Returns (page, base_url).
    """
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    # Navigate to app
    await page.goto(f"{base_url}/")
    
    # Perform admin login via UI
    await page.fill('input[name="username"]', "admin")
    await page.fill('input[name="password"]', "admin-password")
    await page.click('button[type="submit"]')
    
    # Wait for redirect to dashboard
    await page.wait_for_url("**/dashboard", timeout=5000)
    
    yield page, base_url
    await page.close()


@pytest.fixture(scope="function")
def advance_time(app_server):
    """Fixture to advance mutable datetime in app server."""
    base_url, now_ref = app_server
    
    def advance(seconds: int):
        """Advance time by N seconds."""
        now_ref[0] = datetime.fromtimestamp(
            now_ref[0].timestamp() + seconds,
            tz=timezone.utc
        )
    
    return advance
