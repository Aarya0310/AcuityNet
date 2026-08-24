---
phase: 03-monitoring-alerts-lifecycle-and-audit
plan: 04
subsystem: testing
tags: [sqlite, fastapi, uvicorn, websocket, audit, smoke]
requires:
  - phase: 03-monitoring-alerts-lifecycle-and-audit
    provides: REST alert lifecycle, audit persistence, and realtime invalidation contracts
provides:
  - Dependency-safe Phase 3 reset and deterministic reseed verification
  - Cross-layer P-1042 monitoring, alert, lifecycle, audit, authorization, KPI, and recovery proof
  - Secret-safe isolated Uvicorn smoke runner and dated clean-run documentation
affects: [Phase 3 verification, Phase 4 historian and dispatch]
actuals:
  tokens: 5933
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [temporary SQLite app isolation, child-process smoke preflight, REST-authoritative recovery]
key-files:
  created: [backend/tests/test_phase3_integration.py, scripts/phase3_smoke.py]
  modified: [backend/app/seed/reset.py, backend/app/main.py, backend/app/admin/kpis.py, backend/tests/test_phase3_migration.py, README.md]
key-decisions:
  - "Delete Phase 3 child rows before parent alert, evidence, and Phase 1 fixture rows; keep migration separate from seeding."
  - "Use an environment-selected temporary database for child-process smoke runs so developer database artifacts remain untouched."
  - "Expose persisted alert KPI counts while retaining response metrics as Phase 4 not_yet_available values."
patterns-established:
  - "Integration fixtures may add U-ALEX only as an unassigned test user; seed_demo_data remains exactly three accounts."
  - "WebSocket input and malformed transport are recovery boundaries; REST remains authoritative after close or failure."
requirements-completed: [ALRT-01, ALRT-02, ALRT-03, ALRT-04, ALRT-05, AUDT-01, REAL-01, REAL-02]
coverage:
  - id: D1
    description: "Clean migrated SQLite reset/reseed removes Phase 3 children safely and restores exactly three demo accounts."
    requirement: ALRT-02
    verification:
      - kind: integration
        ref: "backend/tests/test_phase3_migration.py#test_reset_deletes_phase3_children_before_reseed"
        status: pass
    human_judgment: false
  - id: D2
    description: "A real P-1042 journey proves threshold crossing, fallback provenance, deduplication, lifecycle ordering, audit evidence, authorization denials, KPI backing, malformed realtime recovery, and REST recovery."
    requirement: ALRT-01
    verification:
      - kind: integration
        ref: "backend/tests/test_phase3_integration.py#test_complete_phase3_journey_is_reconstructable_and_role_scoped"
        status: pass
      - kind: integration
        ref: "python -m pytest backend/tests/test_phase3_migration.py backend/tests/test_phase3_integration.py backend/tests/test_alerts.py backend/tests/test_lifecycle_audit.py backend/tests/test_realtime.py -q"
        status: pass
    human_judgment: false
  - id: D3
    description: "Secret-safe temporary Uvicorn smoke execution is reproducible and documents Phase 4 boundaries."
    requirement: REAL-01
    verification:
      - kind: e2e
        ref: "python scripts/phase3_smoke.py (executed twice)"
        status: pass
    human_judgment: false
---

# Phase 3 Plan 4: Clean-fixture monitoring and audit proof Summary

**A clean temporary SQLite fixture now reproduces the P-1042 threshold-to-audit journey with dependency-safe reset, role-scoped evidence, REST recovery, and secret-safe Uvicorn smoke verification.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-25T00:20:00Z
- **Completed:** 2026-08-25
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Reset deletes alert events and audit rows before alerts, prediction evidence, observations, and existing fixture parents; reseed remains idempotent and restores exactly three demo accounts without fabricated alerts or assignments.
- Added a real TestClient integration journey covering U-ADMIN, U-DOCTOR, U-SARAH, test-only U-ALEX, exact deterioration ticks, deterministic fallback evidence, alert deduplication, lifecycle transitions, ordered audit reconstruction, denial auditing, persisted KPI counts, malformed realtime close, and REST recovery.
- Added temporary-database child-process smoke verification and dated PowerShell documentation. Response time, acknowledgement rate, historian, ranking, human confirmation/override, nurse dispatch, and assigned-Nurse UX remain explicitly Phase 4 scope.

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire clean reset/reseed through the complete Phase 3 integration journey** - `9993b02` (feat)
2. **Task 2: Expand cross-layer regression gates and reset integrity** - `a8bd5f5` (test)

