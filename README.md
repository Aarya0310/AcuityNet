# AcuityNet

AcuityNet is a research prototype for following a fictional patient through a deterministic simulated ICU monitoring journey. Phase 1 is not a clinical device and does not provide diagnosis or treatment advice.

## Windows PowerShell Setup

From the repository root, create a local environment and install the backend dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\backend[test]"
Copy-Item .env.example .env
```

The checked-in `.env.example` documents local defaults. Phase 2 requires a local-only `ACUITYNET_JWT_SECRET`; never commit it, print it, or place it in scripts.

Development-only demo credentials are `admin` / `admin-password`, `doctor` / `doctor-password`, and `sarah` / `sarah-password`. They are fictional prototype credentials and must not be reused.

## Clean Phase 1 Fixture

Run schema migration separately from fixture seeding. The seed is idempotent and creates fictional patient `P-1042`, its ICU bed, nurse, admission, history, and refresh configuration:

```powershell
cd backend
alembic --config alembic.ini upgrade head
alembic --config alembic.ini check
python -c "from app.persistence.database import make_engine, session_factory; from app.seed.demo_data import seed_demo_data; engine=make_engine('sqlite:///acuitynet.db'); seed_demo_data(session_factory(engine)())"
```

To explicitly remove the demo graph and observations before reseeding:

```powershell
python -c "from app.persistence.database import make_engine, session_factory; from app.seed.reset import reset_demo_data; engine=make_engine('sqlite:///acuitynet.db'); session=session_factory(engine)(); reset_demo_data(session); session.commit(); session.close()"
python -c "from app.persistence.database import make_engine, session_factory; from app.seed.demo_data import seed_demo_data; engine=make_engine('sqlite:///acuitynet.db'); seed_demo_data(session_factory(engine)())"
cd ..
```

Reset is explicit and destructive for the fictional Phase 1 fixture. It does not run migrations.

## Run The Stack

Start the API in one PowerShell window:

```powershell
uvicorn backend.app.main:app --reload
```

In a second window, start the frontend:

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

The browser monitoring view uses authenticated synthetic research-prototype endpoints. Bounded advance is Admin-only; Doctor and assigned Nurse Sarah have read access. The unassigned Nurse fixture is test-only and is never part of the three-account demo seed.

## Verification

The deterministic smoke runner launches and tears down its own Uvicorn child process and checks both required API responses, exact synthetic provenance, and freshness:

```powershell
python scripts/phase1_smoke.py
$env:ACUITYNET_JWT_SECRET = "set-a-local-secret-here"
python scripts/phase2_smoke.py
python -m pytest backend/tests/test_migrations.py backend/tests/test_safety_boundary.py backend/tests/test_seed.py backend/tests/test_scenario.py backend/tests/test_vital_contracts.py backend/tests/test_vitals_api.py -q
npm --prefix frontend run test -- --run
npm --prefix frontend run build
npm --prefix frontend run lint
```

The same migration checks can be rerun after an explicit reset:

```powershell
cd backend
alembic --config alembic.ini upgrade head
alembic --config alembic.ini check
cd ..
```