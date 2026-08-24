# Technology Stack

**Project:** AcuityNet
**Scope:** Stack research for an ICU predictive triage and nurse dispatch research prototype
**Researched:** 2026-08-24
**Overall confidence:** MEDIUM

## Recommendation

Build AcuityNet as a small modular monolith: a Vite-powered React and TypeScript single-page application, a FastAPI Python API, and SQLAlchemy 2.0 with Alembic over a SQLite file. Keep the domain logic in backend services and adapters, not in route handlers or React components. This honors the PRD while leaving a clean path to PostgreSQL and a separately deployed worker if the prototype grows.

Use current stable patch releases, pinned in lockfiles, rather than copying a stale version number into this document. The current official documentation confirms SQLAlchemy 2.0.52 and Alembic 1.19.2 release lines; React and FastAPI should be pinned to the stable releases selected during project initialization and upgraded deliberately. Treat all version claims below as MEDIUM confidence because they were checked against official documentation and current provider output, but not against a final generated lockfile.

## Recommended Stack

### Core Framework

| Technology | Version target | Purpose | Why |
|------------|----------------|---------|-----|
| Python | 3.12.x | Backend runtime | Mature async support and compatibility with the current FastAPI ecosystem; also supports SQLAlchemy's documented modern SQLite transaction controls. |
| FastAPI | Latest stable release at initialization, exact pin | REST API, OpenAPI schema, WebSockets | Matches the supplied architecture and provides typed request validation, dependency injection, and WebSocket support without adding a second backend framework. |
| React | 19.x stable, exact pin | Browser UI | Required by the PRD and well suited to role-specific dashboards and live view updates. |
| TypeScript | Current stable 5.x line, exact pin | Frontend type safety | Keeps REST payloads, alert states, roles, and vital schemas explicit. |
| Vite | Current stable major at initialization, exact pin | Frontend dev server and build | Vite provides fast HMR and optimized static production builds; the official guide currently requires Node.js 20.19+ or 22.12+. |
| Node.js | 22 LTS preferred | Frontend tooling | Gives a stable supported runtime for the Vite toolchain while keeping local setup reproducible. |

### Database and Persistence

| Technology | Version target | Purpose | Why |
|------------|----------------|---------|-----|
| SQLAlchemy | 2.0.52 release line | ORM, SQL expression layer, database boundary | The 2.0-style `select()` API is the documented standard and its dialect abstraction preserves the SQLite-to-PostgreSQL path. |
| SQLite | System-supported current 3.x | First local database | Zero-service setup makes seeded accounts and the P-1042 demo reproducible on a developer machine. Use a file database, foreign keys enabled on every connection, short transactions, and explicit migration tests. |
| PostgreSQL | 16 or 17 for the migration target | Durable multi-user database path | Adopt when concurrent writers, deployment, or larger retrospective datasets make SQLite unsuitable; keep application SQL portable until that point. |
| Alembic | 1.19.2 release line | Schema migrations | It is the SQLAlchemy migration tool, supports SQLite batch migrations, and can run against both database URLs. |
| psycopg | Current stable 3.x | PostgreSQL driver | Use the modern PostgreSQL driver when the PostgreSQL profile is enabled; do not bake PostgreSQL-only SQL into the MVP. |

### Supporting Libraries

| Library | Version target | Purpose | When to use |
|---------|----------------|---------|-------------|
| Pydantic | Current stable 2.x line | API schemas, settings, validation | Use separate request, response, and persistence models; validate vital ranges and enum states at the boundary. |
| pydantic-settings | Current stable 2.x line | Environment-backed configuration | Centralize database URL, JWT settings, refresh interval, thresholds, CORS, and prototype labeling flags. |
| Uvicorn | Current stable release | ASGI server for local/demo runs | Run one process locally; use a process manager only when deployment needs it. |
| PyJWT or an equivalent maintained JWT library | Current stable release | JWT encode/decode | Use short-lived access tokens, explicit issuer/audience/expiry checks, and a server-side role lookup or narrowly scoped role claim. |
| pwdlib with Argon2 | Current stable release | Password hashing | Hash seeded demo passwords; never store plaintext credentials even in a research prototype. |
| TanStack Query | Current stable 5.x line | REST cache and mutation state | Use for dashboard reads and alert lifecycle mutations; invalidate or update queries after state transitions. |
| Native WebSocket client | Browser built-in | Live synthetic-vitals stream | Keep the WebSocket as a notification/stream channel and use REST as the authoritative read and mutation interface. |
| Vitest and Testing Library | Current stable releases | Frontend tests | Test role visibility, stale/live state, threshold presentation, and the P-1042 workflow. |
| pytest, httpx, and pytest-asyncio | Current stable releases | Backend/API tests | Test authorization, prediction payload stability, lifecycle transitions, WebSocket messages, and SQLite migrations. |
| Ruff | Current stable release | Python linting and formatting | One fast tool for consistent Python checks in local development and CI. |
| Playwright | Current stable release | Browser workflow tests | Exercise the primary demo journey across login, deterioration, dispatch, acknowledgement, response, and resolution. |

