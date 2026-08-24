---
phase: 03-monitoring-alerts-lifecycle-and-audit
plan: 03
subsystem: testing
tags: [react, tanstack-query, websocket, vitest, typescript]
requires:
  - phase: 03-monitoring-alerts-lifecycle-and-audit
    provides: REST alert lifecycle, audit evidence, and authenticated realtime invalidation tracer
provides:
  - Degraded-state and REST-authority frontend coverage for alert recovery
  - Live-token WebSocket URL generation and strict realtime ref typing
  - Explicit typed operational-state rendering coverage
affects: [Phase 3 verification, Phase 4 alert workflow]
actuals:
  tokens: 3200
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [fake WebSocket transport tests, fake-timer reconnect cleanup, REST-authoritative stale retention]
key-files:
  created: [.planning/phases/03-monitoring-alerts-lifecycle-and-audit/deferred-items.md]
  modified: [frontend/src/alerts/AlertPage.tsx, frontend/src/alerts/useAlertRealtime.ts, frontend/src/api/client.ts, frontend/src/alerts/AlertPage.test.tsx]
key-decisions:
  - "Keep no_candidate and not_yet_available as explicit typed presentation states without candidate logic."
  - "Use REST as the source of truth after scoped invalidations, reconnects, and failed refreshes."
requirements-completed: [REAL-01, REAL-02]
coverage:
  - id: D1
    description: "Alert UI preserves the last successful REST value while visibly marking failed refreshes stale."
    requirement: REAL-01
    verification:
      - kind: automated_ui
        ref: "frontend/src/alerts/AlertPage.test.tsx#retains the last REST value but marks it stale after a failed refresh"
        status: pass
    human_judgment: false
  - id: D2
    description: "Authenticated scoped invalidations trigger REST recovery with bounded reconnect and unmount cleanup."
    requirement: REAL-02
    verification:
      - kind: automated_ui
        ref: "frontend/src/alerts/AlertPage.test.tsx#validates socket scope, recovers through REST, bounds reconnect, and cleans up"
        status: pass
    human_judgment: false
---

# Phase 3 Plan 3: REST-authoritative realtime recovery Summary

**REST-authoritative alert recovery now has explicit degraded-state, authorization-failure, scoped invalidation, reconnect, and cleanup coverage.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-08-25T00:13:00Z
- **Completed:** 2026-08-25T00:15:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Covered loading, stale retention, unavailable REST failures including 401/403, deterministic fallback provenance, no active alert, no candidate, and not-yet-available states.
- Verified malformed and out-of-scope socket messages are ignored, valid scoped invalidations refetch REST evidence, reconnect is bounded, and unmount cleanup stops timers and sockets.
- Fixed live browser-token propagation in realtime URLs and strict React ref typing in the touched hook.

## Task Commits

1. **Task 1: Wire REST alert evidence through an authenticated invalidation channel to recovery UI** - `2fe2191` (feat)
2. **Task 2: Expand degraded-state and REST-authority coverage** - `a8286a6` (test)

## Files Created/Modified

- [AlertPage.test.tsx](frontend/src/alerts/AlertPage.test.tsx) - Adds focused degraded-state and realtime recovery tests.
- [AlertPage.tsx](frontend/src/alerts/AlertPage.tsx) - Accepts explicit typed operational states for honest presentation.
- [useAlertRealtime.ts](frontend/src/alerts/useAlertRealtime.ts) - Uses explicitly typed nullable refs.
- [client.ts](frontend/src/api/client.ts) - Uses the current stored token for WebSocket URL generation.

## Decisions Made

- Keep candidate-related states typed and presentational only; do not add Phase 4 candidate evaluation.
- Retain successful clinical evidence only with a prominent stale/disconnected state after refresh or socket failure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed stale token use in realtime URL generation**
- **Found during:** Task 2 focused socket tests
- **Issue:** The hook checked the current browser token but `realtimeUrl` still serialized the module-load token.
- **Fix:** Generate the URL from `getAccessToken()`.
- **Files modified:** `frontend/src/api/client.ts`
- **Verification:** Focused socket test passed with `access_token=token`.
- **Committed in:** `a8286a6`

**2. [Rule 3 - Blocking issue] Fixed strict React ref initialization in realtime hook**
- **Found during:** Task 2 production build
- **Issue:** Installed React types require initial values for `useRef`, causing build errors in the touched hook.
- **Fix:** Initialize timer and socket refs with `undefined` union types.
- **Files modified:** `frontend/src/alerts/useAlertRealtime.ts`
- **Verification:** Focused tests and lint passed; build no longer reports realtime hook errors.
- **Committed in:** `a8286a6`

**Total deviations:** 2 auto-fixed (Rule 1: 1, Rule 3: 1)
**Impact on plan:** Both fixes were directly required by Task 2 coverage and did not expand behavior beyond Phase 3.

## Issues Encountered

- `npm --prefix frontend run test -- --run src/alerts/AlertPage.test.tsx src/monitoring/MonitoringPage.test.tsx`: passed, 19 tests.
- `npm --prefix frontend run lint`: passed.
- `npm --prefix frontend run build`: blocked by four pre-existing strict-null diagnostics in `frontend/src/prediction/PredictionPage.tsx`; the touched realtime errors were fixed. This is recorded in [deferred-items.md](deferred-items.md).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

REST recovery and operational-state boundaries are covered for Phase 3. Phase 4 may build candidate and dispatch workflows on these contracts; no Phase 4 behavior was added here.

## Self-Check: PASSED

- Summary file exists.
- Task commits `2fe2191` and `a8286a6` exist in git history.
- Deferred build issue is recorded separately and is unrelated to this plan.

---
*Phase: 03-monitoring-alerts-lifecycle-and-audit*
*Completed: 2026-08-25*
