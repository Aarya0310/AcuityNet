---
phase: 05-end-to-end-verification-and-demo-hardening
subphase: 05-05-documentation
document_type: demo-reset-path
status: active
---

# DEMO-RESET-PATH.md

## Complete Step-by-Step Local Demo Setup

This document provides exact reproduction steps for setting up a clean local environment and running the complete P-1042 patient flow from scratch.

**Total time:** ~15 minutes (first run with installs), ~2-3 minutes (reset for re-demo)

## Prerequisites

### Required Software
- **Python:** 3.10+ (`python --version`)
- **Node.js:** 18+ LTS (`node --version`)
- **npm:** 9+ (`npm --version`)
- **Git:** 2.30+ (`git --version`)
- **SQLite3:** Included with Python (verify: `sqlite3 --version`)
- **Playwright:** Will be installed via npm/pip

### Recommended for Windows
- **PowerShell 5.1+** (included with Windows 10/11) or **WSL 2** for bash commands
- **Git Bash** (included with Git for Windows) as alternative shell

### Recommended for macOS/Linux
- **bash** or **zsh** (standard)
- **Homebrew** (optional, for managing dependencies)

## Part 1: Initial Clone and Dependencies (First Run Only)

### Step 1.1: Clone the Repository

```bash
# Navigate to your workspace
cd ~/projects  # or your preferred location

# Clone the AcuityNet repo
git clone https://github.com/your-org/AcuityNet.git
cd AcuityNet
```

### Step 1.2: Set Up Backend Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (Git Bash):
source venv/Scripts/activate

# On macOS/Linux:
source venv/bin/activate

# Install backend dependencies
cd backend
pip install -e .
pip install pytest pytest-asyncio pytest-playwright playwright

# Run Alembic migrations (initializes database schema)
alembic upgrade head

# Return to project root
cd ..
```

### Step 1.3: Set Up Frontend and E2E Tools

```bash
# Install frontend dependencies
cd frontend
npm install

# Return to project root
cd ..

# Install Playwright browsers (one-time)
python -m playwright install chromium

# Optional: Install for other browsers
python -m playwright install firefox
python -m playwright install webkit
```

### Step 1.4: Verify Installation

```bash
# Check backend
python -c "from backend.app.main import create_app; print('✓ Backend imports OK')"

# Check frontend build
npm --prefix frontend run build

# Check Playwright
python -m pytest --version
python -c "from playwright.async_api import async_playwright; print('✓ Playwright OK')"
```

**Expected output:** All three checks pass with no errors.

## Part 2: Clean Database Reset for Demo (Repeatable)

Run these steps each time you want to reset the demo to a clean state with P-1042 ready.

### Step 2.1: Reset Database

```bash
# Activate venv if not already active
# (Windows PowerShell): .\venv\Scripts\Activate.ps1
# (macOS/Linux): source venv/bin/activate

# Navigate to backend
cd backend

# Remove old database if it exists
rm -Force acuitynet.db  # Windows PowerShell
# rm acuitynet.db  # macOS/Linux

# Reinitialize database
alembic upgrade head

# Return to project root
cd ..
```

### Step 2.2: Verify Clean Seed Data

```bash
# Start Python interactive session
python

# Inside Python:
from backend.app.main import create_app
from backend.app.persistence.database import migrate_database
from backend.app.seed.demo_data import seed_demo_data
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

database_url = "sqlite:///./backend/acuitynet.db"
engine = create_engine(database_url)
Sessions = sessionmaker(bind=engine)

with Sessions() as session:
    seed_demo_data(session)
    session.commit()
    
    # Verify
    from backend.app.persistence.models import Patient
    patient = session.query(Patient).filter_by(external_id="P-1042").first()
    print(f"✓ P-1042 seeded: {patient.name if patient else 'NOT FOUND'}")

# Exit Python
exit()
```

**Expected output:** `✓ P-1042 seeded: Patient at Index 1042`

## Part 3: Start Local Application Stack

### Step 3.1: Start Backend Server

```bash
# Terminal 1: Backend API
cd backend

# Activate venv
# (Windows PowerShell): .\venv\Scripts\Activate.ps1
# (macOS/Linux): source venv/bin/activate

# Start Uvicorn
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Expected: "Uvicorn running on http://127.0.0.1:8000"
```

### Step 3.2: Start Frontend Development Server

```bash
# Terminal 2: Frontend dev server
cd frontend

npm run dev

