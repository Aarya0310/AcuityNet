# Codebase Structure

**Analysis Date:** 2026-08-24

## Directory Layout

```text
AcuityNet/
├── AGENTS.md                         # Repository-level agent guidance
├── README.md                         # Project overview and usage notes
├── pyproject.toml                    # Root Python project metadata
├── backend/
│   ├── pyproject.toml                # Backend dependencies and test extra
│   ├── alembic.ini                   # Migration logging and Alembic settings
│   ├── app/
│   │   ├── main.py                   # FastAPI factory, app instance, routes
│   │   ├── contracts/                # Pydantic request/response models
│   │   ├── migrations/               # Alembic environment and revisions
│   │   ├── persistence/              # SQLAlchemy engine, sessions, models
│   │   ├── safety/                   # Synthetic/prototype labels
│   │   ├── seed/                     # Idempotent demo fixture and reset tools
│   │   ├── transport/                # Health and configuration response helpers
│   │   └── vitals/                   # Scenario and observation domain service
│   └── tests/                        # Backend unit and API tests
├── frontend/
│   ├── index.html                    # Vite document shell
│   ├── package.json                  # Frontend scripts and dependencies
│   ├── vite.config.ts                # Vite/Vitest configuration
│   └── src/
│       ├── App.tsx                   # React application shell
│       ├── main.tsx                  # Browser mount and QueryClient provider
│       ├── styles.css                # Global and monitoring styles
│       ├── api/                      # REST client functions
│       ├── contracts/                # TypeScript wire contracts
│       ├── monitoring/               # Monitoring page and tests
│       └── safety/                   # Provenance and prototype UI components
├── scripts/
│   └── phase1_smoke.py               # End-to-end backend smoke runner
└── .planning/
    ├── PROJECT.md                    # Project intent and constraints
    ├── REQUIREMENTS.md               # Requirements and traceability
    ├── ROADMAP.md                    # Phase plan
    ├── STATE.md                      # Current GSD phase/status
    └── codebase/                     # Generated architecture map documents
```

## Directory Purposes

**`backend/app/`:**
- Purpose: Production backend package for the prototype.
- Contains: Application wiring, API contracts, persistence, migration code, seed data, safety metadata, transport helpers, and vitals logic.
- Key files: `backend/app/main.py`, `backend/app/persistence/models.py`, `backend/app/vitals/service.py`.

**`backend/app/contracts/`:**
- Purpose: Own server-side HTTP schemas and validation.
- Contains: `configuration.py`, `metadata.py`, `patients.py`, and `vitals.py`.
- Key files: `backend/app/contracts/vitals.py` for advance validation, freshness, provenance, and observation responses.

**`backend/app/persistence/`:**
- Purpose: Own database connectivity and SQLAlchemy mappings.
- Contains: `database.py` and `models.py`.
- Key files: `backend/app/persistence/database.py` for engine/session/migration setup; `backend/app/persistence/models.py` for schema mappings.

**`backend/app/migrations/`:**
- Purpose: Version the relational schema through Alembic.
- Contains: `env.py` and revision files under `backend/app/migrations/versions/`.
- Key files: `backend/app/migrations/versions/0001_phase1_foundation.py`.

**`backend/app/seed/`:**
- Purpose: Initialize and reset the fictional P-1042 development fixture independently from schema migration.
- Contains: `demo_data.py` and `reset.py`.
- Key files: `backend/app/seed/demo_data.py` for idempotent fixture state.

**`backend/app/vitals/`:**
- Purpose: Keep deterministic synthetic observation generation separate from HTTP transport.
- Contains: `scenario.py`, `service.py`, and package initialization.
- Key files: `backend/app/vitals/scenario.py` for bounded values and `backend/app/vitals/service.py` for persistence behavior.

**`backend/tests/`:**
- Purpose: Verify backend contracts, migrations, seed/reset behavior, safety boundaries, scenario values, API behavior, and the walking skeleton.
- Contains: `test_migrations.py`, `test_safety_boundary.py`, `test_scenario.py`, `test_seed.py`, `test_vital_contracts.py`, `test_vitals_api.py`, and `test_walking_skeleton.py`.
- Key files: `backend/tests/test_walking_skeleton.py` for end-to-end fixture/API behavior; `backend/tests/test_vitals_api.py` for route-level behavior.

**`frontend/src/`:**
- Purpose: Browser client for the monitoring prototype.
- Contains: React composition, REST client, mirrored contracts, styles, monitoring view/tests, and safety display components.
- Key files: `frontend/src/monitoring/MonitoringPage.tsx`, `frontend/src/api/client.ts`, and `frontend/src/App.tsx`.

**`frontend/src/monitoring/`:**
- Purpose: Own the current monitoring workflow and its component-level tests.
- Contains: `MonitoringPage.tsx` and `MonitoringPage.test.tsx`.
- Key files: `frontend/src/monitoring/MonitoringPage.tsx`.

