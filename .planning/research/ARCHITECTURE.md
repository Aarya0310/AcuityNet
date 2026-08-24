# Architecture Patterns

**Domain:** ICU predictive triage and nurse dispatch research prototype
**Project:** AcuityNet
**Researched:** 2026-08-24
**Confidence:** HIGH for the modular-monolith and persistence boundaries; MEDIUM for the prototype's future scale assumptions

## Recommended Architecture

Build AcuityNet as a modular monolith with one FastAPI process, one React application, and SQLAlchemy behind a database port. Keep domain capabilities as modules in the backend rather than separate services. The central workflow is an application service that composes the modules in a deterministic order:

```text
React dashboard
   | REST: initial state, commands, history
   | WebSocket: patient-scoped live updates
   v
FastAPI transport + auth dependencies
   v
Patient journey application service
   |-- vitals simulator -> vital observations
   |-- prediction adapter -> baseline prediction
   |-- historian rules -> contextual explanation and adjusted research score
   |-- alert policy -> alert creation / deduplication
   |-- dispatcher -> ranked nurse recommendation
   |-- audit writer -> append-only lifecycle entries
   v
SQLAlchemy repositories -> SQLite (PostgreSQL-compatible schema)
```

The backend owns workflow state. The frontend owns presentation state only: selected patient, filters, connection status, optimistic loading state, and the last server payload. A WebSocket message is a notification or snapshot, not the source of truth. This keeps refreshes, reconnects, and role changes predictable.

### Component Boundaries

| Component | Responsibility | Communicates With |
|---|---|---|
| `transport` | REST/WebSocket routes, request validation, response DTOs, HTTP error mapping | auth, application services |
| `auth` | Password verification, JWT encode/decode, current-user dependency, role and ownership checks | transport, users repository |
| `patients` | Patient, admission, bed, context, and clinical-note read/write rules | repositories, audit |
| `vitals` | Synthetic stream generation and observation persistence; never represents a device feed | prediction, realtime publisher |
| `prediction` | Stable prediction port and adapters for the available model or deterministic fallback | vitals, historian, alerts |
| `historian` | Configurable research rules over persisted patient context; returns reasoned adjustments | patients, configuration |
| `alerts` | Threshold evaluation, idempotent alert creation, lifecycle transition validation | prediction, dispatcher, audit |
| `dispatch` | Candidate filtering and transparent weighted ranking: availability 40%, proximity 30%, workload 20%, acuity compatibility 10% | nurses, beds, alerts, audit |
| `audit` | Append-only records for state transitions and important actions | every mutating application service |
| `realtime` | In-process connection registry and post-commit event fan-out; no business decisions | WebSocket routes, application services |
| `persistence` | SQLAlchemy models, session factory, repositories, migrations/seeding boundary | all backend modules |
| `configuration` | Risk thresholds, refresh interval, research-rule settings, and versioned configuration reads | historian, alerts, vitals, admin routes |

Application services may call domain modules and repositories. Domain modules must not import FastAPI request objects, React concepts, or WebSocket connections. Repositories accept a session supplied by the application boundary; they do not create or commit their own sessions.

## Central Patient Journey

For P-1042, implement one explicit orchestration path before generalizing dashboards:

1. The simulator emits a timestamped synthetic observation with patient ID, source label, values, and sequence ID.
2. The journey service validates the observation, persists it, and invokes the prediction adapter with a typed feature payload.
3. The adapter returns a stable payload containing risk score, level, predicted event, probability, horizon, model/fallback label, feature timestamp, and current vitals.
4. The historian loads patient context and configured rules, then returns adjustments plus human-readable rule explanations. It does not silently mutate the baseline prediction.
5. The alert policy compares the effective research score with the configured threshold. It creates one active alert for the same patient/prediction condition, or records a non-creation decision when an equivalent active alert exists.
6. If an alert is created, dispatch filters nurses first, scores the remaining candidates, and stores the recommendation with score components and the configuration version used.
7. The service commits the observation, prediction, explanation, alert, recommendation, and corresponding audit entries as one logical write operation where possible.
8. Only after commit, it publishes a patient-scoped update containing IDs and display DTOs. Connected clients refetch or apply the snapshot.
9. Nurse commands transition the alert through `generated -> acknowledged -> responding -> resolved` using one endpoint per allowed transition. Each transition validates actor permissions, expected current state, and idempotency, then persists an audit entry and publishes an update.

The simulator should call the same application service as a manual "simulate deterioration" command. That gives the demo one code path and makes the journey testable without depending on a running browser or timer.