## Files Created/Modified

- `backend/app/seed/reset.py` - Deletes Phase 3 child and parent rows in foreign-key-safe order.
- `backend/app/main.py` - Allows an environment-selected database URL for isolated smoke processes.
- `backend/app/admin/kpis.py` - Reports persisted alert counts while retaining Phase 4 response metrics as unavailable.
- `backend/tests/test_phase3_migration.py` - Covers migrated schema, reset ordering, and exact reseed counts.
- `backend/tests/test_phase3_integration.py` - Covers the cross-layer P-1042 journey and security/recovery regressions.
- `scripts/phase3_smoke.py` - Runs the secret-safe temporary Uvicorn smoke journey.
- `README.md` - Documents dated PowerShell commands, expected typed states, and Phase 4 limitations.

## Decisions Made

- Kept `U-ALEX` out of production/demo seeding and created it only inside the authorization integration fixture.
- Used an environment-selected temporary database to ensure smoke execution never mutates the existing local database.
- Kept WebSocket behavior additive and malformed-message handling non-mutating; REST reads remain the recovery authority.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Isolated smoke database selection**
- **Found during:** Task 1 smoke implementation
- **Issue:** The global app construction otherwise targets the developer `acuitynet.db`, which would make a child-process smoke run mutate an unrelated local artifact.
- **Fix:** `create_app` honors `ACUITYNET_DATABASE_URL`; the smoke child supplies a temporary SQLite URL.
- **Files modified:** `backend/app/main.py`, `scripts/phase3_smoke.py`
- **Verification:** Smoke command passed twice and the existing database remained unstaged.
- **Committed in:** `9993b02`

**2. [Rule 2 - Missing Critical] Backed alert KPI values with Phase 3 rows**
- **Found during:** Task 1 integration assertions
- **Issue:** The admin KPI response still reported alerts as unavailable after alert persistence existed.
- **Fix:** Count persisted alerts and active high/critical alerts while leaving response metrics unavailable for Phase 4.
- **Files modified:** `backend/app/admin/kpis.py`
- **Verification:** Integration KPI assertions passed.
- **Committed in:** `9993b02`

**3. [Rule 1 - Test fixture defects] Corrected transaction, datetime, count, and import setup in new regression tests**
- **Found during:** focused migration/integration validation
- **Issue:** The first fixture wrapped a committing seed in an outer transaction, used string DateTime values, expected aggregate count `None`, and omitted `Path`/`User` imports.
- **Fix:** Use explicit fixture commits, typed UTC datetimes, correct aggregate expectations, and required imports.
- **Files modified:** `backend/tests/test_phase3_migration.py`, `backend/tests/test_phase3_integration.py`
- **Verification:** Focused suite passed with 5 tests; full listed suite passed with 15 tests.
- **Committed in:** `a8bd5f5`

**Total deviations:** 3 auto-fixed (Rule 2: 2, Rule 1: 1)
**Impact on plan:** All changes were directly required for isolated correctness, security, or the plan's requested executable evidence. No Phase 4 behavior was added.

## Issues Encountered

- The listed suites pass with 25 existing deprecation/insecure-key warnings from installed dependencies; no warning blocked verification.
- Pre-existing `acuitynet.db` modification and generated `__pycache__` artifacts were preserved and not staged.

## User Setup Required

None beyond the documented local `ACUITYNET_JWT_SECRET` environment variable for the smoke command.

## Next Phase Readiness

Phase 3 has executable clean-fixture evidence for monitoring, alert persistence, lifecycle, audit, authorization, and realtime recovery. Phase 4 can add historian, candidate ranking, dispatch, human confirmation/override, response metrics, and nurse UX on these contracts. No open blocker remains for this plan.

## Self-Check: PASSED

- Summary file created at `.planning/phases/03-monitoring-alerts-lifecycle-and-audit/03-04-SUMMARY.md`.
- Task commits `9993b02` and `a8bd5f5` exist in git history.
- Full listed regression suite passed: 15 tests.
- Smoke command passed twice with temporary SQLite databases.
- Existing `acuitynet.db` and generated cache artifacts were not staged.

---
*Phase: 03-monitoring-alerts-lifecycle-and-audit*
*Completed: 2026-08-25*