# Expected: "➜  Local:   http://localhost:5173/"
```

### Step 3.3: Verify Connectivity

```bash
# Terminal 3: Verify API health
curl http://127.0.0.1:8000/health

# Expected JSON response:
# {"status":"ok"}
```

**Ports to verify:**
- Backend API: `http://127.0.0.1:8000/` (should return 404, which means server running)
- Frontend: `http://localhost:5173/` (should show login page in browser)

## Part 4: Manual Demo Walkthrough

### Step 4.1: Admin Reset Workflow

Open browser to `http://localhost:5173/`

1. **Login as Admin**
   - Username: `admin`
   - Password: `admin-password`
   - Expected: Redirects to `/dashboard`

2. **Navigate to Admin Panel**
   - Click "Admin" or navigate to `/admin`
   - Expected: See reset button, patient list, settings

3. **Reset Database**
   - Click "Reset Database" button
   - Confirm in modal: "This will delete all alerts and assignments"
   - Expected: Database cleared, P-1042 removed from patient list

4. **Reseed Demo Data**
   - Click "Seed Demo Data" or run script again
   - Expected: P-1042 appears in patient list, status: "Ready"

5. **Verify Patient Ready**
   - Click P-1042 in patient list
   - Navigate to "Monitoring" tab
   - Expected: See vitals (SpO2: 95%, HR: 78, etc.), "Advance Vitals" button enabled

### Step 4.2: Doctor Historian Workflow

1. **Logout and Login as Doctor**
   - Logout (top-right menu → Logout)
   - Username: `doctor`
   - Password: `doctor-password`

2. **Navigate to Historian**
   - Click "Historian" tab or `/historian`
   - Expected: See P-1042 demographics, diagnoses, medications, labs, risk analysis, rules, timeline

3. **Review Historian Content**
   - Verify NO clinical language like "proven", "validated", "diagnostic"
   - Verify NO treatment recommendations
   - Verify risk analysis shows contextual factors
   - Verify rules explain when risk triggers (e.g., "oxygen < 92% for >5 minutes")

### Step 4.3: Doctor Dispatch Evaluation

1. **Navigate to Dispatch**
   - Click "Dispatch" tab or `/dispatch`
   - Expected: See candidate ranking with Sarah at top (score 0.93)

2. **Evaluate Candidates**
   - View candidate scores:
     - 40% Availability
     - 30% Proximity  
     - 20% Current Workload
     - 10% Acuity Compatibility
   - Expected: Sarah's score breakdown visible

3. **Confirm Assignment**
   - Click "Confirm" button
   - Fill form: "Assign to Sarah"
   - Click "Submit"
   - Expected: Success toast, alert transitions to "Acknowledged" state

### Step 4.4: Nurse Response Workflow

1. **Logout and Login as Nurse**
   - Logout
   - Username: `sarah`
   - Password: `sarah-password`

2. **View Assigned Alert**
   - Expected: Alert for P-1042 appears in "My Assignments" or alert list

3. **Acknowledge Alert**
   - Click "Acknowledge" button
   - Expected: Success message, button changes to "Record Response"

4. **Record Response Note**
   - Fill response textarea: "Patient stable, vitals improving, continuing IV fluids, monitor Q2H"
   - Click "Submit Response"
   - Expected: Success message, response saved

5. **Resolve Assignment**
   - Click "Resolve" button
   - Confirm modal: "Mark complete?"
   - Expected: Assignment marked resolved, status: "Completed"

### Step 4.5: Vitals Advance & Stale State

1. **Return to Admin View**
   - Logout, login as admin

2. **Navigate to Monitoring**
   - Go to P-1042 monitoring page
   - Expected: See fresh vitals with "Updated X seconds ago"

3. **Advance Vitals**
   - Click "Advance Vitals" button
   - Expected: SpO2, HR, etc. update with new values

4. **Observe Stale Badge (after 5 minutes)**
   - Wait 5+ minutes without refresh
   - Expected: "Stale" badge appears, showing "Last updated X minutes ago"

5. **Refresh to Clear Stale**
   - Click "Refresh" button
   - Expected: Stale badge disappears, vitals show fresh timestamp

## Part 5: Run Automated Test Suites

### Step 5.1: Run Backend Unit Tests

```bash
cd backend
python -m pytest tests/ -v --tb=short

# Expected: 13+ tests pass (phase 5 subset)
```

### Step 5.2: Run Frontend Component Tests

```bash
npm --prefix frontend run test -- --run

# Expected: 5 test files, 33+ tests pass
```

### Step 5.3: Run Backend E2E Smoke Test

