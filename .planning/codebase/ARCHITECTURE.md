<!-- refreshed: 2026-08-24 -->
# Architecture

**Analysis Date:** 2026-08-24

## System Overview

```text
+----------------------+       REST/JSON        +-----------------------------+
| React monitoring UI  | <--------------------> | FastAPI application         |
| `frontend/src/`      |                        | `backend/app/main.py`       |
+----------+-----------+                        +--------------+--------------+
           |                                                   |
           |                                                   v
           |                                      +-----------------------------+
           |                                      | Contracts and route helpers |
           |                                      | `backend/app/contracts/`    |
           |                                      | `backend/app/transport/`    |
           |                                      +--------------+--------------+
           |                                                     |
           |                                                     v
           |                                      +-----------------------------+
           |                                      | Scenario/domain service     |
           |                                      | `backend/app/vitals/`       |
           |                                      +--------------+--------------+
           |                                                     |
           |                                                     v
           |                                      +-----------------------------+
           |                                      | SQLAlchemy + SQLite         |
           |                                      | `backend/app/persistence/`  |
           |                                      +--------------+--------------+
           |                                                     |
           |                                                     v
           |                                      +-----------------------------+
           |                                      | Alembic migrations + seed   |
           |                                      | `backend/app/migrations/`   |
           |                                      | `backend/app/seed/`         |
           |                                      +-----------------------------+
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Application factory and routes | Creates FastAPI, configures CORS, initializes database state, and exposes health, configuration, current-vitals, and bounded-advance endpoints | `backend/app/main.py` |
| API contracts | Defines Pydantic request/response models, constrained literals, and server-side freshness resolution | `backend/app/contracts/vitals.py`, `backend/app/contracts/configuration.py`, `backend/app/contracts/metadata.py`, `backend/app/contracts/patients.py` |
| Transport helpers | Builds health and refresh-configuration responses from small route-facing functions | `backend/app/transport/health.py`, `backend/app/transport/configuration.py` |
| Observation domain | Owns the bounded P-1042 deterioration sequence and idempotent persistence of observations | `backend/app/vitals/scenario.py`, `backend/app/vitals/service.py` |
| Persistence | Creates SQLAlchemy engines/session factories, enables SQLite foreign keys, runs Alembic, and maps domain tables | `backend/app/persistence/database.py`, `backend/app/persistence/models.py` |
| Fixture initialization | Idempotently creates the fictional patient, bed, nurse, history, admission, and refresh configuration | `backend/app/seed/demo_data.py` |
| Safety metadata | Centralizes the prototype label and synthetic source identity | `backend/app/safety/labels.py` |
| Monitoring UI | Fetches current vitals, loads refresh configuration, performs bounded advances, and renders context, vitals, freshness, provenance, and prototype labeling | `frontend/src/App.tsx`, `frontend/src/monitoring/MonitoringPage.tsx` |

## Pattern Overview

**Overall:** Small modular monolith with a REST boundary and a presentation-only React client.

**Key Characteristics:**
- The backend is authoritative for persisted observations, freshness, provenance, configuration, and safety labels.
- The application factory wires infrastructure and route handlers; route handlers coordinate persistence, contracts, and the observation service.
- The synthetic scenario is deterministic and bounded to ticks 0 through 4; repeated ticks are idempotent through a database uniqueness constraint and service lookup.
- The frontend keeps display state locally but reads server-owned observation and freshness metadata rather than deriving clinical state.
- Database schema management is explicit through Alembic, while demo fixture setup is separate and idempotent.

## Layers

**Presentation Layer:**
- Purpose: Render the monitoring workflow and initiate read/advance operations.
- Location: `frontend/src/`
- Contains: React entry point, app shell, monitoring page, safety display components, API client, and TypeScript contracts.
- Depends on: REST endpoints exposed by `backend/app/main.py`.
- Used by: Browser/Vite runtime.

**Transport/API Layer:**
- Purpose: Expose HTTP resources and translate persistence/domain results into validated response contracts.
- Location: `backend/app/main.py`, `backend/app/transport/`
- Contains: FastAPI application factory, route handlers, CORS policy, health/configuration response helpers.
- Depends on: Contracts, persistence, seed setup, and vitals service.
- Used by: `frontend/src/api/client.ts` and backend HTTP tests.

**Contract Layer:**
- Purpose: Define the wire format and enforce input/output constraints.
- Location: `backend/app/contracts/`, mirrored by `frontend/src/contracts/`.
- Contains: Pydantic models, enums/literals, validation, and TypeScript interfaces/unions.
- Depends on: Standard typing and Pydantic on the backend.
- Used by: Routes, API client, and UI components.

**Domain/Simulation Layer:**
- Purpose: Generate and persist deterministic synthetic observations.
- Location: `backend/app/vitals/`
- Contains: `P1042Scenario` and `ObservationService`.
- Depends on: SQLAlchemy session and persistence model.
- Used by: The advance route in `backend/app/main.py`.

**Persistence/Schema Layer:**
- Purpose: Store fixture context, configuration, and observations and evolve the schema.
- Location: `backend/app/persistence/`, `backend/app/migrations/`
- Contains: SQLAlchemy models, engine/session setup, Alembic environment, and migration versions.
- Depends on: SQLite by default, SQLAlchemy, and Alembic.
- Used by: Application startup, seed code, domain service, and tests.

**Safety Layer:**
- Purpose: Keep prototype and synthetic-source identity consistent across responses and UI.
- Location: `backend/app/safety/`, `frontend/src/safety/`
- Contains: Backend constants plus provenance and prototype banner components.
- Depends on: Contracts on the backend and typed observation data in the frontend.
- Used by: Response assembly and monitoring presentation.

## Data Flow

### Primary Request Path

1. Vite loads `frontend/src/main.tsx`, which creates a TanStack Query client and renders `frontend/src/App.tsx`.
2. `frontend/src/App.tsx` requests current P-1042 data through `frontend/src/api/client.ts`.
3. `backend/app/main.py` queries the latest `VitalObservation`, then loads its `Patient` and `Bed` context.
4. The route builds `VitalObservationResponse`, adding `SyntheticProvenance`, server-calculated freshness, and the centralized prototype label.
5. `frontend/src/monitoring/MonitoringPage.tsx` renders the response and separately requests refresh configuration.
6. Manual or automatic refresh posts to `/api/v1/patients/{patient_id}/vitals/advance`; the route resolves the next sequence, calls `ObservationService.advance`, and then the UI reads current data again.

### Application Startup Flow

1. `create_app` in `backend/app/main.py` calls `migrate_database`.
2. `backend/app/persistence/database.py` configures Alembic against the supplied database URL and upgrades to `head`.
3. The app creates an engine and session factory; SQLite connections receive `PRAGMA foreign_keys=ON`.
4. `seed_demo_data` creates or updates the P-1042 fixture and configuration, then commits.
5. The application constructs one `ObservationService(P1042Scenario())` for route use.

### Observation Advancement Flow

1. `AdvanceRequest` validates that automatic advancement uses a supported interval or that an explicit tick is bounded.
2. The route rejects patients other than `P-1042` and derives the next sequence when no tick is supplied.
3. `ObservationService.advance` returns an existing row for a repeated patient/sequence or asks `P1042Scenario.values_for` for deterministic values.
4. The service writes a `VitalObservation` with scenario identity and synthetic source metadata.
5. `response_for` joins patient/bed context and emits the typed response.

**State Management:**
- Durable state is SQLite-backed through SQLAlchemy models and transactions.
- The backend owns observation sequence and freshness semantics.
- The frontend owns transient selected refresh interval, current displayed observation, and an in-flight refresh guard.
- Automatic refresh uses a browser interval and stops when the bounded backend operation returns validation status 422.

## Key Abstractions

**Application Factory:**
- Purpose: Build an isolated FastAPI application against a supplied database and clock, which enables deterministic tests.
- Examples: `backend/app/main.py`
- Pattern: Dependency injection through `create_app(database_url, clock)` with nested route closures over sessions and time.

**Scenario Adapter:**
- Purpose: Represent deterministic synthetic values independently from HTTP concerns.
- Examples: `backend/app/vitals/scenario.py`
- Pattern: Dataclass with scenario identity, bounded `values_for`, and reset semantics.

**Observation Service:**
- Purpose: Apply scenario values to persistence and provide idempotent advancement.
- Examples: `backend/app/vitals/service.py`
- Pattern: Small service object receiving a SQLAlchemy `Session` and explicit timestamp.

**Wire Contract:**
- Purpose: Prevent unsafe or malformed data from crossing the API boundary.
- Examples: `backend/app/contracts/vitals.py`, `frontend/src/contracts/vitals.ts`
- Pattern: Pydantic constrained fields and TypeScript structural types kept in parallel.

## Entry Points

**Backend ASGI entry point:**
- Location: `backend/app/main.py`
- Triggers: Uvicorn or an ASGI test client imports module-level `app`.
- Responsibilities: Construct the application and register all current endpoints.

**Frontend browser entry point:**
- Location: `frontend/src/main.tsx`
- Triggers: Vite loads the module referenced by `frontend/index.html`.
- Responsibilities: Create the query client, mount React, and include global styles.

**Backend smoke entry point:**
- Location: `scripts/phase1_smoke.py`
- Triggers: Direct Python execution during Phase 1 verification.
- Responsibilities: Start Uvicorn, call health/current/advance paths, assert deterministic responses, and clean up.

## Architectural Constraints

- **Threading:** FastAPI route functions are synchronous; SQLAlchemy sessions are opened per operation. Browser refresh is timer-driven.
- **Global state:** Module-level `app = create_app()` in `backend/app/main.py` performs startup migration and seeding on import; the frontend has one module-level `QueryClient` in `frontend/src/main.tsx`.
- **Circular imports:** No deliberate circular dependency chain is detected; Alembic includes a fallback import in `backend/app/migrations/env.py` for alternate invocation roots.
- **Scenario scope:** `P1042Scenario` accepts only the `p1042-demo` seed and only ticks 0 through 4.
- **API authority:** REST current GET remains authoritative; the UI advances through REST and then re-reads current data.
- **Safety boundary:** All current observations are labeled synthetic and non-bedside through typed provenance and prototype metadata.

## Anti-Patterns

### Route-Coupled Response Assembly

**What happens:** `backend/app/main.py` contains route coordination and the `response_for` mapper, including patient/bed joins and safety metadata.
**Why it's wrong:** Additional response shapes or workflows can make the application factory a concentration point for persistence and presentation translation.
**Do this instead:** Keep new route-specific contracts in `backend/app/contracts/` and move reusable mapping or use-case logic beside the owning domain/persistence abstraction before adding more route complexity.

### Client-Derived Freshness or Provenance

**What happens:** The UI could infer currentness from browser time or treat a feed as live based on rendering state.
**Why it's wrong:** It would bypass the server-owned safety and source-of-truth boundary.
**Do this instead:** Render `freshness`, `provenance`, and `prototype_label` supplied by `backend/app/contracts/vitals.py` through `frontend/src/monitoring/MonitoringPage.tsx` and `frontend/src/safety/`.

## Error Handling

**Strategy:** Backend validation and resource errors become FastAPI 4xx responses; frontend API helpers throw on non-2xx responses and the monitoring page handles bounded-operation exhaustion by returning to manual mode.

**Patterns:**
- Pydantic rejects extra fields and invalid tick/interval combinations in `backend/app/contracts/vitals.py`.
- Routes use `HTTPException` for unsupported patients, missing observations/context, and domain `ValueError` conversion.
- Database work uses context-managed sessions and transactions in `backend/app/main.py`.
- Frontend `getJson` and `getCurrentVitals` check `response.ok` before parsing JSON.

## Cross-Cutting Concerns

**Logging:** Alembic uses Python logging configuration from `backend/alembic.ini`; application-specific logging is not detected in route or service code.
**Validation:** Pydantic contracts validate HTTP payloads; SQLAlchemy constraints enforce foreign keys and unique patient/sequence observations; TypeScript provides frontend compile-time shape checks.
**Authentication:** No authentication or authorization layer is implemented yet; this is consistent with Phase 2 being the current planning focus.
**Safety:** `backend/app/safety/labels.py` and typed provenance fields make synthetic status explicit at the API and UI boundary.

---

*Architecture analysis: 2026-08-24*
