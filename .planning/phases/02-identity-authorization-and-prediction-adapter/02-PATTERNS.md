# Phase 2: Identity, Authorization, and Prediction Adapter - Pattern Map

**Mapped:** 2026-08-24  
**Files analyzed:** 31 inferred new/modified files  
**Analogs found:** 24 / 31

Phase 2 has no `CONTEXT.md`; the file inventory below is grounded in `02-RESEARCH.md`, Phase 2 requirements, and roadmap success criteria. Preserve the existing modular-monolith boundaries and keep REST contracts authoritative.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/app/persistence/models.py` | model | CRUD | same file | exact |
| `backend/app/migrations/versions/0002_identity_prediction.py` | migration | transform | `0001_phase1_foundation.py` | exact |
| `backend/app/seed/demo_data.py` | seed | CRUD | same file | exact |
| `backend/app/auth/security.py` | service/utility | request-response | `vitals/service.py` | partial |
| `backend/app/auth/dependencies.py` | dependency/middleware | request-response | `main.py` route closures | partial |
| `backend/app/auth/service.py` | service | CRUD | `vitals/service.py` | role-match |
| `backend/app/auth/policy.py` | utility | request-response | `contracts/vitals.py` validation | partial |
| `backend/app/transport/auth.py` | route/controller | request-response | `main.py` | role-match |
| `backend/app/transport/configuration.py` | service/transport | CRUD | same file | exact |
| `backend/app/prediction/adapter.py` | service/adapter | request-response | `vitals/service.py` | partial |
| `backend/app/prediction/fallback.py` | service | transform | `vitals/scenario.py` | partial |
| `backend/app/transport/predictions.py` | route/controller | request-response | `main.py` | role-match |
| `backend/app/contracts/auth.py` | contract | request-response | `contracts/vitals.py` | role-match |
| `backend/app/contracts/predictions.py` | contract | request-response | `contracts/vitals.py` | role-match |
| `backend/app/contracts/configuration.py` | contract | request-response | same file | exact |
| `backend/app/contracts/metadata.py` | contract | request-response | same file | exact |
| `backend/app/tests/test_auth.py` | test | request-response | `backend/tests/test_vitals_api.py` | role-match |
| `backend/tests/test_authorization.py` | test | request-response | `test_vitals_api.py` | role-match |
| `backend/tests/test_prediction.py` | test | transform | `test_scenario.py` | role-match |
| `backend/tests/test_phase2_migration.py` | test | CRUD | `test_migrations.py` | exact |
| `backend/tests/test_phase2_seed.py` | test | CRUD | `test_seed.py` | exact |
| `frontend/src/auth/AuthContext.tsx` | provider/state | request-response | `main.tsx` QueryClient provider | partial |
| `frontend/src/auth/LoginPage.tsx` | component | request-response | `monitoring/MonitoringPage.tsx` | role-match |
| `frontend/src/auth/ProtectedRoute.tsx` | component/guard | request-response | `App.tsx` loading branch | partial |
| `frontend/src/navigation/AppShell.tsx` | component/navigation | request-response | `App.tsx` | role-match |
| `frontend/src/api/client.ts` | utility | request-response | same file | exact |
| `frontend/src/contracts/auth.ts` | contract | request-response | `contracts/vitals.ts` | exact |
| `frontend/src/contracts/predictions.ts` | contract | request-response | `contracts/vitals.ts` | exact |
| `frontend/src/prediction/PredictionPage.tsx` | component | request-response | `MonitoringPage.tsx` | role-match |
| `frontend/src/App.tsx` | route/state composition | request-response | same file | exact |
| `frontend/src/**/*.test.tsx` | test | request-response | `MonitoringPage.test.tsx` | role-match |

## Pattern Assignments

### Backend application wiring and dependencies

**Analogs:** `backend/app/main.py` lines 1-143; `backend/app/persistence/database.py` lines 1-25.

Copy the explicit import grouping, `create_app(database_url, clock)` injection, migration-before-engine setup, and `session_factory(engine)` construction. Route handlers use a session per operation: `with sessions() as session` for reads and `with sessions.begin() as session` for mutations. Keep auth dependencies request-scoped and never hold a SQLAlchemy session for a token or WebSocket lifetime. Protected routes should receive a typed current-user dependency and apply policy checks before querying the resource.

The current app has no middleware/auth analog. Keep `CORSMiddleware` configuration in the factory (`main.py` lines 34-41), but do not treat hidden frontend navigation as authorization. Known failures should remain explicit FastAPI `HTTPException` responses, preserving exception chaining as in `main.py` lines 93-113.

### Authentication, sessions, and authorization

**Closest partial analogs:** `backend/app/main.py` lines 19-32 and 85-143; `backend/app/contracts/vitals.py` lines 18-35.

There is no existing auth implementation. New JWT code should follow the project's small typed-module style: separate token/password mechanics (`auth/security.py`), current-user FastAPI dependencies (`auth/dependencies.py`), and resource/role policy (`auth/policy.py`). Model exactly `Admin`, `Doctor`, and `Nurse`; reject unknown roles at the contract/model boundary. Return a stable login/session DTO and use bearer authentication on protected API routes. A missing, malformed, expired, or invalid token should produce 401; a valid identity lacking role/resource/assignment permission should produce 403. Scope database reads to the authorized patient/assignment rather than loading all rows and filtering in React.

Use the existing `ConfigDict(extra="forbid")`, `Field`, `Literal`, and typed response approach from `contracts/vitals.py` lines 18-61. Do not persist plaintext passwords or put mutable authorization decisions in JWT claims without checking the current user record. Seed deterministic demo accounts through `seed_demo_data.py` lines 6-38, using stable identifiers and idempotent update-or-insert behavior.

### SQLAlchemy models, migration, and seeding

**Analogs:** `backend/app/persistence/models.py` lines 1-67; `backend/app/migrations/versions/0001_phase1_foundation.py` lines 1-34; `backend/app/seed/demo_data.py` lines 6-38; `backend/app/seed/reset.py` lines 12-15.

Extend `models.py` with typed `Mapped[...]` columns, explicit string lengths, non-null constraints, and named uniqueness constraints. Add the Phase 2 revision after `0001_phase1_foundation`; author upgrade and downgrade explicitly and preserve foreign-key ordering. Do not use `create_all()` or seed code to evolve schema. If a user references a nurse or patient, declare and test the foreign key.

Follow the seed loop that selects stable IDs, creates missing rows, updates existing rows, flushes before dependent rows, and commits once. Add users/roles/configuration by stable external identifiers and make repeated startup seeding preserve counts and IDs. Extend reset deletion order before parent rows, as `reset.py` demonstrates. Reuse `make_engine()`'s SQLite foreign-key listener (`database.py` lines 9-17) and migration helper (`database.py` lines 20-25).

### Pydantic contracts and configuration endpoints

**Analogs:** `backend/app/contracts/vitals.py` lines 7-61; `backend/app/contracts/configuration.py` lines 1-12; `backend/app/contracts/patients.py` lines 1-7; `backend/app/transport/configuration.py` lines 1-17.

Keep wire DTOs separate from ORM models. Use constrained literals/enums for roles, prediction level/source, fallback status, and configuration keys. Prediction responses should include risk score, level, predicted event, probability, horizon, current vitals, provenance, prototype label, model identifier/version, and an explicit `source_kind` or fallback reason. The server owns safety and source metadata; frontend types mirror the serialized shape.

For configuration, copy `refresh_configuration()`'s session lookup, parse persisted values, and raise `ValueError` for unavailable or invalid configuration. Route translation belongs in `main.py`'s `HTTPException` pattern. Admin update DTOs must forbid extras and constrain threshold/refresh values; do not expose arbitrary key/value writes. Keep configuration reads role-aware and mutations Admin-only.

### Prediction/service adapter and deterministic fallback

**Analogs:** `backend/app/vitals/scenario.py` lines 1-29; `backend/app/vitals/service.py` lines 7-48; `backend/app/main.py` lines 45-83.

No prediction adapter exists yet. Use a small adapter interface with a primary existing-ML implementation and a deterministic fallback implementation. Keep model invocation outside transport, accept a typed current-vitals/context input, and return one stable prediction DTO regardless of source. The fallback should be pure and repeatable like `P1042Scenario.values_for()`; never use global randomness or wall-clock values. Capture model name/version, fallback availability/reason, input observation sequence, and safety/prototype metadata in the result.

The route should authorize the patient first, obtain the authoritative current observation, call the adapter, and return the contract. A missing observation is a resource error; an unavailable model is a successful, explicitly labeled fallback result unless the contract cannot be produced. Do not call a prediction adapter directly from React or let the UI infer risk level from the numeric score.

### Frontend routing, navigation, and state

**Analogs:** `frontend/src/main.tsx` lines 1-13; `frontend/src/App.tsx` lines 1-16; `frontend/src/api/client.ts` lines 1-29; `frontend/src/monitoring/MonitoringPage.tsx` lines 19-58.

There is no router or auth state yet. Preserve the module-level `QueryClient` provider in `main.tsx` and make auth state a provider above the app shell. Extend `api/client.ts`'s centralized `API_BASE_URL` and `getJson()` boundary with login/logout/session calls and a bearer-token mechanism; every non-2xx response must remain an `Error` rather than being silently treated as data. Keep token persistence narrowly scoped to the prototype's selected session strategy and clear it on logout/401.

Use a role-aware shell/navigation component to expose only permitted destinations, but pair every view with `ProtectedRoute` or equivalent session checks and rely on backend 401/403 responses for enforcement. Keep loading/error/empty branches explicit as in `App.tsx`, and use TanStack Query for server state rather than duplicating fetch state in every page. Monitoring's local transient state and cleanup pattern (`MonitoringPage.tsx` lines 25-68) is the model for timers/effects; auth/session effects must also clean up and avoid updating unmounted components.

### Testing conventions

**Backend analogs:** `backend/tests/test_vitals_api.py` lines 1-92; `backend/tests/test_walking_skeleton.py` lines 1-105; `backend/tests/test_migrations.py` lines 1-67; `backend/tests/test_scenario.py` and `backend/tests/test_vital_contracts.py`.

Use temporary SQLite URLs, `create_app(database_url, clock=...)`, real `TestClient`, real migrations, real seed, and native `assert` statements. Add focused matrix coverage for login success/failure, missing/expired token, each role, forbidden resource and assignment scope, and admin-only configuration mutation. Assert status codes and response bodies, not implementation details. Keep persistence and foreign-key checks real; do not mock SQLAlchemy or auth dependencies in integration tests.

**Frontend analog:** `frontend/src/monitoring/MonitoringPage.test.tsx` lines 1-155.

Co-locate component tests, use `describe`/`it`, semantic Testing Library queries, `vi.stubGlobal("fetch", ...)`, fake timers where session expiry/refresh is time-driven, and cleanup/un-stubbing in hooks. Test navigation by visible role-appropriate links and denied/redirect states, and test prediction rendering for model, deterministic fallback, provenance, and non-clinical labeling. Add API-client tests only if the new token/error behavior cannot be covered through component tests.

## Shared Patterns

### Dependency injection and transactions

**Source:** `backend/app/main.py` lines 25-32, 104-128; `backend/app/persistence/database.py` lines 9-25.  
**Apply to:** auth dependencies, protected routes, prediction routes, configuration routes, and tests.

Keep application construction parameterized for isolated databases and clocks. Open one short-lived session per request/operation, use `sessions.begin()` for mutations, and let the application own transaction boundaries.

### Contract validation and safety metadata

**Source:** `backend/app/contracts/vitals.py` lines 18-61; `backend/app/safety/labels.py`; `frontend/src/contracts/vitals.ts` lines 1-28; `frontend/src/safety/PrototypeBanner.tsx` lines 1-5.  
**Apply to:** auth, prediction, configuration, and all new user-facing views.

Keep bounded domain states typed on both sides. Prediction/model/fallback output must carry explicit source and prototype metadata; no UI should call synthetic data live bedside data or present research rules as validated clinical advice.

### REST/cache authority

**Source:** `frontend/src/api/client.ts` lines 3-29; `frontend/src/App.tsx` lines 4-16.  
**Apply to:** session restoration, protected data, prediction pages, and configuration.

Keep HTTP URL construction and non-OK handling in the API client, and use query keys that include the patient/resource identity. Invalidate or refetch authoritative queries after login/logout/configuration changes rather than maintaining parallel copies in components.

## No Analog Found

| File/Capability | Reason |
|---|---|
| JWT signing/verification, password hashing, bearer session extraction | No authentication provider, token code, or secret configuration exists. |
| Role/resource/assignment authorization policy | Phase 1 has no users, roles, permissions, or protected routes. |
| Frontend router, auth provider, login, route guard, and role navigation | The frontend is a single monitoring view with no router or session state. |
| Primary ML prediction adapter and model availability handling | Phase 1 contains only deterministic vitals generation; use its pure scenario/service split as the fallback analog. |

Planner should use the exact Phase 1 patterns above for boundaries and testing, then make explicit Phase 2 decisions for token storage/expiry, password hashing dependency, JWT secret configuration, router choice, and primary ML pipeline discovery.

## Metadata

**Analog search scope:** `backend/app/`, `backend/tests/`, `frontend/src/`, Phase 1 planning map and implementation artifacts.  
**Files scanned:** 27 implementation/test files plus 6 codebase-map documents.  
**Pattern extraction date:** 2026-08-24