```bash
python scripts/phase5_smoke.py

# Expected: Full journey completes without errors
```

### Step 5.4: Run Browser E2E Tests (if Playwright configured)

```bash
python -m pytest e2e/test_admin_reset_setup.py -v -s

# Expected: Browser launches, executes admin workflow, closes cleanly
```

## Part 6: Troubleshooting

### Issue: "Uvicorn failed to start"
**Symptoms:** `Address already in use :8000`
**Fix:**
```bash
# Find process on port 8000
# Windows: netstat -ano | findstr :8000
# macOS/Linux: lsof -i :8000

# Kill process (replace PID with actual process ID)
# Windows: taskkill /PID 1234 /F
# macOS/Linux: kill -9 1234
```

### Issue: "Patient P-1042 not found"
**Symptoms:** Historian page blank, monitoring shows no data
**Fix:**
```bash
# Re-run seed in Python shell
python
from backend.app.persistence.database import migrate_database
migrate_database("sqlite:///./backend/acuitynet.db")
from backend.app.seed.demo_data import seed_demo_data
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine("sqlite:///./backend/acuitynet.db")
Sessions = sessionmaker(bind=engine)
with Sessions() as s:
    seed_demo_data(s)
    s.commit()
exit()
```

### Issue: "Frontend won't connect to backend"
**Symptoms:** Network error 404 when loading historian
**Fix:**
```bash
# Verify backend running
curl http://127.0.0.1:8000/health
# Should return {"status":"ok"}

# Check frontend .env
# Ensure VITE_API_BASE_URL=http://127.0.0.1:8000

# Restart frontend dev server
npm --prefix frontend run dev
```

### Issue: "Playwright tests timeout"
**Symptoms:** E2E tests hang or timeout waiting for selectors
**Fix:**
```bash
# Verify data-testid attributes exist in React components
# Increase timeout in test
await page.wait_for_selector('[data-testid="alert-card"]', timeout=10000)

# Run in headful mode to see what's happening
PLAYWRIGHT_HEADLESS=false python -m pytest e2e/ -v -s
```

### Issue: "Database locked" during migrations
**Symptoms:** `UNIQUE constraint failed` or `database is locked`
**Fix:**
```bash
# Stop all processes using database
pkill -f uvicorn  # Kill backend
pkill -f pytest   # Kill tests

# Remove lockfile if it exists
rm -Force backend/acuitynet.db-wal  # Windows
rm backend/acuitynet.db-wal  # macOS/Linux

# Re-run migration
cd backend
alembic upgrade head
```

## Part 7: Quick Reference Commands

### Reset and Re-Demo (Copy-Paste Friendly)

```bash
# 1. Stop all servers (Ctrl+C in terminals)

# 2. Reset database
cd backend
rm -Force acuitynet.db
alembic upgrade head
python -c "from backend.app.seed.demo_data import seed_demo_data; from sqlalchemy import create_engine; from sqlalchemy.orm import sessionmaker; engine = create_engine('sqlite:///./acuitynet.db'); Sessions = sessionmaker(bind=engine); s = Sessions(); seed_demo_data(s); s.commit()"
cd ..

# 3. Restart backend
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
cd ..

# 4. Restart frontend
npm --prefix frontend run dev &

# 5. Open browser to http://localhost:5173
```

## Part 8: Performance Baseline

For reference, expected performance on a 2020 MacBook Pro (or equivalent):
- **Backend startup:** 2-3 seconds
- **Frontend dev server startup:** 3-5 seconds
- **Full page load (historian):** 1-2 seconds
- **Vitals advance:** <500ms
- **Dispatch evaluation:** <1 second
- **Nurse acknowledgement:** <500ms
- **Full admin-to-nurse workflow:** 3-5 minutes (manual clicks)
- **E2E test suite:** 20-30 seconds (browser automation)

## Summary

This DEMO-RESET-PATH documents the complete reproducible local setup for AcuityNet Phase 5. 

**Key milestones:**
1. ✓ Prerequisites installed (Python, Node.js, Playwright)
2. ✓ Backend and frontend running on localhost
3. ✓ P-1042 seeded and ready in database
4. ✓ Admin can reset and verify demo readiness
5. ✓ Doctor can review historian and dispatch
6. ✓ Nurse can acknowledge, respond, resolve
7. ✓ Vitals advance deterministically, stale state displays correctly
8. ✓ All test suites pass (unit, component, E2E)

**For production deployment**, replace SQLite with PostgreSQL and follow separate production deployment guide (not covered here).
