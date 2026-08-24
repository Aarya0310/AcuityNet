# External Integrations

**Analysis Date:** 2026-08-24

## APIs & External Services

**Frontend to backend REST API:**
- FastAPI service - serves health, refresh configuration, current synthetic vitals, and bounded fixture advance endpoints
  - SDK/Client: browser `fetch` wrapper in `frontend/src/api/client.ts`
  - Auth: none; requests do not send bearer tokens or session credentials
  - Boundary: `/health`, `/api/v1/configuration`, `/api/v1/configuration/refresh`, `/api/v1/patients/{patient_id}/vitals/current`, and `/api/v1/patients/{patient_id}/vitals/advance` in `backend/app/main.py`
- Local CORS boundary - allows only `http://127.0.0.1:5173` and `http://localhost:5173` in `backend/app/main.py`
  - SDK/Client: FastAPI `CORSMiddleware`
  - Auth: not applicable

**External APIs:**
- Not detected. No vendor SDK, remote API client, OAuth client, device connector, or outbound HTTP integration is implemented.
- WebSockets are not implemented in the current code, although the project state records them as a future additive option.

## Data Storage

**Databases:**
- SQLite file database - stores the seeded fictional P-1042 graph, refresh configuration, and vital observations
  - Connection: `sqlite:///acuitynet.db` default in `backend/app/main.py` and `backend/alembic.ini`; callers can pass another SQLAlchemy URL to `create_app()`
  - Client: SQLAlchemy 2.0.52 in `backend/app/persistence/database.py` and `backend/app/persistence/models.py`
  - Schema lifecycle: Alembic 1.19.1 migration in `backend/app/migrations/versions/0001_phase1_foundation.py`
  - Integrity: SQLite foreign keys are enabled on every created engine connection in `backend/app/persistence/database.py`

**File Storage:**
- Local filesystem only - the SQLite database file and migration assets; no object storage integration is detected

**Caching:**
- In-process frontend query cache only - `@tanstack/react-query` is initialized in `frontend/src/main.tsx`
- No Redis, distributed cache, or backend response cache is detected

## Authentication & Identity

**Auth Provider:**
- None in the current implementation
  - `backend/app/main.py` defines no authentication dependency or authorization middleware
  - `frontend/src/api/client.ts` sends no credentials or authorization header
  - Seeded demo data in `backend/app/seed/demo_data.py` contains patient, bed, nurse, admission, history, and configuration records, but no user identity provider
  - JWT-backed login and exactly three roles are Phase 2 requirements, not an existing integration

## Monitoring & Observability

**Error Tracking:**
- None detected. No Sentry, OpenTelemetry, hosted logging, or metrics client is present.

**Logs:**
- Python/Alembic standard logging configuration in `backend/alembic.ini`
- HTTP errors are returned as FastAPI `HTTPException` responses in `backend/app/main.py`; no centralized application logger is detected
- Frontend request failures become JavaScript `Error` objects in `frontend/src/api/client.ts`

## CI/CD & Deployment

**Hosting:**
- None detected. `README.md` documents local Uvicorn and Vite processes only.

**CI Pipeline:**
- None detected. No GitHub Actions workflow, Dockerfile, compose deployment, or hosting configuration is present.
- Verification is command-based: `scripts/phase1_smoke.py`, pytest, Vitest, TypeScript build, and TypeScript lint as documented in `README.md`.

## Environment Configuration

**Required env vars:**
- `VITE_API_BASE_URL` is the only environment variable referenced by application source, and it is optional because `frontend/src/api/client.ts` supplies a local default.
- No backend environment variable is referenced in the current application code.
- `.env.example` exists at the repository root; values were not read.

**Secrets location:**
- No application secret, credential store, or secret-management integration is detected.

## Webhooks & Callbacks

**Incoming:**
- None. The backend exposes synchronous REST routes only; no webhook receiver or callback endpoint is implemented.

**Outgoing:**
- None. The backend does not call external services, publish events, send notifications, or deliver webhooks.

## Service Boundaries

- Browser client to API: typed JSON contract boundary in `frontend/src/contracts/` and `backend/app/contracts/`.
- API to persistence: SQLAlchemy session factory and migration boundary in `backend/app/persistence/database.py`.
- API to synthetic scenario: `ObservationService` and `P1042Scenario` in `backend/app/vitals/`; source metadata is emitted as non-live synthetic provenance.
- Seed/reset tooling is separate from migration execution in `backend/app/seed/demo_data.py` and `backend/app/seed/reset.py`.

---

*Integration audit: 2026-08-24*