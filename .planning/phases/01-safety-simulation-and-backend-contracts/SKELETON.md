# Walking Skeleton — AcuityNet

**Phase:** 1
**Generated:** 2026-08-24

## Capability Proven End-to-End

A developer can open the React/Vite monitoring page, trigger one deterministic P-1042 synthetic observation, and see the migration-backed current vital response with its timestamps, freshness state, provenance, and research-prototype label.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | React 19 + TypeScript + Vite SPA, FastAPI Python API | Matches the approved modular-monolith architecture and keeps the browser/API boundary explicit. |
| Data layer | SQLAlchemy 2 + Alembic + file-backed SQLite | Zero-service local setup with an auditable migration path to PostgreSQL. |
| Auth | Public read-only synthetic monitoring for the local prototype; bounded advance is a development fixture operation; no Phase 1 session | Authentication and authenticated mutations are owned by Phase 2+; Phase 1 must clearly label this boundary and not imply production access control. |
| Deployment target | Local development: one Uvicorn process and one Vite dev server | Reproduces the synthetic demonstration on a developer machine without external services. |
| Directory layout | `backend/app/{contracts,persistence,seed,vitals,safety,transport}` and `frontend/src/{api,contracts,monitoring,safety}` | Follows the researched responsibility map and keeps domain logic out of transport and presentation. |
| Source of truth | REST current-vitals reads and mutation responses; WebSocket is additive | Reload and reconnect remain recoverable and the browser does not invent monitoring truth. |
| Simulation | Versioned scenario ID and seed with injected logical clock and bounded tick advancement | Wall-clock scheduling controls cadence only; scenario values remain deterministic and testable without sleeping. |
| Safety boundary | Required provenance and prototype-label metadata on monitoring responses and views | Synthetic ICU data, retrospective research data, and clinical claims must remain visibly distinct. |

## Stack Touched in Phase 1

- [ ] Project scaffold: framework, build, lint, and test runner (frontend bootstrap is owned by Plan 04)
- [ ] Routing: one real monitoring route
- [ ] Database: one real migration-backed read and one real write
- [ ] UI: one button/interaction wired to the API
- [ ] Deployment: documented local full-stack run and checked-in `scripts/phase1_smoke.py` API smoke command

## Phase 1 Plan Ownership

Requirement ownership is intentionally exact-once across plan frontmatter: DATA-01 and DATA-02 belong to Plan 01; VITAL-01 and VITAL-02 belong to Plan 02; VITAL-03 and SAFE-01 belong to Plan 04. Plans 03, 05, and 06 expand or verify those contracts without duplicate requirement claims.

## Out of Scope (Deferred to Later Slices)

- JWT login, password hashing, seeded authentication sessions, and role enforcement
- Prediction adapter, clinical prognostication, thresholds, alerts, dispatch, historian rules, and audit lifecycle
- MIMIC-IV ingestion or runtime retrospective/replay feeds
- Multi-patient monitoring, device integrations, production PHI, and deployment infrastructure
- Autonomous staffing or any diagnosis, treatment, or bedside recommendation behavior

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without changing its architectural decisions:

- Phase 2: seeded JWT identity, server-side roles, and stable prediction adapter contract
- Phase 3: recoverable live updates, threshold alerts, lifecycle state machine, and audit evidence
- Phase 4: contextual historian explanation, human-confirmed dispatch, and assignment-scoped Nurse workflow
- Phase 5: clean-reset browser journey, degraded-state verification, and demo hardening
