# Codebase Concerns

**Analysis Date:** 2026-08-24

## Tech Debt

**Prototype authorization boundary is not implemented:**
- Issue: Both the read endpoint and the bounded mutation endpoint are callable without authentication or role checks. The application currently exposes the same patient view to every caller, while the v1 requirements require JWT sessions, exactly three roles, resource permissions, logout, and rejection of unauthenticated protected requests.
- Files: `backend/app/main.py`, `backend/app/contracts/vitals.py`, `.planning/REQUIREMENTS.md`
- Impact: This is the primary Phase 2 delivery risk. Any network exposure would allow anonymous patient-data reads and repeated state-changing requests; frontend navigation cannot mitigate this because authorization must be server-side.
- Fix approach: Add a centralized identity/session dependency and explicit authorization policies before expanding prediction, alert, or dispatch routes. Test unauthenticated, wrong-role, wrong-patient, and assignment-owner cases at the API boundary.

**Single-patient hard-coding limits extensibility:**
- Issue: Patient `P-1042`, bed `ICU-12`, and the only supported scenario are embedded in `backend/app/main.py` and `backend/app/vitals/service.py`; the scenario values and bounds are module constants in `backend/app/vitals/scenario.py`.
- Files: `backend/app/main.py`, `backend/app/vitals/service.py`, `backend/app/vitals/scenario.py`, `backend/app/seed/demo_data.py`
- Impact: New patients, beds, scenarios, or assignments require code changes and can accidentally bypass database relationships. This conflicts with the later multi-role/resource-scope workflow even though the v1 journey is intentionally single-patient.
- Fix approach: Keep the P-1042 fixture, but resolve patient, bed, and scenario ownership from persisted records and inject a scenario registry behind a bounded development adapter.

**Configuration is stored as unvalidated strings:**
- Issue: `Configuration.value` is a free-form string, and `refresh_configuration` parses only digits while always returning a hard-coded default interval of 10. Stored freshness values are not used by `resolve_freshness`, which also hard-codes 15 and 60 seconds.
- Files: `backend/app/persistence/models.py`, `backend/app/transport/configuration.py`, `backend/app/contracts/vitals.py`, `backend/app/seed/demo_data.py`
- Impact: Admin-editable research settings can become invalid or silently diverge from runtime behavior. The future threshold/configuration work can inherit the same split-brain behavior.
- Fix approach: Introduce typed configuration validation at write/read boundaries, use one server-owned configuration object for freshness and refresh behavior, and reject malformed values with an explicit error.

**Application construction performs database side effects:**
- Issue: Importing `backend.app.main` creates the module-level app, runs migrations, creates an engine, and commits demo seed data through `create_app`.
- Files: `backend/app/main.py`, `backend/app/persistence/database.py`, `README.md`
- Impact: Test collection and process startup depend on filesystem/database availability, startup latency includes migrations, and multiple workers can race on migration/seed initialization. It also makes deployment lifecycle and failure reporting less predictable.
- Fix approach: Move migration/seed commands to explicit setup or deployment steps and use an application lifespan hook for controlled initialization; keep tests using an explicit fixture setup.

## Known Bugs

**Automatic refresh can report success without advancing the current observation:**
- Symptoms: `ObservationService.advance` returns an existing row when the requested sequence already exists, and `main.py` computes the next sequence by reading the current maximum. Concurrent requests can select the same next sequence; one can fail on the unique constraint or both can return the same state rather than producing one ordered tick.
- Files: `backend/app/main.py`, `backend/app/vitals/service.py`, `backend/app/persistence/models.py`
- Trigger: Two clients or refresh loops POST automatic advancement for `P-1042` at the same time.
- Workaround: The frontend suppresses overlapping requests in one browser tab with `refreshInFlight`, but this does not protect multiple tabs, users, or processes.

**Frontend silently suppresses most refresh failures:**
- Symptoms: `MonitoringPage.refresh` only changes the control to manual for status 422; network errors, 401/403, 404, 5xx responses, and failed current reads are caught without an error state.
- Files: `frontend/src/monitoring/MonitoringPage.tsx`, `frontend/src/api/client.ts`
- Trigger: API outage, expired session after Phase 2, exhausted/invalid fixture, or a failed REST recovery request.
- Workaround: The displayed observation remains on screen, which can look current unless the previously returned freshness state is independently noticed.