## Integration Patterns

### REST is authoritative; WebSockets are additive

Expose versioned REST resources such as `/api/v1/auth`, `/patients`, `/vitals`, `/predictions`, `/alerts`, `/dispatch`, `/notes`, `/configuration`, and `/audit`. Define stable Pydantic response models for prediction and alert payloads. Use WebSockets for synthetic vital samples and invalidation events such as `vitals.updated`, `prediction.created`, and `alert.changed`; on reconnect, refetch REST state because a socket can drop messages.

Authenticate the WebSocket during the handshake, authorize subscriptions server-side, validate message size and type, and close unauthorized or malformed connections. Do not let a client-provided patient or alert ID bypass the same object-level checks used by REST.

### Backend boundaries

Use modules for `auth`, `patients`, `vitals`, `prediction`, `historian`, `dispatch`, `alerts`, and `audit`. Route handlers should coordinate dependencies and schemas. Services should own business transitions. Repository/database code should own persistence. The prediction service should call a `PredictionAdapter` with the existing ML pipeline when available and a deterministic fallback for demos; persist model/version, feature timestamp, input provenance, threshold configuration, and explanation metadata with every result.

Run the synthetic vital generator as an application-owned background task for the single-process demo. It should emit every 5-10 seconds, be cancellable on shutdown, and never be mistaken for an external bedside device. A later deployment can move it to a worker or event broker without changing the REST contract.

### SQLite to PostgreSQL

Use SQLAlchemy URLs selected by configuration, SQLAlchemy generic types, UUID/string identifiers where portability matters, UTC-aware timestamps, named constraints, and Alembic migrations from the first schema. Enable SQLite foreign keys on every connection. Avoid SQLite-only JSON or upsert behavior in core workflows unless there is a PostgreSQL equivalent and an integration test. Run the migration suite against both SQLite and PostgreSQL before calling the path complete.

Keep one `Session` per request or one `AsyncSession` per task; never share a session across concurrent tasks. Use short `begin/commit/rollback` scopes so an alert transition and its audit event are committed atomically. SQLite is not a production concurrency strategy: document its single-file writer limitation and use PostgreSQL for multi-process or multi-user deployment.

### Authentication and authorization

Use JWT bearer authentication for the seeded accounts, with a password hash in the database and configuration-driven signing secret, issuer, audience, and token lifetime. API dependencies should resolve the current user, then enforce one of exactly `Admin`, `Doctor`, or `Nurse` permissions. A hidden navigation item is only a UX choice, never an authorization control. Nurses must be constrained to assigned work; doctors receive read-oriented clinical access; admins receive operational management access.

Use deny-by-default checks on every request and every object lookup. Test vertical and horizontal escalation explicitly, including changing a patient, alert, or nurse ID in a URL. Store audit rows with actor, role, action, target type/id, outcome, timestamp, request correlation ID, and safe before/after summaries. Do not log access tokens, passwords, raw clinical notes, or unnecessary identifiers.

## Safety and Prototype Practices

- Put a persistent UI/API label on every environment: **Simulated ICU environment - research prototype - not for clinical use**.
- Store synthetic vitals separately from retrospective MIMIC-IV imports, with a provenance/source field that cannot be omitted from API responses.
- Treat risk scores, historian adjustments, thresholds, horizons, and dispatch weights as configurable research rules, not validated clinical recommendations. Include rule/model version and a deterministic fallback indicator in prediction responses.
- Never stream MIMIC-IV as live data. MIMIC-IV v3.1 is retrospective, deidentified research data with credentialed access, required training, and a data-use agreement. Keep it in an offline import/training workflow and do not commit it, derived patient rows, or credentials to the repository.
- Seed only obviously fictional demonstration accounts and data. Require an environment-specific secret and refuse insecure default JWT secrets outside an explicitly marked demo mode.
- Add rate limits or at least bounded payload/message sizes, strict CORS origins, HTTPS in any shared environment, dependency lockfiles, secret scanning, and automated authorization regression tests.
- Make audit persistence part of the same transaction as each alert state transition. If audit storage fails, fail the mutation rather than silently creating an untraceable state change.

