# Phase 2 Plan Checker

**Review date:** 2026-08-24
**Scope:** All eight Phase 2 planning artifacts 02-01 through 02-08

**Verdict:** Ready for plan validation and execution

## Scope And Invariants

- [x] Phase 2 remains limited to AUTH-01 through AUTH-04, UI-01, PRED-01 through PRED-04, and ADMIN-01 through ADMIN-02.
- [x] Producer order is explicit: `02-07` is Wave 4, `02-04` is Wave 5 and depends on `02-07`, `02-05` is Wave 6, `02-06` is Wave 7, and `02-08` is Wave 8.
- [x] All eight plans are present, dated 2026-08-24, and retain bounded Phase 2 scope.
- [x] Exactly three seeded demo accounts remain: Admin, Doctor, and assigned Nurse Sarah.
- [x] The unassigned Nurse remains a deterministic persisted test-only fixture, excluded from demo seed and demo account counts.
- [x] Research decisions, synthetic provenance, prototype labeling, deterministic fallback, human confirmation boundaries, REST authority, and deferred later-phase entities remain preserved.

## Requirement Ownership

- [x] AUTH-01, AUTH-02, AUTH-04: `02-01` identity migration, seed, JWT session, current-user, logout, and rejection tests.
- [x] AUTH-03: `02-02` server-side role, patient, and Nurse assignment policy tests.
- [x] UI-01 primary owner: `02-06` role dashboards/navigation and exact owned frontend tests; `02-02` is supporting ownership for session guard behavior only.
- [x] PRED-01, PRED-02, PRED-03: `02-03` stable prediction DTO, ML-or-fallback adapter, protected route, and Prognosticator.
- [x] PRED-04 primary: `02-04` Admin-editable thresholds and research configuration, with configuration-to-adapter persistence proof; `02-07` is supporting ownership for typed configuration persistence.
- [x] ADMIN-01 primary: `02-04` Admin users, Nurse status, beds, refresh settings, thresholds, research rules, service/transport wiring, and create-user endpoint; `02-07` is supporting ownership for repository persistence.
- [x] ADMIN-02: `02-05` typed server-owned KPI read model and Admin dashboard.

## Blocker Resolution Checklist

- [x] `02-07` solely owns `backend/app/admin/repository.py`, `backend/app/admin/configuration.py`, and `backend/tests/test_admin_repository.py`, plus the supporting typed configuration persistence boundary; `02-04` has no repository/configuration persistence file ownership.
- [x] `02-07` names repository operations `get_user`, `create_user`, `update_user`, `update_nurse_status`, and `update_bed`, plus typed configuration persistence operations.
- [x] `02-04` has exactly two task blocks, a synchronized `estimate.tasks` value, and a 14-file `files_modified` list covering both task blocks; `02-07` has three files, with no overlap.
- [x] `02-04` is the primary Admin-01/PRED-04 owner and explicitly specifies `POST /api/v1/admin/users`, `create_admin_user`, `UserCreateRequest`, `UserResponse`, `create_prototype_user`, Admin success, Doctor/Nurse 403, validation, atomicity, persistence wiring, and the Admin frontend create-user form/client/success-error behavior.
- [x] `02-06` is the sole primary UI-01 owner, lists exact frontend test paths, and contains no recursive frontend test glob; `02-02` is supporting UI-01 session behavior.
- [x] `02-06` verification contains no `test_phase2_integration.py` or `scripts/phase2_smoke.py` references; those producer checks belong only to `02-08`.
- [x] Threat IDs are unique across all eight plans, including distinct IDs for `02-06` and `02-08`.
- [x] Reset/reseed, foreign-key safety, secret preflight, and secret-safe smoke expectations remain assigned to `02-01` and `02-08`.

## Ready Checks

- [x] Run the blocking PyJWT legitimacy and local secret setup checkpoint in `02-01` before installation.
- [x] Validate all eight plan frontmatters and task structures before execution.
- [x] Execute plans in declared wave order, with `02-07` completing before `02-04`; 02-04 consumes the persistence/configuration boundary and does not modify its owned file.
- [x] Run each plan's automated verification, including frontend tests/build/lint and producer-owned integration/smoke checks.
- [x] Confirm Phase 2 smoke output never prints secrets, passwords, or tokens.
- [x] Keep implementation status not started until execution produces plan summaries.

## Coverage Summary

All 11 Phase 2 requirement IDs have one explicit primary owning plan. Where frontmatter repeats `PRED-04` and `ADMIN-01`, `02-04` is primary and `02-07` is supporting for persistence only; `02-02` supports UI-01 session behavior, and `02-08` provides cross-plan integration evidence without changing primary requirement ownership. No alert, lifecycle, audit, historian, dispatch, WebSocket, live integration, enterprise identity, tenancy, or other deferred scope is introduced.
