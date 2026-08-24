# AcuityNet Setup

AcuityNet is a local research prototype using simulated ICU data. It is not a clinical device and does not provide diagnosis or treatment advice.

## Prerequisites

Install:

- Python 3.13 or newer
- Node.js and npm
- Git

The commands below target Windows PowerShell and should be run from the repository root.

## 1. Configure Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".\backend[test]"
```

If PowerShell blocks environment activation, run this once in PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 2. Set local environment variables

The API requires a local JWT signing secret. Set it for the current PowerShell session:

```powershell
$env:ACUITYNET_JWT_SECRET = "replace-with-a-local-secret"
$env:ACUITYNET_DATABASE_URL = "sqlite:///acuitynet.db"
```

Do not commit, print, or share the JWT secret. The application defaults to SQLite at `acuitynet.db` when `ACUITYNET_DATABASE_URL` is not set.

## 3. Create the database

Run migrations separately from demo seeding:

```powershell
Push-Location backend
alembic --config alembic.ini upgrade head
alembic --config alembic.ini check
Pop-Location
```

The application also runs migrations and idempotent seeding during startup. The explicit commands above make the setup state visible and reproducible.

## 4. Start the backend

Open PowerShell window 1 at the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
$env:ACUITYNET_JWT_SECRET = "replace-with-a-local-secret"
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Check that it is running:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
```

API documentation is available at:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

## 5. Start the frontend

Open PowerShell window 2 at the repository root:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open the URL printed by Vite, normally:

- http://127.0.0.1:5173

The frontend defaults to `http://127.0.0.1:8000` for the API. To use another API URL, set it before starting Vite:

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
npm --prefix frontend run dev
```

## Demo accounts

| Username | Password | Role |
|---|---|---|
| `admin` | `admin-password` | Admin |
| `doctor` | `doctor-password` | Doctor |
| `sarah` | `sarah-password` | Nurse |

These are fictional development credentials only.

## Reset and reseed the demo data

This removes the local fictional demo data and is destructive to the SQLite fixture. It does not run migrations:

```powershell
.\.venv\Scripts\Activate.ps1
python -c "from backend.app.persistence.database import make_engine, session_factory; from backend.app.seed.reset import reset_demo_data; engine=make_engine('sqlite:///acuitynet.db'); session=session_factory(engine)(); reset_demo_data(session); session.commit(); session.close()"
python -c "from backend.app.persistence.database import make_engine, session_factory; from backend.app.seed.demo_data import seed_demo_data; engine=make_engine('sqlite:///acuitynet.db'); seed_demo_data(session_factory(engine)())"
```

## Run verification

Backend tests:

```powershell
python -m pytest backend/tests -q
```

Frontend tests, typecheck, and production build:

```powershell
npm --prefix frontend run test -- --run
npm --prefix frontend run lint
npm --prefix frontend run build
```

Phase 3 smoke verification:

```powershell
$env:ACUITYNET_JWT_SECRET = "replace-with-a-local-secret"
python scripts/phase3_smoke.py
```

The smoke journey verifies deterministic deterioration, prediction fallback provenance, alert deduplication, lifecycle transitions, audit evidence, and REST recovery. Historian context, nurse candidate ranking, human confirmation, and assigned-Nurse workflow are Phase 4 capabilities and are not included yet.

## Troubleshooting

- **401 responses:** Set `ACUITYNET_JWT_SECRET` in the same PowerShell session used to start the API, then log in again.
- **Frontend cannot reach the API:** Confirm the backend is running on port `8000` and that `VITE_API_BASE_URL` matches it.
- **Port already in use:** Start Uvicorn with another port, then set `VITE_API_BASE_URL` to that port before starting Vite.
- **Migration errors:** Stop the API, verify the database URL, run `Push-Location backend; alembic --config alembic.ini upgrade head; Pop-Location` from the repository root, and restart the API.