## Data Flow and Persistence Contracts

Use normalized tables with stable external identifiers such as `P-1042`, while keeping internal integer or UUID primary keys free to change. The minimum aggregate relationships are:

```text
User -> Role
Patient -> Admission -> Bed
Patient -> VitalObservation[]
Patient -> Prediction[] -> ResearchExplanation[]
Patient -> Alert[] -> AlertLifecycleEvent[]
Alert -> DispatchRecommendation -> Nurse
Any important action -> AuditEvent
Configuration -> (thresholds, refresh settings, historian rules, dispatch weights)
```

Persist these contracts:

- **VitalObservation:** patient ID, observed-at timestamp, sequence ID, synthetic source, typed vital values, and optional simulator scenario. Do not overwrite observations.
- **Prediction:** patient ID, observation ID, generated-at timestamp, score, level, event, probability, horizon, adapter name/version, and fallback flag. Store the input observation reference so a result can be reproduced.
- **ResearchExplanation:** prediction ID, rule ID/version, context facts used, signed adjustment, resulting effective score, and prototype disclaimer. Keep baseline and adjusted values separate.
- **Alert:** patient ID, prediction ID, severity, threshold/configuration version, current state, created/updated timestamps, and assigned nurse when applicable. Enforce a uniqueness rule for the active equivalent condition or perform an explicit active-alert lookup in the transaction.
- **AlertLifecycleEvent:** alert ID, from-state, to-state, actor/user ID or system actor, timestamp, reason, and request/idempotency key. This is the authoritative ordered lifecycle; current alert state is a convenient projection.
- **DispatchRecommendation:** alert ID, recommended nurse, ranked candidates or compact score breakdown, weight/configuration version, generated-at timestamp, and acceptance/rejection status. A recommendation is explainable research output, not an assignment unless explicitly accepted.
- **AuditEvent:** actor, action, entity type/ID, timestamp, request ID, role, and structured metadata. Treat it as append-only; corrections are new events.

Keep one SQLAlchemy session per REST request or simulator task, and one session per WebSocket-triggered command. Use an explicit `begin`/commit/rollback boundary around mutations and close the session promptly. Never hold a database session open for the lifetime of a WebSocket connection, and never share a session across concurrent simulator tasks. These boundaries follow SQLAlchemy's current session guidance.

The initial SQLite setup should use migrations or an equivalent repeatable schema process, seeded demonstration users, P-1042, nurses, beds, context, and configuration. Keep database URLs and dialect-sensitive behavior behind persistence configuration so PostgreSQL is a later deployment change, not a domain rewrite.

## API and Realtime Contract

Expose DTOs rather than ORM objects. Suggested initial endpoints:

```text
POST   /auth/login
GET    /me
GET    /patients/{patient_id}/overview
GET    /patients/{patient_id}/vitals
GET    /patients/{patient_id}/predictions
GET    /patients/{patient_id}/alerts
POST   /patients/{patient_id}/simulate-observation
POST   /alerts/{alert_id}/acknowledge
POST   /alerts/{alert_id}/respond
POST   /alerts/{alert_id}/resolve
GET    /alerts/{alert_id}/lifecycle
WS     /ws/patients/{patient_id}
```

Use one versioned response shape for predictions and alerts so the fallback adapter and a future model are interchangeable. WebSocket messages should include `type`, `patient_id`, `entity_id`, `version` or event timestamp, and a compact payload. On connect, authorize the patient scope, send an initial snapshot, then send updates. On disconnect, remove the connection. The React hook must close the socket during cleanup and reconnect only when its patient or authenticated session changes.

Do not make the WebSocket the only delivery mechanism. REST must remain sufficient to recover after a missed message, and the UI should show stale/disconnected state rather than implying current monitoring when the connection is down.

## Security Boundaries

JWT validation is a backend dependency on every protected REST route and WebSocket handshake. The token identifies the user and role; route handlers then apply resource-level rules. Hiding navigation is not authorization.

| Role | Allowed boundary |
|---|---|
| Admin | Manage users, nurses, beds, configuration, and audit logs; read operational data |
| Doctor | Read patient context, history, predictions, explanations, alerts, and notes within the prototype scope; no user/configuration administration |
| Nurse | Read assigned patients and assigned alerts; transition only alerts assigned to that nurse |

Centralize role checks and nurse assignment checks in dependencies or application policies. Validate that patient and alert IDs belong to the requested resource before returning data. Do not put clinical context, permissions, or secrets in JWT claims beyond the minimum identity and role data. Hash seeded account passwords, keep signing configuration outside source control, and never log raw tokens.

