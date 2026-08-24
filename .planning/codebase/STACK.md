# Technology Stack

**Analysis Date:** 2026-08-24

## Languages

**Primary:**
- Python >=3.13 - FastAPI application, domain services, persistence, migrations, seed/reset tooling, and backend tests in `backend/`
- TypeScript - React frontend, typed API contracts, Vite configuration, and frontend tests in `frontend/src/`

**Secondary:**
- JavaScript/JSX runtime output - Vite and React build tooling; source uses TypeScript with JSX
- SQL - Alembic-generated relational schema operations in `backend/app/migrations/versions/0001_phase1_foundation.py`

## Runtime

**Environment:**
- Python 3.13 or newer - required by `backend/pyproject.toml`
- Node.js/npm - required by the Vite frontend; exact Node version is not pinned in the repository
- Browser DOM - frontend runs as a React single-page application

**Package Manager:**
- pip - installs the editable backend project and its `test` extra, as documented in `README.md`
- npm - installs frontend dependencies from `frontend/package.json`
- Lockfile: `frontend/package-lock.json` present; no backend lockfile detected

## Frameworks

**Core:**
- FastAPI 0.141.1 - HTTP API and OpenAPI application in `backend/app/main.py`
- React 19.2.8 and React DOM 19.2.8 - browser UI in `frontend/src/`
- SQLAlchemy 2.0.52 - ORM and database access in `backend/app/persistence/`
- Pydantic 2.13.4 - request/response contracts in `backend/app/contracts/`

**Testing:**
- pytest 9.1.1 - backend tests in `backend/tests/`
- Vitest 4.1.11 - frontend test runner configured in `frontend/vite.config.ts`
- Testing Library for React 16.3.2 and jest-dom 6.9.1 - frontend component tests in `frontend/src/monitoring/MonitoringPage.test.tsx`

**Build/Dev:**
- Uvicorn 0.52.4 - local ASGI server for `backend.app.main:app`, documented in `README.md`
- Vite 8.2.2 - frontend development server and production bundler configured in `frontend/vite.config.ts`
- TypeScript 5.9.3 - strict frontend type checking through `frontend/tsconfig.app.json`
- Alembic 1.19.1 - schema migration execution through `backend/alembic.ini` and `backend/app/migrations/`

## Key Dependencies

**Critical:**
- `fastapi==0.141.1` - exposes health, configuration, current-vitals, and bounded-advance endpoints in `backend/app/main.py`
- `sqlalchemy==2.0.52` - persists patients, beds, configuration, and vital observations in `backend/app/persistence/models.py`
- `alembic==1.19.1` - migrates the database before application startup in `backend/app/persistence/database.py`
- `pydantic==2.13.4` - validates API contracts and typed synthetic provenance in `backend/app/contracts/`
- `@tanstack/react-query` 5.x - provides frontend query state and caching in `frontend/src/App.tsx` and `frontend/src/main.tsx`

**Infrastructure:**
- `httpx==0.28.1` - backend test client dependency used by FastAPI tests
- `uvicorn==0.52.4` - ASGI runtime
- `@vitejs/plugin-react` 6.x - React transform integration for Vite
- `jsdom` 27.x - browser-like environment for Vitest

## Configuration

**Environment:**
- Backend database URL is passed to `create_app()` and defaults to `sqlite:///acuitynet.db` in `backend/app/main.py`
- Frontend API base URL reads `VITE_API_BASE_URL`, falling back to `http://127.0.0.1:8000`, in `frontend/src/api/client.ts`
- `.env.example` exists at the repository root; its contents were not inspected because environment files are sensitive
- No runtime settings framework or secret provider is detected

**Build:**
- `frontend/vite.config.ts` configures the React plugin and Vitest jsdom setup
- `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, and `frontend/tsconfig.node.json` define TypeScript project settings
- `backend/alembic.ini` defines migration location, SQLite default URL, and logging
- Root `pyproject.toml` configures pytest discovery and Python import path

## Platform Requirements

**Development:**
- Windows PowerShell workflow is documented in `README.md`
- Python 3.13+, pip, Node.js/npm, a local file system, and two local processes for Uvicorn and Vite

**Production:**
- No production deployment target, container definition, process manager, or CI deployment configuration is detected
- Current design is a local research prototype; SQLite is the active persistence target

---

*Stack analysis: 2026-08-24*