## What Not to Use in v1

| Avoid | Reason | Use instead |
|-------|--------|-------------|
| Next.js, Remix, or a second full-stack server framework | The PRD already has a FastAPI backend; adding server-side React routing duplicates API and deployment concerns. | React + Vite SPA with FastAPI REST/WebSockets. |
| GraphQL or gRPC | Not needed for the narrow demo contract and adds schema, caching, and operational complexity. | Versioned REST plus WebSocket events. |
| Redis, Kafka, Celery, or Kubernetes | Premature for one reproducible local process and synthetic streams. | FastAPI background task for v1; introduce a broker only for demonstrated multi-process needs. |
| Feature stores, vector databases, LLM agents, or online MLOps | They imply capabilities and clinical maturity the prototype does not need and can obscure deterministic provenance. | A versioned prediction adapter and transparent weighted dispatcher. |
| MIMIC-IV as runtime seed/live telemetry | Violates the retrospective research boundary and risks presenting deidentified research data as bedside monitoring. | Synthetic vitals at runtime; offline MIMIC-IV training/import tooling. |
| Client-only RBAC or JWT role trust without server checks | Easily bypassed and vulnerable to object-level access errors. | FastAPI dependencies plus per-resource authorization tests. |
| `Base.metadata.create_all()` as the schema strategy | It bypasses an auditable migration history and makes SQLite/PostgreSQL drift likely. | Alembic migrations, with autogenerate reviewed manually. |
| SQLite `:memory:` for concurrent async tests | Separate connections can see separate databases, and a shared single connection is not concurrent-safe. | File SQLite for app behavior; shared-cache or a controlled fixture only for narrow tests, plus PostgreSQL integration tests. |

## Installation Baseline

Pin exact versions in `pyproject.toml` and `package-lock.json` (or the repository's chosen lockfile), then refresh deliberately:

```bash
# Backend
python -m venv .venv
python -m pip install -U pip
python -m pip install fastapi uvicorn sqlalchemy alembic pydantic pydantic-settings \
  psycopg[binary] pyjwt pwdlib[argon2]
python -m pip install -D pytest pytest-asyncio httpx ruff

# Frontend
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @tanstack/react-query
npm install -D vitest @testing-library/react @testing-library/jest-dom playwright
```

The generated scaffold should be reviewed and committed with its lockfile; do not use `@latest` in the project's durable dependency declarations.

## Sources

- React documentation: https://react.dev/learn/start-a-new-react-project and https://react.dev/learn
- Vite guide and compatibility requirements: https://vite.dev/guide/
- FastAPI documentation: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0 documentation, SQLite dialect, and session basics: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html and https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- Alembic documentation, migrations, autogenerate, and SQLite batch mode: https://alembic.sqlalchemy.org/en/latest/ and https://alembic.sqlalchemy.org/en/latest/batch.html
- Pydantic documentation: https://docs.pydantic.dev/latest/
- MIMIC-IV v3.1 access, provenance, and release information: https://physionet.org/content/mimiciv/3.1/ and https://mimic.mit.edu/docs/iv/
- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html

## Confidence Notes

| Area | Level | Basis |
|------|-------|-------|
| React/Vite choice | MEDIUM | Official React and Vite docs support the setup; exact React/Vite patch pins remain an initialization task. |
| FastAPI/WebSocket/JWT pattern | MEDIUM | FastAPI's official documentation and the supplied PRD align, but the page extractor did not return all targeted FastAPI pages. |
| SQLAlchemy/Alembic/database path | HIGH | Current official SQLAlchemy and Alembic documentation directly covers 2.0 querying, sessions, SQLite behavior, PostgreSQL dialects, migrations, and batch mode. |
| MIMIC-IV boundary | HIGH | PhysioNet and MIT-LCP documentation explicitly identify the dataset as retrospective research data and document credentialed access and DUA requirements. |
| Security and audit practices | MEDIUM | OWASP official guidance directly supports deny-by-default authorization, per-request checks, authorization tests, and careful audit logging; application-specific policy still needs implementation tests. |

**Research status:** Current official-source cross-checks were classified MEDIUM by the configured research seam. Reconfirm package versions against the lockfile at project bootstrap and before any deployment beyond the local research demo.