Every denied mutation should be observable in application logs without exposing sensitive payloads; every accepted state transition should create an audit event. Label all synthetic observations, model fallback results, research-rule adjustments, and UI surfaces as simulated/non-clinical.

## Patterns to Follow

### Application service as the workflow boundary

The service owns ordering and transaction scope. Prediction, historian, and dispatch are small ports with pure or mostly pure functions, which makes them independently testable and prevents routes from becoming orchestration code.

### State machine for alert lifecycle

Represent allowed transitions explicitly. Reject stale commands such as resolving an already resolved alert with a conflict or idempotent success according to a documented rule. Never infer history from the current state alone.

### Post-commit notification

Persist first, publish second. If publication fails, the next REST refresh or reconnect recovers the UI. For this single-process prototype, an in-memory publisher is sufficient; introducing a broker before there is a multi-process requirement would add failure modes without improving the demo.

## Anti-Patterns to Avoid

### Feature routes that own business rules

Duplicating threshold checks or transition logic in multiple endpoints will make the demo paths disagree. Put rules in application/domain services and let routes translate transport concerns.

### Long-lived simulator or WebSocket database sessions

This causes stale ORM state, locked SQLite transactions, and unsafe concurrent session use. Create a short-lived task session per tick/command and publish DTOs after commit.

### Treating model output as clinical truth

Keep adapter provenance, fallback status, research-rule explanation, threshold configuration, and prototype labels in the payload and persistence model. Do not present the result as a diagnosis or validated recommendation.

### Premature event-driven infrastructure

An in-process post-commit publisher and one worker loop meet the synthetic 5-10 second requirement. Add a queue, broker, or separate prediction service only when deployment topology or measured load requires it.

## Suggested Build Order

1. **Backend foundation:** settings, SQLite engine/session factory, schema/migrations, seed data, typed DTO conventions, and health endpoint.
2. **Identity and policy:** seeded JWT login, current-user dependency, three roles, resource/assignment checks, and authorization tests.
3. **Patient read model:** patient/admission/bed/context/nurse endpoints and the P-1042 overview.
4. **Synthetic observation path:** simulator plus manual trigger, vital persistence, and a patient-scoped WebSocket snapshot/update contract.
5. **Prediction adapter:** stable response schema, deterministic fallback, and prediction persistence linked to observations.
6. **Historian and alert state machine:** configurable rules, separate baseline/effective scores, threshold evaluation, deduplication, lifecycle events, and audit entries.
7. **Dispatcher:** candidate filtering, weighted ranking, explainable score breakdown, and recommendation persistence.
8. **Role workflows:** nurse acknowledge/respond/resolve commands, doctor read views, admin controls, and audit viewer.
9. **Journey verification:** an automated integration test and a seeded demo script that drives P-1042 from deterioration through resolution, including reconnect/reload recovery.

This order makes the first usable vertical slice possible after step 6, then adds dispatch and role-specific polish without changing the core contracts. Defer MIMIC ingestion, model training, global optimization, multi-hospital tenancy, background queues, and PostgreSQL deployment until the journey is reliable and its audit trail is demonstrable.

## Scalability Considerations

| Concern | Prototype approach | Later trigger for change |
|---|---|---|
| Live updates | In-process connection registry and patient-scoped WebSockets | Multiple API workers or unreliable cross-process delivery |
| Synthetic generation | One bounded async loop with short DB sessions | Many scenarios or durable scheduled jobs |
| Database | SQLite with SQLAlchemy and migration discipline | Concurrent writes, multiple workers, or production deployment |
| Prediction | Adapter plus deterministic fallback in-process | Expensive models, independent scaling, or GPU scheduling |
| Audit | Append-only SQL table with indexes on entity/time | Retention, export, or compliance requirements |

## Sources

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - official endpoint, connection lifecycle, and disconnect handling guidance; HIGH confidence for transport patterns.
- [FastAPI OAuth2 with JWT tokens](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) - official authentication dependency pattern; HIGH confidence for JWT boundary.
- [SQLAlchemy 2.0 Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) - official transaction, close, and per-thread/task session guidance; HIGH confidence.
- [React `useEffect`](https://react.dev/reference/react/useEffect) - official external-system subscription setup/cleanup guidance; HIGH confidence.
- AcuityNet project brief: [PROJECT.md](../PROJECT.md) - product constraints, roles, workflow, and out-of-scope decisions; HIGH confidence for project-specific requirements.