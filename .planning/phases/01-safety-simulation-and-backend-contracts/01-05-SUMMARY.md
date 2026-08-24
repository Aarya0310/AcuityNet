---
phase: 01-safety-simulation-and-backend-contracts
plan: 05
subsystem: ui
tags: [react, typescript, vitest, refresh, safety]
requires:
  - phase: 01-safety-simulation-and-backend-contracts
    provides: typed P-1042 monitoring and server-owned freshness/provenance contracts
provides:
  - typed server refresh configuration client
  - backend-owned bounded advance followed by authoritative current GET
  - reusable prototype and provenance safety components
affects: [phase-02-authentication, monitoring-ui]
actuals:
  tokens: 3706
  tasks: 1
  commits: 3
tech-stack:
  added: []
  patterns: [server-configured refresh selector, advance-then-authoritative-read orchestration, reusable safety metadata components]
key-files:
  created:
    - frontend/src/contracts/configuration.ts
    - frontend/src/safety/PrototypeBanner.tsx
    - frontend/src/safety/ProvenanceBadge.tsx
  modified:
    - frontend/src/api/client.ts
    - frontend/src/monitoring/MonitoringPage.tsx
    - frontend/src/monitoring/MonitoringPage.test.tsx
key-decisions:
  - "Use the server default numeric interval for manual bounded advance because the backend advance contract accepts only 5, 10, or 30 seconds."
  - "Keep the exact non-clinical prototype label and server-provided provenance visible at the monitoring surface."
requirements-completed: []
coverage:
  - id: D1
    description: "Monitoring refresh controls render exactly the server-provided 5, 10, 30, and manual options."
    verification:
      - kind: unit
        ref: "frontend/src/monitoring/MonitoringPage.test.tsx"
        status: pass
      - kind: other
        ref: "npm --prefix frontend run build"
        status: pass
    human_judgment: false
  - id: D2
    description: "Manual and automatic refresh advance backend state before the authoritative current GET and clean up timers on unmount."
    verification:
      - kind: unit
        ref: "frontend/src/monitoring/MonitoringPage.test.tsx"
        status: pass
      - kind: other
        ref: "npm --prefix frontend run lint"
        status: pass
    human_judgment: false
  - id: D3
    description: "Reusable prototype and provenance components preserve visible non-clinical and server-owned metadata."
    verification:
      - kind: unit
        ref: "frontend/src/monitoring/MonitoringPage.test.tsx"
        status: pass
      - kind: other
        ref: "frontend diagnostics"
        status: pass
    human_judgment: false

duration: 12 min
completed: 2026-08-24
status: complete
---

# Phase 1 Plan 5: Server-Driven Monitoring Refresh Summary

**Server-configured 5/10/30/manual monitoring refresh with bounded backend advancement, authoritative REST reads, and reusable safety metadata**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-24T16:34:00Z
- **Completed:** 2026-08-24
- **Tasks:** 1
- **Files modified:** 6

## Accomplishments

- Added a typed refresh configuration contract and REST client methods for configuration and bounded vital advancement.
- Wired manual and automatic refresh to await backend-owned advance before fetching authoritative current vitals; interval timers are cleared on unmount.
- Added reusable `PrototypeBanner` and `ProvenanceBadge` components while preserving the exact non-clinical label and server metadata.
- Added fake-timer coverage for exact selector values, call ordering, and cleanup behavior.

## Task Commits

TDD task was committed with RED and GREEN commits:

1. **Task 1 RED:** `82fd3a6` (test: add refresh orchestration coverage)
2. **Task 1 GREEN:** `9d3c073` (feat: wire server-driven monitoring refresh)

**Plan metadata:** pending final planning metadata commit.

## Files Created/Modified

- `frontend/src/contracts/configuration.ts` - typed server refresh interval contract.
- `frontend/src/api/client.ts` - typed configuration and bounded advance requests.
- `frontend/src/monitoring/MonitoringPage.tsx` - configuration loading, refresh sequencing, interval lifecycle, and controls.
- `frontend/src/monitoring/MonitoringPage.test.tsx` - focused fake-timer and call-order coverage.
- `frontend/src/safety/PrototypeBanner.tsx` - shared mandated prototype label.
- `frontend/src/safety/ProvenanceBadge.tsx` - shared server provenance presentation.

## Decisions Made

Manual refresh invokes the bounded backend operation using the currently selected numeric interval, falling back to the server default when the selector is manual. The browser never advances scenario values locally and always follows advance with the current REST GET.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected provenance sequence rendering**
- **Found during:** Task 1 GREEN verification
- **Issue:** The initial reusable provenance component displayed the scenario identifier where the observation sequence belonged.
- **Fix:** Passed the authoritative observation sequence as a dedicated component prop.
- **Files modified:** `frontend/src/safety/ProvenanceBadge.tsx`, `frontend/src/monitoring/MonitoringPage.tsx`
- **Verification:** Focused suite passed with the original sequence assertion.
- **Committed in:** `9d3c073`

**2. [Rule 1 - Test infrastructure] Made fake-timer async assertions deterministic**
- **Found during:** Task 1 GREEN verification
- **Issue:** Testing Library polling helpers depend on real timer progression and timed out under fake timers.
- **Fix:** Used React `act` with explicit promise flushing and fake timer advancement.
- **Files modified:** `frontend/src/monitoring/MonitoringPage.test.tsx`
- **Verification:** Focused suite passed: 8 tests.
- **Committed in:** `9d3c073`

**Total deviations:** 2 auto-fixed (Rule 1: 2). **Impact:** Both were local correctness/test reliability repairs required to verify the planned behavior; no scope expansion.

## Issues Encountered

The shared worktree contains an unrelated untracked `.planning/milestone.lock`; it was left untouched and was not included in the plan commits.

## User Setup Required

None - the frontend uses the existing local backend endpoints.

## Next Phase Readiness

The monitoring surface now has a server-driven refresh boundary suitable for later authenticated transport. REST remains authoritative, and safety/provenance metadata remains visible during refresh and degraded states.

## Self-Check: PASSED

- Summary file created at the required path.
- Task commits `82fd3a6` and `9d3c073` exist in git history.
- Focused frontend tests passed: 8 tests.
- `npm --prefix frontend run build` passed.
- `npm --prefix frontend run lint` passed.
- Touched-file diagnostics report no errors.
- Stub scan found no placeholder, TODO, FIXME, or empty UI data source patterns.
- No new unplanned network, auth, file-access, or schema trust boundary was introduced.

---
*Phase: 01-safety-simulation-and-backend-contracts*
*Completed: 2026-08-24*