## Security Considerations

**Unauthenticated state-changing endpoint:**
- Risk: `POST /api/v1/patients/{patient_id}/vitals/advance` mutates persistent observations without authentication, authorization, CSRF protection, rate limiting, or audit recording.
- Files: `backend/app/main.py`, `frontend/src/api/client.ts`
- Current mitigation: The operation is bounded to `P-1042`, accepts only ticks 0-4 or intervals 5/10/30, and is labeled synthetic. These controls limit damage but do not establish access control.
- Recommendations: Protect the route with the Phase 2 session and role policy, require an explicit development/admin capability for fixture advancement, add request throttling/idempotency, and record denied and successful mutations for the Phase 3 audit trail.

**CORS and transport defaults are development-only:**
- Risk: CORS allows two localhost origins and all headers, while the frontend defaults to plain HTTP on `127.0.0.1`. There is no visible production origin, TLS, security-header, or trusted-proxy configuration.
- Files: `backend/app/main.py`, `frontend/src/api/client.ts`, `README.md`
- Current mitigation: The README describes a local research prototype and the allowed origins are narrow localhost values.
- Recommendations: Make origins an environment/configuration setting, fail closed outside development, deploy behind TLS, and add secure cookie/token transport and standard security headers when identity is introduced.

**Synthetic labeling is contract-level, not a complete data-safety boundary:**
- Risk: The API exposes fictional identifiers and server-owned provenance, but no route-wide authorization or audit layer guarantees that future prediction, history, alert, or dispatch responses preserve provenance and non-clinical labeling.
- Files: `backend/app/contracts/metadata.py`, `backend/app/contracts/vitals.py`, `backend/app/safety/labels.py`, `.planning/REQUIREMENTS.md`
- Current mitigation: Pydantic literal types reject retrospective/live-bedside metadata in the current contracts, and UI tests verify the prototype banner.
- Recommendations: Make provenance/safety metadata mandatory in every user-facing clinical-looking contract, add tests for every future surface, and keep synthetic and retrospective stores/types separated.

## Performance Bottlenecks

**Latest-observation lookup lacks an explicit supporting index:**
- Problem: Current vitals selects all rows for a patient and orders by descending sequence on every read. The uniqueness constraint supports patient/sequence uniqueness but does not guarantee an equivalent descending lookup index across supported databases.
- Files: `backend/app/main.py`, `backend/app/persistence/models.py`, `backend/app/migrations/versions/0001_phase1_foundation.py`
- Cause: The schema is a minimal SQLite-first foundation and has no explicit index declaration for the read path.
- Improvement path: Add a migration-backed `(patient_id, sequence)` index if query plans show growth, and use a repository query shared by current-read and next-sequence logic.

**Startup work scales with every process and test app:**
- Problem: Each `create_app` call runs Alembic upgrade and a seed transaction, and the module-level app does so at import time.
- Files: `backend/app/main.py`, `backend/app/persistence/database.py`, `backend/tests/test_vitals_api.py`
- Cause: Initialization is coupled to app construction rather than a one-time deployment/bootstrap operation.
- Improvement path: Separate schema/fixture setup from serving, then use pooled engine lifecycle and explicit readiness checks for deployed environments.

## Fragile Areas

**ORM models and migration are maintained separately:**
- Files: `backend/app/persistence/models.py`, `backend/app/migrations/versions/0001_phase1_foundation.py`, `backend/tests/test_migrations.py`
- Why fragile: The ORM declares `Bed.patient_id`, `Admission.patient_id`, and `History.patient_id` without explicit `nullable=False`, while the migration makes those columns non-nullable. Future model edits can drift from the migration because there is no model-metadata comparison test; migration tests only verify an empty database and foreign keys.
- Safe modification: Treat Alembic migrations as the schema authority, add a migration/model drift check, and test upgrade/downgrade plus representative constraints before changing models.
- Test coverage: No test covers downgrade, migration ordering beyond the current head, or schema parity.