**`frontend/src/safety/`:**
- Purpose: Present non-clinical prototype and provenance metadata.
- Contains: `PrototypeBanner.tsx` and `ProvenanceBadge.tsx`.
- Key files: `frontend/src/safety/ProvenanceBadge.tsx`.

**`.planning/`:**
- Purpose: Store GSD project intent, requirements, roadmap, state, and generated codebase intelligence.
- Contains: Planning artifacts and the `codebase/` output directory.
- Key files: `.planning/STATE.md` records that Phase 2, Identity, Authorization, and Prediction Adapter, is ready to plan.

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: Module-level ASGI app and `create_app` factory.
- `frontend/src/main.tsx`: React DOM mount and TanStack Query provider.
- `frontend/index.html`: Vite browser document.
- `scripts/phase1_smoke.py`: Executable smoke verification path.

**Configuration:**
- `backend/pyproject.toml`: Python version, backend dependencies, and pytest extra.
- `frontend/package.json`: Vite, TypeScript, React, Vitest, and test scripts.
- `frontend/vite.config.ts`: Frontend build/test tool configuration.
- `backend/alembic.ini`: Alembic configuration.
- `.planning/STATE.md`: Current project phase and constraints.

**Core Logic:**
- `backend/app/vitals/scenario.py`: Deterministic P-1042 observation sequence.
- `backend/app/vitals/service.py`: Idempotent observation advancement.
- `backend/app/persistence/models.py`: Relational model definitions.
- `backend/app/main.py`: Current HTTP use cases and response enrichment.
- `frontend/src/monitoring/MonitoringPage.tsx`: Monitoring UI behavior.

**Testing:**
- `backend/tests/`: Backend tests are separate from application package code.
- `frontend/src/monitoring/MonitoringPage.test.tsx`: Frontend test is co-located with the component.
- `frontend/src/test-setup.ts`: Frontend test environment setup.

## Naming Conventions

**Files:**
- Python modules use lowercase `snake_case`, such as `demo_data.py`, `database.py`, and `test_vitals_api.py`.
- React components use PascalCase filenames, such as `MonitoringPage.tsx`, `PrototypeBanner.tsx`, and `ProvenanceBadge.tsx`.
- Frontend tests append `.test.tsx` to the component/module name.
- Alembic revisions use a numeric prefix and descriptive suffix, such as `0001_phase1_foundation.py`.

**Directories:**
- Python package directories use lowercase nouns, such as `contracts`, `persistence`, `transport`, and `vitals`.
- Frontend directories use lowercase feature or responsibility names, such as `api`, `contracts`, `monitoring`, and `safety`.
- Planning output documents use uppercase names under `.planning/codebase/`.

**Symbols:**
- Python functions and variables use `snake_case`; classes use `PascalCase`.
- TypeScript functions and variables use `camelCase`; React components and type names use `PascalCase`.
- API paths use lowercase resource segments and version under `/api/v1/`.

## Where to Add New Code

**New Feature:**
- Primary backend use case: add the owning domain module under `backend/app/<feature>/`, then expose it through `backend/app/main.py` or a transport module matching the existing route-helper pattern.
- Backend contracts: add request/response models under `backend/app/contracts/` and mirror externally visible shapes in `frontend/src/contracts/`.
- Persistence changes: update `backend/app/persistence/models.py` and add a new Alembic revision under `backend/app/migrations/versions/`; do not rely on seed code to change schema.
- Tests: add backend behavior tests under `backend/tests/`; add frontend view tests beside the component under `frontend/src/<feature>/`.

**New Component/Module:**
- React feature components belong in a focused folder under `frontend/src/`, with API calls remaining in `frontend/src/api/` and safety display remaining in `frontend/src/safety/`.
- Backend reusable transport shaping belongs in `backend/app/transport/`; domain behavior belongs in its feature package rather than in a route handler.

**Utilities:**
- Shared backend data access belongs in `backend/app/persistence/` only when it is persistence-specific.
- Shared frontend HTTP behavior belongs in `frontend/src/api/client.ts`; avoid duplicating base URL and non-2xx handling in components.
- Cross-cutting safety constants belong in `backend/app/safety/` and should be carried by typed contracts.

## Special Directories

**`backend/app/migrations/versions/`:**
- Purpose: Committed Alembic schema history.
- Generated: No, revisions are authored and committed.
- Committed: Yes.

**`backend/.venv/` or frontend dependency/build directories:**
- Purpose: Local runtime/install artifacts when present.
- Generated: Yes.
- Committed: No; no such directories are part of the tracked source layout shown here.

**`.planning/codebase/`:**
- Purpose: Generated architecture, structure, quality, technology, and concern maps consumed by GSD planning.
- Generated: Yes, by mapping workflows.
- Committed: Expected to be committed as planning documentation; current files are this architecture mapping output.

---

*Structure analysis: 2026-08-24*
