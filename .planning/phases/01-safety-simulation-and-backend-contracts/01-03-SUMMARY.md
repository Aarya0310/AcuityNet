---
phase: 01-safety-simulation-and-backend-contracts
plan: 03
subsystem: api
tags: [fastapi, pydantic, sqlalchemy, sqlite, pytest, freshness, deterministic-simulation]
requires:
  - phase: 01-safety-simulation-and-backend-contracts
    provides: seeded P-1042 fixture, bounded scenario, immutable observation service
provides:
  - typed patient, vital, freshness, provenance, and refresh configuration contracts
  - public read-only current-vitals and bounded interval-driven advance endpoints
  - server-owned freshness calculation and automatic progression before authoritative REST reads
affects: [monitoring-ui, alerts, prediction, phase-01-plans]
actuals:
  tokens: 4752
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [typed Pydantic transport DTOs, server-owned freshness policy, interval-driven bounded scenario advancement]
key-files:
  created: [backend/app/contracts/patients.py, backend/app/contracts/configuration.py, backend/app/transport/configuration.py, backend/tests/test_vital_contracts.py, backend/tests/test_vitals_api.py]
  modified: [backend/app/contracts/vitals.py, backend/app/main.py]
key-decisions:
  - "Keep current-vitals REST read-only and use the existing advance route for a bounded development fixture operation."
  - "Use server-owned synthetic-only provenance and freshness thresholds of 15 seconds fresh and 60 seconds stale."
  - "Expose refresh intervals as the exact server-defined set 5, 10, 30, and manual, with default 10 seconds."
patterns-established:
  - "Transport responses contain both legacy flat monitoring fields and a typed patient summary for compatibility and explicit context."
  - "Automatic interval requests advance exactly one backend logical tick; browser GET/refetch never mutates scenario state."
requirements-completed: []
coverage:
  - id: D1
    description: "Typed current-vitals responses expose patient and bed context, six vitals, timestamps, synthetic provenance, prototype labeling, and resolved freshness states."
    verification:
      - kind: unit
        ref: "backend/tests/test_vital_contracts.py"
        status: pass
      - kind: integration
        ref: "backend/tests/test_vitals_api.py::test_current_vitals_resolves_freshness_and_unavailable_state"
        status: pass
    human_judgment: false
  - id: D2
    description: "The backend publishes the supported refresh intervals and advances one bounded logical tick before returning authoritative REST state."
    verification:
      - kind: integration
        ref: "backend/tests/test_vitals_api.py::test_refresh_configuration_publishes_supported_intervals_and_default"
        status: pass
      - kind: integration
        ref: "backend/tests/test_vitals_api.py::test_automatic_advance_is_bounded_backend_owned_and_authoritative"
        status: pass
      - kind: other
        ref: "python -m pytest backend/tests -q"
        status: pass
    human_judgment: false
duration: 22 min
completed: 2026-08-24
status: complete
---

# Phase 1 Plan 3: Typed Monitoring and Refresh Contracts Summary

**Typed P-1042 monitoring contracts with server-owned freshness, synthetic provenance, and bounded backend refresh progression**

## Performance

- **Duration:** 22 min
- **Started:** 2026-08-24T10:41:00Z
- **Completed:** 2026-08-24
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added typed patient context, vital response, freshness enum, and synthetic-only provenance contracts.
- Added public read-only current-vitals mapping with server-computed fresh, stale, disconnected, and unavailable states.
- Added typed refresh configuration for exactly 5, 10, 30, and manual intervals with default 10 seconds.
- Added interval-only bounded automatic advancement that persists one backend tick before returning state; subsequent current GET returns the same authoritative representation.
- Preserved the existing Phase 2 JWT seam by leaving Phase 1 monitoring reads public and keeping advancement a development fixture operation.

## Task Commits

Each TDD task was committed atomically with RED and GREEN commits:

1. **Task 1 RED:** `074ad52` (test: add failing typed vital contract tests)
2. **Task 1 GREEN:** `15c0d0e` (feat: expose typed current vital contracts)
3. **Task 2 RED:** `c63a309` (test: add failing refresh configuration tests)
4. **Task 2 GREEN:** `398455f` (feat: publish refresh configuration and automatic progression)

**Plan metadata:** pending final planning metadata commit.

## Files Created/Modified

- [backend/app/contracts/patients.py](../../../backend/app/contracts/patients.py) - typed patient display, bed, and unit context.
- [backend/app/contracts/vitals.py](../../../backend/app/contracts/vitals.py) - bounded advance input, freshness policy, synthetic provenance, and vital response DTO.
- [backend/app/contracts/configuration.py](../../../backend/app/contracts/configuration.py) - supported refresh interval response contract.
- [backend/app/transport/configuration.py](../../../backend/app/transport/configuration.py) - database-backed configuration mapping.
- [backend/app/main.py](../../../backend/app/main.py) - authoritative REST response mapping and interval-driven advancement.
- [backend/tests/test_vital_contracts.py](../../../backend/tests/test_vital_contracts.py) - contract and freshness boundary tests.
- [backend/tests/test_vitals_api.py](../../../backend/tests/test_vitals_api.py) - API, configuration, and automatic progression tests.

## Decisions Made

The public monitoring contract remains synthetic-only and read-only for current state. Freshness is resolved by the backend from receipt age, with transport failure and observations older than the stale window represented as disconnected. Automatic refresh is modeled as an explicit interval-driven backend operation rather than a browser GET side effect.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Normalized SQLite naive timestamps for freshness comparison**
- **Found during:** Task 1 GREEN verification
- **Issue:** SQLite returned persisted timestamps without timezone metadata, causing aware/naive datetime subtraction to raise a `TypeError`.
- **Fix:** Treat persisted naive timestamps as UTC before calculating freshness.
- **Files modified:** backend/app/contracts/vitals.py
- **Verification:** Focused Task 1 suite passed with 5 tests.
- **Committed in:** `15c0d0e`

**2. [Rule 1 - Bug] Normalized persisted timestamps in authoritative responses**
- **Found during:** Task 2 GREEN verification
- **Issue:** The immediate advance response serialized UTC timestamps with `Z`, while a subsequent SQLite-backed current GET serialized the same values without `Z`.
- **Fix:** Normalize ORM timestamps to UTC-aware values before response serialization.
- **Files modified:** backend/app/main.py
- **Verification:** Focused Task 2 suite passed with 5 tests; full backend suite passed with 15 tests.
- **Committed in:** `398455f`

**Total deviations:** 2 auto-fixed (Rule 1 bugs). **Impact:** Both fixes were local correctness repairs required for truthful freshness and REST-authority equality; no scope expansion.

## Issues Encountered

The full backend run retains 13 existing deprecation warnings from Alembic configuration and Starlette/httpx compatibility. They are non-blocking and unrelated to this plan. Plan-owned files report no diagnostics.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The monitoring API now provides the typed, server-authoritative contract needed by the frontend refresh and safety-state plans. The five-tick scenario remains bounded and server-owned, and JWT authentication remains deferred to Phase 2 as planned.

## Self-Check: PASSED

- Required summary file exists at this path.
- Task commits `074ad52`, `15c0d0e`, `c63a309`, and `398455f` exist in git history.
- `python -m pytest backend/tests -q` passed: 15 tests passed.
- Plan-owned source and test files report no diagnostics.
- No stub or placeholder patterns were introduced in plan-owned files.

---
*Phase: 01-safety-simulation-and-backend-contracts*
*Completed: 2026-08-24*
