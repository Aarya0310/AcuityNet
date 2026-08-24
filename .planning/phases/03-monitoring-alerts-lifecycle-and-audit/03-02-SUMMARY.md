---
phase: 03-monitoring-alerts-lifecycle-and-audit
plan: 02
subsystem: api
tags: [fastapi, sqlalchemy, audit, lifecycle, realtime]
requires:
  - phase: 03-monitoring-alerts-lifecycle-and-audit
    provides: threshold-backed alert persistence and deduplication from 03-01
provides:
  - Explicit generated-to-resolved alert lifecycle with role and assignment checks
  - Ordered, safe audit evidence and protected REST projections
  - Session-scoped post-commit realtime invalidation publisher
 affects: [phase-03-plan-03, phase-03-plan-04, phase-04]
actuals:
  tokens: 8515
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [single transition map, append-only audit rows, REST-authoritative post-commit notifications]
key-files:
  created: [backend/app/alerts/lifecycle.py, backend/app/audit/repository.py, backend/app/audit/service.py, backend/app/contracts/audit.py, backend/app/realtime/publisher.py, backend/app/transport/audit.py, backend/tests/test_lifecycle_audit.py, backend/tests/test_realtime_publisher.py]
  modified: [backend/app/alerts/repository.py, backend/app/alerts/service.py, backend/app/contracts/alerts.py, backend/app/main.py, backend/app/transport/admin.py, backend/app/transport/alerts.py]
key-decisions:
  - "Keep assignment_id and assignment evidence in safe lifecycle audit details because the 03-01 schema has no assignment column; derive current assignment from ordered audit evidence."
  - "Use server timestamp plus persisted event ID/index ordering and never persist authorization headers, tokens, or credentials."
  - "Keep realtime delivery additive and in-process; commit state and evidence through REST transactions first."
patterns-established:
  - "AlertLifecycleService owns the closed forward-only transition matrix and outcome validation."
  - "AuditService appends structured evidence in the caller transaction, while RealtimePublisher emits only after commit and discards rollback work."
requirements-completed: [ALRT-03, ALRT-04, ALRT-05, AUDT-01]
coverage:
  - id: D1
    description: "Authorized lifecycle transitions from generated through assigned, acknowledged, responded, and resolved"
    requirement: ALRT-03
    verification:
      - kind: integration
        ref: "backend/tests/test_lifecycle_audit.py::test_full_lifecycle_is_ordered_and_role_scoped"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ordered lifecycle and audit evidence with safe authenticated and anonymous denial records"
    requirement: AUDT-01
    verification:
      - kind: integration
        ref: "backend/tests/test_lifecycle_audit.py::test_invalid_transition_and_anonymous_denial_do_not_mutate_or_leak"
        status: pass
    human_judgment: false
  - id: D3
    description: "Post-commit realtime notification and rollback discard behavior"
    verification:
      - kind: unit
        ref: "backend/tests/test_realtime_publisher.py::test_publisher_commits_and_discards_session_messages"
        status: pass
    human_judgment: false
---
# Phase 3 Plan 2 Summary

**Role-scoped alert lifecycle with transactionally appended ordered audit evidence and post-commit invalidation publishing**

## Performance

- **Duration:** approximately 20 min
- **Started:** 2026-08-24
- **Completed:** 2026-08-24
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments

- Added strict `generated -> assigned -> acknowledged -> responded -> resolved` lifecycle commands with Admin/Doctor full control and assignment-scoped Sarah Nurse actions.
- Added typed alert event and audit projections, protected current/events/audit REST routes, successful configuration audit rows, and a shared 401/403 denial recorder that preserves HTTP status.
- Added session-owned realtime invalidation queuing with automatic post-commit publication and rollback discard behavior.
- Added focused integration and unit coverage for valid transitions, invalid skips, denial safety, ordering, and publisher behavior.

## Task Commits

1. **Task 1: Wire one authorized lifecycle path through state, events, audit, and REST** - `7409b8e`
2. **Task 2: Prove complete transition matrix, rollback, ordering, and denial evidence** - `41e1766`

## Files Created/Modified

- `backend/app/alerts/lifecycle.py` - Closed transition map, role checks, assignment validation, and lifecycle/audit mutation.
- `backend/app/audit/repository.py` and `backend/app/audit/service.py` - Append-only safe audit persistence and ordered reads.
- `backend/app/contracts/alerts.py` and `backend/app/contracts/audit.py` - Closed command and response DTOs.
- `backend/app/transport/alerts.py` and `backend/app/transport/audit.py` - Protected current alert, event, lifecycle, and audit endpoints.
- `backend/app/main.py` and `backend/app/transport/admin.py` - Service wiring, shared denial audit boundary, and configuration audit events.
- `backend/app/realtime/publisher.py` - Post-commit/rollback notification interface.
- `backend/tests/test_lifecycle_audit.py` and `backend/tests/test_realtime_publisher.py` - Focused verification.

## Decisions Made

Assignment evidence is stored in structured audit details and reconstructed from the ordered record to remain compatible with the existing 03-01 schema. Realtime remains a best-effort notification layer; REST remains authoritative.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Enforced assigned-Nurse read scope**
- **Found during:** Task 1
- **Issue:** The existing generic Nurse policy checked only the seeded user identity and patient, so a Nurse could inspect an alert before an assignment existed.
- **Fix:** Alert and audit reads now require a successful `N-SARAH` assignment evidence row for Nurse actors.
- **Files modified:** `backend/app/transport/alerts.py`, `backend/app/transport/audit.py`
- **Verification:** `test_full_lifecycle_is_ordered_and_role_scoped` and end-to-end lifecycle check passed.
- **Committed in:** `7409b8e`

**Total deviations:** 1 auto-fixed (Rule 2)
**Impact on plan:** Required for ALRT-05 resource scoping; no Phase 4 dispatch or Nurse UX was added.

## Issues Encountered

The expected `03-01-SUMMARY.md` was not present in the phase directory; execution used the actual committed 03-01 implementation and supplied plan/research artifacts. Generated `acuitynet.db` and Python cache files remain unstaged and were preserved.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

03-03 can add REST-authoritative realtime transport/recovery around the publisher interface. Phase 4 still owns historian context, dispatch ranking, human confirmation/override, no-candidate decisions, and Nurse UX.

## Self-Check: PASSED

- Summary file exists.
- Task commits `7409b8e` and `41e1766` exist in repository history.

## Verification

- `python -m pytest backend/tests/test_lifecycle_audit.py backend/tests/test_auth.py -q` -> **5 passed**
- `python -m pytest backend/tests/test_realtime_publisher.py backend/tests/test_auth.py -q` -> **3 passed**
- `python -m pytest backend/tests/test_alerts.py -q` -> **4 passed**
- Diagnostics for all touched backend files -> **No errors found**

---
*Phase: 03-monitoring-alerts-lifecycle-and-audit*
*Plan: 03-02*
*Completed: 2026-08-24*
