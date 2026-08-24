# Phase 3: Monitoring, Alerts, Lifecycle, and Audit - Pattern Map

**Mapped:** 2026-08-24  
**Files analyzed:** 22 inferred new/modified files  
**Analogs found:** 18 / 22

Phase 3 has no `CONTEXT.md` or `RESEARCH.md` in the repository. The inventory below is inferred from the Phase 3 roadmap success criteria, ALRT-01 through ALRT-05, AUDT-01, REAL-01, REAL-02, the Phase 2 summaries, and the current implementation. Keep the existing modular-monolith boundaries: SQLAlchemy/Alembic own persistence, domain modules own alert and lifecycle behavior, FastAPI owns transport/dependencies, and REST remains authoritative while realtime delivery is additive.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/app/persistence/models.py` | model | CRUD/event persistence | same file | exact |
| `backend/app/migrations/versions/0003_alerts_lifecycle_audit.py` | migration | transform/CRUD | `0002_identity_authorization.py` | exact |
| `backend/app/alerts/service.py` | service | request-response/CRUD | `prediction/adapter.py`, `vitals/service.py` | role-match |
| `backend/app/alerts/repository.py` | repository | CRUD | `admin/repository.py` | exact |
| `backend/app/alerts/lifecycle.py` | policy/service | event-driven state transition | `auth/policy.py` | role-match |
| `backend/app/audit/service.py` | service | event-driven append-only | `admin/repository.py` | partial |
| `backend/app/audit/repository.py` | repository | append/read ordered events | `admin/repository.py` | role-match |
| `backend/app/transport/alerts.py` | route/controller | request-response | `transport/predictions.py` | role-match |
| `backend/app/transport/audit.py` | route/controller | request-response | `transport/admin.py` | role-match |
| `backend/app/transport/realtime.py` | route/controller | streaming/event-driven | no analog | none |
| `backend/app/contracts/alerts.py` | contract | request-response | `contracts/predictions.py` | role-match |
| `backend/app/contracts/audit.py` | contract | request-response | `contracts/admin.py` | role-match |
| `frontend/src/contracts/alerts.ts` | contract | request-response/event-driven | `contracts/predictions.ts` | role-match |
| `frontend/src/api/client.ts` | utility | request-response | same file | exact |
| `frontend/src/alerts/AlertPage.tsx` | component | request-response | `prediction/PredictionPage.tsx`, `monitoring/MonitoringPage.tsx` | role-match |
| `frontend/src/alerts/useAlertRealtime.ts` | hook | streaming/recovery | no analog; `MonitoringPage.tsx` timer effect | partial |
| `frontend/src/operational/OperationalState.tsx` | component | transform/presentation | `MonitoringPage.tsx` state map | role-match |
| `backend/tests/test_alerts.py` | test | CRUD/request-response | `test_vitals_api.py` | role-match |
| `backend/tests/test_lifecycle_audit.py` | test | event-driven/CRUD | `test_auth.py`, `test_migrations.py` | role-match |
| `frontend/src/alerts/AlertPage.test.tsx` | test | request-response/event-driven | `MonitoringPage.test.tsx` | role-match |
| `scripts/phase3_smoke.py` | test/smoke | request-response/recovery | `scripts/phase2_smoke.py` | role-match |

## Pattern Assignments

### SQLAlchemy models and migration

**Analog:** `backend/app/persistence/models.py` lines 1-84; `backend/app/migrations/versions/0002_identity_authorization.py` lines 1-29.

Add alert, lifecycle, and audit tables to `models.py` using SQLAlchemy 2 typed mappings: `Mapped[...]`, `mapped_column`, explicit `String` lengths, `nullable=False`, foreign keys, and named uniqueness constraints. Keep stable string identifiers for the seeded prototype and integer IDs only where an append-only event stream benefits from ordering. Model alert identity separately from lifecycle events so the current alert row is cheap to read while ordered transitions remain immutable. Include actor/user foreign keys for authenticated actions, and preserve alert/patient relationships.

Author `0003_alerts_lifecycle_audit.py` as an explicit Alembic revision after `0002_identity_authorization`; do not use `create_all()` or seed code for schema changes. `0002` demonstrates `upgrade()` creating a table and adding a foreign key, then `downgrade()` dropping constraints/columns in reverse order (lines 10-29). Ensure downgrade ordering removes audit/event children before alert parents and preserves SQLite-compatible foreign-key behavior from `database.py` lines 8-17.

Use migration-backed constraints for valid state values where portable, and enforce transition legality in the lifecycle service/policy. Add indexes for the authoritative reads: active alert by patient/status, lifecycle events by alert and sequence/time, and audit events by timestamp/id. The existing `VitalObservation` uniqueness pattern (`models.py` lines 63-84) is the closest precedent for deduplicating a deterioration episode; make the episode key/cooldown semantics explicit rather than relying on an application-only check.

### Alert repository and deterministic alert generation

**Analogs:** `backend/app/admin/repository.py` lines 1-15; `backend/app/prediction/adapter.py` lines 1-16; `backend/app/prediction/fallback.py` lines 1-7; `backend/app/vitals/service.py` lines 1-48.

Keep repositories session-bound and small, with callers owning transaction scope. `admin/repository.py` uses `Session`, `select`, `session.get`, ordered list reads, mutation plus `flush()`, and no hidden session creation. Follow that shape for `get_active_alert`, `list_alert_events`, `create_alert`, and append operations.

Alert generation should consume the authoritative latest observation and the Phase 2 prediction adapter/configuration, not recompute risk in a route or in React. `PredictionAdapter.predict()` accepts the observation and typed vitals and applies the configured critical threshold before falling back to `deterministic_prediction()` (`prediction/adapter.py` lines 4-16). Preserve the prediction payload’s risk, event, probability, horizon, current vitals, provenance, prototype label, source kind/version, and fallback reason in the alert evidence. A fallback prediction is still usable, but the alert must carry its explicit `deterministic_fallback` source and safety metadata.

Make generation deterministic for P-1042: same observation/prediction/episode key yields the existing active alert or a clearly recorded cooldown decision. The existing idempotent observation lookup in `vitals/service.py` and unique `(patient_id, sequence)` constraint are useful mechanics, but alert deduplication needs a domain key such as patient + episode or prediction observation sequence plus an active-state query. Return a result that distinguishes `created`, `existing`, and `suppressed/cooldown` so ALRT-02 is observable.

### Lifecycle transition policy and routes

**Analogs:** `backend/app/auth/policy.py` lines 1-39; `backend/app/transport/predictions.py` lines 1-25; `backend/app/main.py` lines 105-143.

Keep transition validation in `alerts/lifecycle.py`, not in route handlers. The auth policy module demonstrates small explicit predicates that raise `HTTPException(403)` for forbidden role/resource/assignment access. Adapt the same clarity to a domain transition map: generated -> dispatched/assigned -> acknowledged -> responded -> resolved, reject skips/backward transitions, and require assignment scope for Nurse mutations. Return a domain error that transport translates to a stable 409 or 422 response.

Alert routes should follow `prediction_router()`: construct an `APIRouter`, inject `sessions`, `current_user`, and the alert service, apply `Depends(current_user)`, authorize the patient before querying, open a short-lived session, and return a typed contract (`transport/predictions.py` lines 8-25). GET current alert and ordered events should be available only to Admin and authorized clinical users. Lifecycle mutation routes must require authenticated actor identity, role policy, and nurse assignment checks before changing state.

For request transactions copy `main.py` lines 105-128: use `with sessions.begin() as session`, resolve the authoritative row, call the domain service, append the lifecycle/audit event in the same transaction, and return the resulting read model. Translate known `ValueError`/domain failures with `raise HTTPException(...) from error`, as in `main.py` lines 129-143. Do not let a WebSocket message perform a mutation; realtime is notification/invalidation only.

### Audit persistence and ordered evidence

**Closest analogs:** `backend/app/admin/repository.py` lines 1-15; `backend/app/transport/admin.py` lines 1-38; `backend/app/auth/service.py` lines 6-22.

There is no existing audit/event persistence implementation. Add an append-only audit repository/service modeled on the session-bound admin repository: accept the active `Session`, actor/user ID when authenticated, action/event type, resource type/id, resulting state, timestamp, and structured outcome/evidence. Flush within the caller’s transaction and never update or delete audit rows during ordinary lifecycle operations.

The audit contract should be explicit and bounded like `PredictionResponse` (`contracts/predictions.py` lines 5-20) and admin DTOs (`contracts/admin.py` lines 4-22): forbid extra fields for requests, use literals for known action/state categories, keep nullable actor only for system-generated events, and serialize ordered events with stable timestamps and IDs. Denied access must be recorded without leaking sensitive detail; because authorization failures can happen before a resource is loaded, the audit writer may need a separate short transaction or request-level hook, but it must not turn an authorization failure into a successful mutation.

The audit route should mirror the Admin transport’s Admin dependency (`transport/admin.py` lines 8-38), broaden access only to the roles required by ALRT-05, and apply resource scoping before returning events. Return ascending event order explicitly, with a deterministic tie-breaker (`event_id` after timestamp). Include configuration changes, alert creation/deduplication, lifecycle actions, assignment/dispatch actions when later phases call them, and denied access outcomes.

### Pydantic contracts and safety metadata

**Analogs:** `backend/app/contracts/predictions.py` lines 1-20; `backend/app/contracts/vitals.py` lines 1-75; `backend/app/contracts/configuration.py` lines 1-23.

Keep alert and audit wire DTOs separate from ORM models. Use `ConfigDict(extra="forbid")`, `Literal`/enums for lifecycle states, alert priority, source kinds, operational states, and bounded action names. Use `Field` constraints for probabilities, scores, horizons, identifiers, and note lengths. Model transition requests narrowly: action plus relevant outcome/note/assignment fields, rather than accepting arbitrary event payloads.

An alert response should contain patient, bed, priority, risk score/level, event, probability, horizon, current observation reference, provenance, prototype label, prediction source/version/fallback reason, deduplication outcome, current lifecycle state, and ordered evidence. Reuse `SyntheticProvenance` and `VitalObservationResponse` rather than creating a second safety vocabulary. `PredictionResponse` already shows how source and fallback metadata travel with the result (`contracts/predictions.py` lines 8-20).

The server owns freshness and operational state. Extend the existing `FreshnessState` values (`contracts/vitals.py` lines 8-14) or define a separate alert transport state only if alert loading/disconnect/fallback/no-candidate semantics cannot be represented without conflation. Do not let the frontend infer an alert from a numeric score or browser time.

### Deterministic prediction/configuration integration

**Analogs:** `backend/app/prediction/adapter.py` lines 1-16; `backend/app/prediction/fallback.py` lines 1-7; `backend/app/admin/configuration.py` lines 1-15; `backend/app/transport/configuration.py` lines 1-17.

Use the same injected adapter/service seam in alert generation. Obtain effective settings through the configuration module rather than reading raw `Configuration.value` in the alert route. `effective_settings()` merges stored values with allowlisted defaults and `update_typed_configuration()` restricts keys (`admin/configuration.py` lines 1-15); Phase 3 should preserve that allowlist and add alert deduplication/cooldown settings as typed fields, not arbitrary key/value writes.

The current `refresh_configuration()` transport helper reads one configuration row and parses its bounded interval values (`transport/configuration.py` lines 1-17). Treat this as a compatibility pattern, but do not copy its hard-coded `default_interval` or digit-only parser into alert policy. Centralize threshold, episode identity, cooldown duration, and operational timeout values in one effective settings object so prediction and alert generation cannot disagree.

### Realtime wiring and REST recovery

**Analog:** `frontend/src/monitoring/MonitoringPage.tsx` lines 25-68 for effect/timer cleanup and authoritative REST reread. **No WebSocket analog exists.**

Search found no WebSocket, `EventSource`, backend publish/subscribe, or realtime client wiring in the repository. Implement the smallest additive channel: a FastAPI WebSocket endpoint or server-side notification hub may emit alert/vital invalidation envelopes, but all reads and lifecycle mutations remain REST endpoints. Authenticate the WebSocket handshake, scope subscriptions to the authorized patient/alert, and close unauthorized or malformed connections. Never use the socket as the durable source of alert state.

On the frontend, a `useAlertRealtime` hook may subscribe, mark the alert query stale on a valid invalidation message, and immediately refetch current alert/audit through `api/client.ts`. Copy `MonitoringPage`’s `useEffect` cleanup and in-flight guard (`MonitoringPage.tsx` lines 31-68), adding explicit `connecting`, `connected`, `disconnected`, and `error` state. Reconnect with bounded backoff and stop on unmount or logout. Page reload must simply begin with REST queries and recover without a socket.

### Frontend server-state and operational state

**Analogs:** `frontend/src/main.tsx` lines 1-13; `frontend/src/App.tsx` lines 1-18; `frontend/src/prediction/PredictionPage.tsx` lines 1-4; `frontend/src/monitoring/MonitoringPage.tsx` lines 8-22, 69-132; `frontend/src/api/client.ts` lines 1-55.

Keep the module-level TanStack Query provider (`main.tsx` lines 5-12) and use stable query keys including patient/alert identity. `App.tsx` owns the initial current-vitals query with `retry: false` and explicit loading behavior (lines 10-18); alert views should use the same server-state owner and expose loading/error/empty states instead of copying server state into multiple components.

The current MonitoringPage copies the observation into local state, fetches configuration independently, and suppresses most errors (`MonitoringPage.tsx` lines 25-68). For Phase 3, prefer query data for current alert and audit evidence, reserving local state for transient mutation/reconnect state. After a successful lifecycle mutation, invalidate/refetch the alert and audit queries. Preserve the API client’s centralized base URL, bearer headers, 401 token clearing, and non-2xx `Error` behavior (`api/client.ts` lines 3-55).

Represent operational state visibly and separately from clinical-looking alert content: loading, stale, disconnected, unavailable fallback, and no active candidate/alert. The existing `stateCopy` map in `MonitoringPage.tsx` lines 8-14 and `freshnessOverride` handling lines 69-71 are the nearest presentation pattern. Alert pages should not leave the last successful alert looking current after a failed refresh; retain the last data only with a prominent server-reported stale/disconnected state and a retry path.

### Backend test conventions

**Analogs:** `backend/tests/test_auth.py` lines 1-32; `backend/tests/test_migrations.py` lines 1-67; `backend/tests/test_vitals_api.py`; `backend/tests/test_phase2_integration.py` lines 1-5.

Use isolated temporary SQLite URLs, `monkeypatch.setenv("ACUITYNET_JWT_SECRET", ...)`, `create_app(database_url, clock=...)`, real Alembic migrations, real seed data, and `TestClient`. Assert HTTP status, response contracts, persisted event order/counts, actor IDs, and rejected transitions. Keep prediction fallback and alert deduplication deterministic by injecting a fixed clock and using exact P-1042 ticks.

Add focused cases for threshold crossing, alert evidence/provenance, repeated same-episode generation, cooldown outcome, every valid lifecycle edge, invalid/backward transitions, wrong role, unassigned nurse, missing/expired token, and atomicity when audit append fails. Migration tests should verify upgrade schema, foreign keys, uniqueness/index constraints, and downgrade ordering. Do not mock SQLAlchemy or FastAPI authorization in integration tests; a small pure lifecycle-policy test is appropriate for the transition matrix.

### Frontend test conventions

**Analog:** `frontend/src/monitoring/MonitoringPage.test.tsx` lines 1-155.

Keep tests colocated with alert components. Use Vitest `describe`/`it`, Testing Library semantic queries, `vi.stubGlobal("fetch", ...)`, fake timers for reconnect/backoff, and cleanup in `afterEach`. Assert visible priority, risk/source/provenance/fallback metadata, lifecycle action availability, disabled/forbidden states, ordered audit entries, no-active-alert state, and operational status after rejected fetch, 401/403, timeout, malformed payload, socket close, and successful REST recovery.

Mock only the browser network boundary. Keep backend lifecycle, persistence, migrations, and authorization real in backend tests. Reuse the existing local `VitalObservation` fixture shape and response helper pattern (`MonitoringPage.test.tsx` lines 8-34, 37-43); add alert fixtures with complete typed safety and lifecycle fields so tests cannot accidentally omit provenance or source metadata.

### Smoke/reproducibility

**Analog:** `scripts/phase2_smoke.py` and its summary in `02-08-SUMMARY.md`.

Extend the secret-safe child-process smoke style for the Phase 3 journey: preflight `ACUITYNET_JWT_SECRET`, start Uvicorn with a temporary SQLite database, login as seeded users, advance deterministic P-1042 ticks, fetch prediction/current alert, assert one deduplicated alert, execute authorized lifecycle transitions, fetch ordered audit evidence, and exercise REST recovery after a simulated/disconnected realtime path. Never print passwords, tokens, or secret values. Keep setup/reset separate from migrations and report failure without claiming clinical behavior.

## Shared Patterns

### Session and transaction ownership

**Source:** `backend/app/main.py` lines 25-32, 105-143; `backend/app/persistence/database.py` lines 8-25.  
**Apply to:** alert repositories/services, lifecycle routes, audit append/read, tests.

Inject `sessions`, open a short-lived session per operation, use `sessions.begin()` for state-changing requests, flush repository writes, and commit alert state plus lifecycle/audit event atomically. Do not hold a SQLAlchemy session across a WebSocket lifetime.

### Authorization before resource access

**Source:** `backend/app/auth/policy.py` lines 6-39; `backend/app/transport/predictions.py` lines 10-25.  
**Apply to:** alert reads, lifecycle mutations, audit reads, realtime subscriptions.

Resolve the current user from the bearer dependency, apply role/patient/assignment policy before returning or mutating data, and use 401 for invalid identity versus 403 for valid but unauthorized access. Record denied access outcomes in the audit design without weakening the rejection.

### Safety and source metadata

**Source:** `backend/app/contracts/vitals.py` lines 18-61; `backend/app/contracts/predictions.py` lines 5-20; `backend/app/safety/labels.py`; `frontend/src/safety/PrototypeBanner.tsx`.  
**Apply to:** alert contracts, alert UI, audit evidence, realtime envelopes.

Carry server-provided synthetic provenance, prototype label, prediction source/version, and fallback reason through every alert-facing response. Do not describe generated alerts as clinical diagnoses or validated risk.

### REST/cache authority

**Source:** `frontend/src/main.tsx` lines 5-12; `frontend/src/App.tsx` lines 10-18; `frontend/src/api/client.ts` lines 22-55.  
**Apply to:** alert query, lifecycle mutations, audit query, socket invalidation.

Use TanStack Query for durable server state, invalidate after mutations or socket notifications, and use REST on initial load/reload/reconnect. Keep bearer/error handling in the API client rather than in feature components.

## No Analog Found

| Capability | Reason | Planner Guidance |
|---|---|---|
| WebSocket/server realtime hub and reconnect protocol | No WebSocket, EventSource, broker, or publish/subscribe code exists | Define an authenticated additive invalidation channel; REST remains authoritative and must recover after close/reload. |
| Alert ORM/repository/service | No alert table or domain service exists | Combine typed SQLAlchemy/session patterns with deterministic prediction adapter and explicit deduplication result. |
| Lifecycle event persistence | No state machine or event table exists | Use a transition map/policy plus append-only ordered event rows in the same transaction as alert state. |
| Audit event persistence | No audit logger or audit table exists | Create a separate append-only repository/service; cover authenticated actions and denied outcomes without leaking details. |

## Metadata

**Analog search scope:** `backend/app/`, `backend/tests/`, `frontend/src/`, `scripts/`, `.planning/codebase/`, and Phase 2 summaries/patterns.  
**Files scanned:** 25 implementation/test files, 7 codebase-map/planning documents, and 8 Phase 2 summaries.  
**Pattern extraction date:** 2026-08-24
