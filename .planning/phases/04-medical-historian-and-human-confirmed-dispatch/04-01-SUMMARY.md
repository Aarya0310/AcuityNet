---
phase: 04-medical-historian-and-human-confirmed-dispatch
plan: 01
subsystem: api
tags: [fastapi, sqlalchemy, alembic, pydantic, historian, audit]
requires:
  - phase: 03-monitoring-alerts-lifecycle-and-audit
    provides: alert evidence, lifecycle audit ordering, role-scoped access, and reset conventions
provides:
  - migration-backed typed P-1042 context facts and versioned research rules
  - protected Historian projection with baseline-only incomplete behavior and ordered timeline
  - Doctor-only audited timeline annotations
affects: [04-02, 04-06, historian, doctor-workflow]
actuals:
  tokens: 8796
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [normalized synthetic context facts, immutable rule evaluation snapshots, closed Pydantic DTOs, shared audit boundary]
key-files:
  created: [backend/app/migrations/versions/0004_historian_context.py, backend/app/contracts/historian.py, backend/app/historian/service.py, backend/app/transport/historian.py, backend/tests/test_historian.py, backend/tests/test_phase4_migration.py]
  modified: [backend/app/persistence/models.py, backend/app/main.py, backend/app/seed/demo_data.py, backend/app/seed/reset.py]
key-decisions:
  - "Use four normalized synthetic context categories and four rules.v1 definitions; contextual score is calculated only when every required category is fresh and complete."
  - "Keep annotations outside scoring and append annotation.created audit evidence with bounded structured details."
  - "Reuse the existing AlertService and lifecycle/audit projection boundaries; no frontend or dispatch behavior is added to this plan."
patterns-established:
  - "Historian reads are Admin/Doctor protected at transport and return a closed, unpaginated research projection."
  - "Missing or stale context yields baseline score, null contextual score, named missing evidence, and no partial delta total."
requirements-completed: [HIST-01, HIST-02, HIST-03]
coverage:
  - id: D1
    description: "Protected seeded P-1042 historian returns all four context categories, four named deltas, prototype provenance, prediction, alert slot, and ordered timeline."
    requirement: HIST-01
    verification:
      - kind: integration
        ref: "python -m pytest backend/tests/test_historian.py -q"
        status: unknown
      - kind: other
        ref: "direct migrated/seeded HistorianService smoke: complete, score 0.4, 4 rules, 9 timeline entries"
        status: pass
    human_judgment: true
    rationale: "The focused integration test could not collect because the active interpreter lacks the pinned PyJWT dependency."
  - id: D2
    description: "Historian completeness gate, immutable annotation semantics, audit evidence, migration indexes, and reset/reseed behavior are covered by focused regressions."
    requirement: HIST-02
    verification:
      - kind: unit
        ref: "python -m pytest backend/tests/test_phase4_migration.py -q"
        status: pass
      - kind: other
        ref: "python -m compileall -q backend/app backend/tests/test_historian.py backend/tests/test_phase4_migration.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Named configurable research-rule DTOs and explicit prototype labeling are persisted and returned without clinical-weighting claims."
    requirement: HIST-03
    verification:
      - kind: other
        ref: "fresh SQLite migration/seed smoke: four rules.v1 definitions and exact fictional facts"
        status: pass
    human_judgment: false

# Metrics
duration: 35min
completed: 2026-08-26
status: complete
---

# Phase 4 Plan 1: Medical Historian and Human-Confirmed Dispatch Summary

**Typed, seeded P-1042 historian context with named research-rule deltas, baseline-only incompleteness, ordered timeline evidence, and audited Doctor annotations.**

## Performance

- **Duration:** approximately 35 min
- **Started:** 2026-08-26
- **Completed:** 2026-08-26
- **Tasks:** 2
- **Files modified:** 10 unique application/test files

## Accomplishments

- Added Alembic revision `0004_historian_context` and SQLAlchemy models for context facts, rule definitions, immutable evaluations, and timeline annotations.
- Seeded exact fictional P-1042 diagnoses, medication, lab, prior ICU event, four `rules.v1` named deltas, and the 86,400-second historian freshness configuration.
- Added closed REST contracts and protected `/historian` and `/annotations` endpoints. The service returns complete contextual risk only when all required fresh categories exist; otherwise it preserves baseline risk and names missing evidence.
- Merged facts, prediction, alert, audit, rule, and annotation entries into a deterministic timeline while keeping annotations out of scoring.
- Added migration/reset and focused historian regression tests, including role and closed-DTO assertions.