**Seed and reset are destructive shared-fixture operations:**
- Files: `backend/app/seed/demo_data.py`, `backend/app/seed/reset.py`, `README.md`
- Why fragile: Reset deletes all modeled rows in dependency order and the application automatically reseeds the same database at startup. Running reset against a non-isolated database can destroy data, and concurrent startup/reset activity is not coordinated.
- Safe modification: Require an explicit development mode and database identity check, isolate demo databases per environment, and make reset a command with an explicit confirmation mechanism.
- Test coverage: Tests cover the intended fixture graph but not concurrent reset/startup, rollback on seed failure, or protection against a non-demo database.

**Frontend state is split between React Query and local state:**
- Files: `frontend/src/App.tsx`, `frontend/src/monitoring/MonitoringPage.tsx`
- Why fragile: `App` owns the initial query, while `MonitoringPage` copies the observation into local state and performs independent fetches. React Query cache invalidation, retry/error states, and post-mutation consistency are not used.
- Safe modification: Choose one server-state owner, model loading/error/disconnected states explicitly, and invalidate or update the current-vitals query after a successful advance.
- Test coverage: The monitoring tests cover successful fetch ordering and timer cleanup, but not initial query failure, malformed payloads, or stale local state after prop changes plus in-flight requests.

## Scaling Limits

**SQLite-first single-file persistence:**
- Current capacity: The fixture contains one patient, one bed, one nurse, three configuration rows, and at most five synthetic observations.
- Limit: `backend/app/main.py` and the README default to `sqlite:///acuitynet.db`; SQLite file locking and the current max-sequence write pattern are unsuitable for concurrent multi-user alert/audit workloads.
- Scaling path: Keep SQLite for deterministic local demos, but define a supported server database path before multi-user phases, add indexes and transaction/concurrency tests, and avoid embedding production assumptions in the seed path.

## Dependencies at Risk

**Runtime dependency baseline is unusually forward-looking:**
- Risk: The backend requires Python `>=3.13`, while frontend dependencies use broad caret ranges and the repository does not show a lockfile in the checked-in structure.
- Impact: Fresh installs can resolve different frontend versions, and environments limited to Python 3.12 cannot run the backend. Reproducibility is weaker than the pinned backend package list suggests.
- Migration plan: Pin and commit the frontend lockfile, document supported Node/npm versions, and verify the Python version requirement against CI/deployment images.

## Missing Critical Features

**Identity, authorization, audit, prediction, alert, and dispatch layers are absent:**
- Problem: The current implementation covers the Phase 1 monitoring fixture only. The active Phase 2 and later requirements still need authentication, role/resource policy, prediction fallback, alert lifecycle, audit evidence, history, dispatch, and nurse assignment workflows.
- Blocks: The core value journey cannot be safely followed beyond synthetic vitals, and the current public monitoring surface cannot serve as an authorized clinical workflow.
- Files: `backend/app/main.py`, `frontend/src/App.tsx`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`

## Test Coverage Gaps

**Authorization and adversarial API behavior:**
- What's not tested: Authentication, role boundaries, assignment ownership, denied access audit events, malformed authorization claims, rate limiting, concurrent advance requests, and cross-patient access.
- Files: `backend/tests/test_vitals_api.py`, `backend/tests/test_safety_boundary.py`
- Risk: Security regressions can pass while happy-path API tests remain green.
- Priority: High

**Failure recovery and operational state:**
- What's not tested: Fetch rejection, timeout, malformed JSON, 401/403/5xx responses, retry/reconnect behavior, browser reload after a mutation, or REST recovery after a future WebSocket disconnect.
- Files: `frontend/src/monitoring/MonitoringPage.test.tsx`, `frontend/src/api/client.ts`, `.planning/REQUIREMENTS.md`
- Risk: Operators may see stale data without a sufficiently prominent or accurate failure state.
- Priority: High

**Database concurrency and lifecycle:**
- What's not tested: Parallel advancement, duplicate sequence races, migration downgrade, seed rollback, startup failure, and reset protection.
- Files: `backend/app/persistence/database.py`, `backend/app/seed/reset.py`, `backend/tests/test_migrations.py`, `backend/tests/test_scenario.py`
- Risk: The deterministic single-client demo can conceal production-like transaction and initialization failures.
- Priority: Medium

---

*Concerns audit: 2026-08-24*