# Phase 3 Plan Checker

**Review date:** 2026-08-24
**Scope:** Revised Phase 3 plans 03-01 through 03-04
**Verdict:** Ready for structural validation and execution after the Phase 2 prerequisite gate.

## Blocker Resolution Checklist

- [x] ALRT-01 owns a persisted/versioned `PredictionEvidence` artifact with prior/current score and source metadata.
- [x] The advance path is explicit: advance -> one `PredictionAdapter.predict` -> persist evidence -> compare prior committed evidence -> create/reuse/suppress alert in one transaction.
- [x] Tests name first, threshold crossing, non-crossing, repeated ticks, adapter call count, cooldown, re-arm, equality, and off-by-one boundaries.
- [x] Alert configuration ownership names `backend/app/contracts/configuration.py`, `backend/app/admin/configuration.py`, and `backend/app/transport/admin.py`, exact keys, ranges, cross-field validation, PATCH methods/paths, and focused tests.
- [x] AUDT-01 names the shared FastAPI HTTPException handler/dependency denial boundary and covers anonymous 401 plus authenticated 403 without changing status.
- [x] Configuration, Admin, alert, lifecycle, wrong-scope, and unassigned-Nurse route-level denial tests are assigned to the owning plan.
- [x] `backend/app/realtime/publisher.py` is owned by 03-02 with enqueue, after-commit publish, rollback discard, and focused tests before 03-03 consumes it.
- [x] 03-04 has concrete PowerShell fail-fast checks for pytest, backend imports, frontend node_modules/tsc, and WebSocket TestClient capability; missing prerequisites are blocked, never passes.
- [x] Every effective `files_modified` list is exact and <=15 files; no new implementation is created by planning.
- [x] All eight Phase 3 requirements remain covered, REST authority and safety labels remain locked, and Phase 4 historian/dispatch/nurse scope remains fenced.

## Wave And Ownership

- Wave 1: 03-01 threshold/evidence/configuration owner.
- Wave 2: 03-02 lifecycle/audit/denial/publisher owner; depends on 03-01.
- Wave 3: 03-03 realtime transport and frontend consumer; depends on 03-02.
- Wave 4: 03-04 reset/integration/smoke/prerequisite gate; depends on 03-03 and is the only non-autonomous plan.

## Requirement Ownership

- ALRT-01, ALRT-02: 03-01 primary, 03-04 integration evidence.
- ALRT-03, ALRT-04, ALRT-05, AUDT-01: 03-02 primary, 03-04 integration evidence.
- REAL-01, REAL-02: 03-03 primary, 03-04 integration evidence.

## Invariants

- Exactly three roles remain in scope.
- Synthetic provenance, deterministic fallback metadata, research-prototype labeling, and REST authority remain required.
- Phase 3 does not implement historian retrieval, nurse candidate ranking, human confirmation/override, fabricated no-candidate decisions, assigned-Nurse UX, or autonomous dispatch.
- Phase 2 verification uncertainty remains an explicit prerequisite and is not silently relabeled as passing evidence.