## Task Commits

Each task was committed atomically:

1. **Task 1: Trace complete historian evidence from SQLite through the backend REST timeline projection** - `11ad952` (feat)
2. **Task 2 RED: Prove historian incompleteness, annotation immutability, migration, and access boundaries** - `55f6020` (test)
3. **Task 2 GREEN: Enforce historian completeness semantics** - `8c65bb0` (feat)

**Plan metadata:** pending final metadata commit

## Files Created/Modified

- `backend/app/migrations/versions/0004_historian_context.py` - Creates historian fact, rule, evaluation, and annotation tables plus lookup indexes.
- `backend/app/persistence/models.py` - Adds typed historian persistence models.
- `backend/app/seed/demo_data.py` - Seeds exact P-1042 context/rule fixtures and freshness configuration.
- `backend/app/historian/service.py` - Owns freshness/completeness evaluation, contextual score, projection, timeline, and annotation audit.
- `backend/app/contracts/historian.py` - Defines closed historian, rule, fact, timeline, and annotation DTOs.
- `backend/app/transport/historian.py` and `backend/app/main.py` - Wire protected Admin/Doctor REST access.
- `backend/app/seed/reset.py` - Deletes historian dependents before existing alert/prediction rows.
- `backend/tests/test_historian.py` and `backend/tests/test_phase4_migration.py` - Focused Phase 4 regression coverage.

## Decisions Made

- Contextual scoring uses all four required categories or none; stale facts are treated as missing evidence.
- The full timeline remains an additive read projection, with stable timestamp plus entry-ID ordering.
- Dispatch and frontend work remain deferred to their owned Phase 4 plans.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected historian projection control flow**
- **Found during:** Task 2 GREEN service smoke
- **Issue:** The first implementation constructed `current_prediction` but returned from the nested vital helper, causing `project()` to return `None`.
- **Fix:** Moved response assembly and timeline construction back into `project()`.
- **Files modified:** `backend/app/historian/service.py`
- **Verification:** Direct migrated/seeded service smoke passed with complete score `0.4`, four evaluations, and nine timeline entries.
- **Committed in:** `8c65bb0`

**Total deviations:** 1 auto-fixed (Rule 1: 1)
**Impact on plan:** Required for the historian REST projection to return its contract; no scope expansion.

## Issues Encountered

- `python -m pytest backend/tests/test_historian.py backend/tests/test_phase4_migration.py -q` and the required Phase 3 regression suite were blocked during collection by `ModuleNotFoundError: No module named 'jwt'` in the active interpreter. No package was installed because the plan specifies no package installation and package installs require human legitimacy verification.
- `python -m pytest backend/tests/test_phase4_migration.py -q` passed with one pre-existing Alembic deprecation warning.
- Pylance diagnostics found no errors in any touched file; compileall passed.
- Generated Python cache changes and the user’s existing `.planning/STATE.md`, plan edits, and `.planning/milestone.lock` were preserved and not staged.

## User Setup Required

None - no new external service configuration required. The existing backend environment must provide the pinned `PyJWT==2.13.0` dependency to run authenticated API tests.

## Next Phase Readiness

The backend historian contract is ready for 04-02’s Doctor evidence-timeline UI. The REST surface is synthetic/research-labeled, complete-context gated, role-protected, and compatible with existing Phase 3 alert/audit evidence. Dispatch persistence, confirmation, Nurse workflow, and frontend work remain for later plans.

## Self-Check: PASSED

- Summary file created at `.planning/phases/04-medical-historian-and-human-confirmed-dispatch/04-01-SUMMARY.md`.
- Task commits `11ad952`, `55f6020`, and `8c65bb0` exist in repository history.
- `backend/tests/test_phase4_migration.py` passed; direct service and migration/seed smoke checks passed.
- Touched-file diagnostics and compileall passed.

---
*Phase: 04-medical-historian-and-human-confirmed-dispatch*
*Completed: 2026-08-26*
