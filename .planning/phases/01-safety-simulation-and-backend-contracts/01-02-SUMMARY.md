---
phase: 01-safety-simulation-and-backend-contracts
plan: 02
subsystem: api
tags: [fastapi, sqlalchemy, sqlite, pytest, deterministic-simulation]
requires:
  - phase: 01-safety-simulation-and-backend-contracts
    provides: migration-backed schema and minimal stable P-1042 fixture
provides:
  - authoritative idempotent full P-1042 seed and explicit reset
  - versioned bounded p1042-demo five-tick scenario
  - short-lived-session immutable observation service with injected time
affects: [monitoring, alerts, prediction, phase-01-plans]
actuals:
  tokens: 3140
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns: [authoritative idempotent fixture repair, dependency-ordered reset, pure versioned scenario, service-owned observation persistence]
key-files:
  created: [backend/app/seed/reset.py, backend/app/vitals/__init__.py, backend/app/vitals/scenario.py, backend/app/vitals/service.py, backend/tests/test_seed.py, backend/tests/test_scenario.py]
  modified: [backend/app/seed/demo_data.py, backend/app/main.py]
key-decisions:
  - "Keep reset separate from migration execution and delete observations before dependent P-1042 fixture rows."
  - "Use the server-owned p1042-demo seed and exact fixed tuples as the scenario source; injected logical timestamps remain the only time input to persistence."
patterns-established:
  - "Seed repairs existing fictional rows to canonical values while preserving stable primary keys."
  - "ObservationService owns scenario identity and persists one immutable row per patient/tick."
requirements-completed: [VITAL-01, VITAL-02]
coverage:
  - id: D1
    description: "Reset and repeated full seed reproduce one stable P-1042 aggregate with patient, admission, bed, nurse, history, and resolved configuration."
    requirement: VITAL-01
    verification:
      - kind: unit
        ref: "backend/tests/test_seed.py::test_full_seed_has_stable_p1042_aggregate"
        status: pass
      - kind: unit
        ref: "backend/tests/test_seed.py::test_reset_then_reseed_and_repeated_seed_preserve_graph"
        status: pass
    human_judgment: false
  - id: D2
    description: "The p1042-demo scenario reproduces the exact five resolved deterioration ticks and persists immutable observations with bounded reset and injected time."
    requirement: VITAL-02
    verification:
      - kind: unit
        ref: "backend/tests/test_scenario.py::test_p1042_scenario_is_exact_and_bounded"
        status: pass
      - kind: integration
        ref: "backend/tests/test_scenario.py::test_service_persists_injected_time_and_immutable_ticks"
        status: pass
      - kind: other
        ref: "python -m pytest backend/tests/test_seed.py backend/tests/test_scenario.py backend/tests/test_walking_skeleton.py -q"
        status: pass
    human_judgment: false

duration: 18 min
completed: 2026-08-24
status: complete
---

# Phase 1 Plan 2: Full Seed and Deterministic Scenario Summary

**Idempotent resettable P-1042 fixture and exact bounded five-tick synthetic deterioration service**

## Performance

- **Duration:** 18 min
- **Started:** 2026-08-24T10:26:00Z
- **Completed:** 2026-08-24
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added canonical full seed repair and explicit dependency-ordered reset for the fictional P-1042 aggregate.
- Added exact `p1042-demo` tick values for ticks 0 through 4, with server-owned scenario identity and bounds.
- Added an observation service that uses injected logical timestamps, short-lived sessions, and immutable patient/tick persistence.
- Routed the existing advance endpoint through the scenario service without changing the synthetic, non-clinical prototype boundary.

## Task Commits

Each TDD task was committed through RED and GREEN checkpoints:

1. **Task 1 RED:** `ea92b01` (test: add failing tests for full seed reset)
2. **Task 1 GREEN:** `2dafd25` (feat: implement full idempotent demo reset)
3. **Task 2 RED:** `a153f05` (test: add failing tests for deterministic scenario)
4. **Task 2 GREEN:** `16a8c4b` (feat: implement deterministic P-1042 scenario service)

**Plan metadata:** captured in the final planning metadata commit.

## Files Created/Modified

- `backend/app/seed/demo_data.py` - repairs existing fixture rows to canonical fictional values and configuration.
- `backend/app/seed/reset.py` - deletes observations and demo aggregate rows in foreign-key order.
- `backend/app/vitals/scenario.py` - pure exact five-tick `p1042-demo` calculation with bounds and reset.
- `backend/app/vitals/service.py` - persists one immutable observation per patient/tick using injected time.
- `backend/app/main.py` - delegates advance persistence to the scenario service.
- `backend/tests/test_seed.py` - full aggregate and reset/reseed tests.
- `backend/tests/test_scenario.py` - exact scenario, bounds, persistence, and timestamp tests.

## Decisions Made

Reset is explicit and separate from Alembic migration execution. Seed remains idempotent and authoritative for the fictional P-1042 graph, while the scenario engine remains pure and versioned. The service rejects unsupported patients and persists synthetic provenance without clinical interpretation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test fixture] Seeded required foreign-key parents in scenario persistence test**
- **Found during:** Task 2 GREEN verification
- **Issue:** The new service test created an empty schema and attempted to persist an observation whose P-1042 patient and ICU bed did not exist.
- **Fix:** Seeded the existing P-1042 demo aggregate before exercising the observation service.
- **Files modified:** `backend/tests/test_scenario.py`
- **Verification:** Focused scenario suite passed with 2 tests.
- **Committed in:** `16a8c4b`

**Total deviations:** 1 auto-fixed (Rule 1). **Impact:** Required test-boundary correction only; no production scope expansion.

## Issues Encountered

Alembic emitted its existing `prepend_sys_path` deprecation warning and Starlette emitted its existing `httpx` compatibility warning. Both are non-blocking and unrelated to this plan's behavior; no unrelated files were changed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 01-03 can build typed monitoring/freshness and interval contracts on the stable seed, exact scenario values, and service persistence boundary. MIMIC-IV remains excluded from runtime seed data, and authenticated mutations remain deferred to Phase 2.

## Self-Check: PASSED

- Required summary file created at this path.
- Task commits `ea92b01`, `2dafd25`, `a153f05`, and `16a8c4b` exist in git history.
- `python -m pytest backend/tests/test_seed.py backend/tests/test_scenario.py backend/tests/test_walking_skeleton.py -q` passed: 7 tests passed.
- `get_errors` reported no errors in all 7 plan-owned source/test files.
- No stub or placeholder patterns were introduced in plan-owned files.

---
*Phase: 01-safety-simulation-and-backend-contracts*
*Completed: 2026-08-24*
