---
phase: 01-safety-simulation-and-backend-contracts
plan: 06
subsystem: api
tags: [fastapi, safety, alembic, sqlite, pytest, uvicorn, smoke]
requires:
  - phase: 01-safety-simulation-and-backend-contracts
    provides: typed synthetic current-vitals API, deterministic P-1042 fixture, migration/reset helpers
provides:
  - centralized server-owned safety labels and typed health metadata
  - migration, foreign-key, reset-order, and provenance regression coverage
  - deterministic standard-library full-stack smoke runner and Windows setup documentation
affects: [phase-02-authentication, backend-contracts, developer-setup]
actuals:
  tokens: 4389
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [centralized safety metadata contract, child-process API smoke lifecycle, explicit migration-seed-reset workflow]
key-files:
  created:
    - backend/app/safety/__init__.py
    - backend/app/safety/labels.py
    - backend/app/contracts/metadata.py
    - backend/app/transport/health.py
    - backend/tests/test_migrations.py
    - backend/tests/test_safety_boundary.py
    - scripts/phase1_smoke.py
    - README.md
    - .env.example
  modified:
    - backend/app/main.py
key-decisions:
  - "Keep the exact non-clinical prototype label and synthetic source identity in one backend safety-label module."
  - "Expose health metadata through a typed response and reuse the centralized label/source values for current-vitals responses."
  - "Have the smoke runner establish deterministic tick 0 through the bounded fixture endpoint before asserting the authoritative current read."
patterns-established:
  - "SafetyMetadata rejects retrospective provenance and live-bedside claims at the Pydantic boundary."
  - "Windows smoke verification owns Uvicorn startup readiness polling and finally-based teardown."
requirements-completed: []
coverage:
  - id: D1
    description: "Health and current-vitals responses publish centralized synthetic, non-bedside prototype metadata."
    verification:
      - kind: unit
        ref: "backend/tests/test_safety_boundary.py"
        status: pass
      - kind: other
        ref: "python scripts/phase1_smoke.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fresh migration, SQLite foreign-key enforcement, explicit reset ordering, and provenance boundaries are executable regressions."
    verification:
      - kind: unit
        ref: "backend/tests/test_migrations.py"
        status: pass
      - kind: other
        ref: "cd backend; alembic --config alembic.ini check"
        status: pass
    human_judgment: false
  - id: D3
    description: "A checked-in Windows-friendly full-stack smoke and setup sequence documents the Phase 1 public synthetic boundary."
    verification:
      - kind: other
        ref: "README.md setup and verification commands"
        status: pass
      - kind: other
        ref: "npm --prefix frontend run test -- --run; npm --prefix frontend run build; npm --prefix frontend run lint"
        status: pass
    human_judgment: false
duration: 25 min
completed: 2026-08-24
status: complete
---

# Phase 1 Plan 6: Safety Regression and Full-Stack Smoke Summary

**Centralized synthetic safety metadata, migration/reset regressions, and a Windows-runnable Uvicorn smoke workflow close Phase 1 without adding authentication or clinical behavior.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-24T16:25:00Z
- **Completed:** 2026-08-24
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Centralized the exact prototype label and synthetic source identity, added typed health metadata, and wired the same server-owned safety boundary into current-vitals responses.
- Added regression tests covering fresh migration state, SQLite foreign-key enforcement, reset ordering, synthetic-only provenance, and health/current response metadata.
- Added `scripts/phase1_smoke.py`, which starts Uvicorn, waits for `/health`, establishes P-1042 tick 0 through the bounded fixture endpoint, asserts both required responses, and always tears down the child process.
- Added Windows PowerShell documentation for migration, idempotent seed, explicit reset, API/frontend startup, tests, build, lint, and the Phase 1 public synthetic scope.

## Task Commits

Each task was committed atomically, with the TDD task using RED/GREEN commits:

1. **Task 1 RED:** `132f001` (test: add safety and migration regressions)
2. **Task 1 GREEN:** `1d16da4` (feat: centralize safety metadata and migration guards)
3. **Task 2:** `b294d29` (docs: add Windows Phase 1 smoke workflow)
4. **Task 2 follow-up:** `9f2e43f` (fix: correct documented API launch directory)

**Plan metadata:** pending final planning metadata commit.

## Verification

- `cd backend; alembic --config alembic.ini upgrade head`: passed.
- `cd backend; alembic --config alembic.ini check`: passed with no new upgrade operations.
- `python scripts/phase1_smoke.py`: passed; `/health` and P-1042 current vitals were synthetic and labeled.
- Full Phase 1 backend subset: 18 passed, 14 existing dependency/deprecation warnings.
- `npm --prefix frontend run test -- --run`: 8 passed.
- `npm --prefix frontend run build`: passed.
- `npm --prefix frontend run lint`: passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test fixture defect] Used timezone-aware datetime values in migration tests**
- **Found during:** Task 1 GREEN verification
- **Issue:** The new SQLAlchemy fixtures supplied ISO strings to DateTime columns, so the tests failed before reaching the intended foreign-key and reset assertions.
- **Fix:** Replaced strings with timezone-aware `datetime` values.
- **Files modified:** `backend/tests/test_migrations.py`
- **Verification:** Focused migration and safety suite passed.
- **Committed in:** `1d16da4`

**2. [Rule 1 - Documentation defect] Corrected API launch directory**
- **Found during:** Task 2 documentation review
- **Issue:** Running `uvicorn backend.app.main:app` after `cd backend` would not resolve the repository-root package imports.
- **Fix:** Documented the Uvicorn command from the repository root, matching the smoke runner and test import path.
- **Files modified:** `README.md`
- **Verification:** `python scripts/phase1_smoke.py` passed after the correction.
- **Committed in:** `9f2e43f`

**Total deviations:** 2 auto-fixed (Rule 1: 2). **Impact:** Both were local correctness repairs; no scope expansion.

## Issues Encountered

The initial standalone Alembic check found the existing local database behind head. Running the prescribed upgrade first resolved that local state, after which `alembic check` passed. The pre-existing untracked `.planning/milestone.lock` was preserved and excluded from all commits.

## Known Stubs

None found in files created or modified by this plan.

## User Setup Required

None. Phase 1 uses local SQLite and no secrets or external services.

## Next Phase Readiness

Phase 1 now has executable safety, migration/reset, and full-stack smoke evidence. Public reads remain synthetic research-prototype views, bounded advance remains a fixture operation, and authenticated mutations are left for Phase 2.

## Self-Check: PASSED

- Summary file exists at the required path.
- Task commits `132f001`, `1d16da4`, `b294d29`, and `9f2e43f` exist in git history.
- All plan verification commands passed.
- No intentional stubs, skipped tests, or unrun verification remain.
- No new authentication, clinical behavior, or unrelated trust boundary was introduced.
- `.planning/milestone.lock` remains untouched and uncommitted.

---
*Phase: 01-safety-simulation-and-backend-contracts*
*Completed: 2026-08-24*
