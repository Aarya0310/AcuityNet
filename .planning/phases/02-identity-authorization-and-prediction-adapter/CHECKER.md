# Phase 2 Plan Checker

**Review date:** 2026-08-24
**Scope:** Current eight-plan Phase 2 planning set

**Verdict:** Ready for plan validation and execution

## Scope And Invariants

- [x] Phase 2 remains limited to AUTH-01 through AUTH-04, UI-01, PRED-01 through PRED-04, and ADMIN-01 through ADMIN-02.
- [x] Dependencies remain `02-01` -> `02-02` -> `02-03` -> `02-04`, then parallel Wave 5 plans `02-05` and `02-07`, followed by `02-06` and `02-08`; waves remain 1 through 7.
- [x] Exactly three seeded demo accounts remain: Admin, Doctor, and assigned Nurse Sarah.
- [x] The unassigned Nurse remains a deterministic persisted test-only fixture, excluded from demo seed and demo account counts.
- [x] Research decisions, synthetic provenance, prototype labeling, deterministic fallback, human confirmation boundaries, REST authority, and deferred later-phase entities remain preserved.

## Requirement Ownership

- [x] AUTH-01, AUTH-02, AUTH-04: `02-01` identity migration, seed, JWT session, current-user, logout, and rejection tests.
- [x] AUTH-03: `02-02` server-side role, patient, and Nurse assignment policy tests.
- [x] UI-01 primary owner: `02-06` role dashboards/navigation and exact owned frontend tests; `02-02` is supporting ownership for session guard behavior only.
- [x] PRED-01, PRED-02, PRED-03: `02-03` stable prediction DTO, ML-or-fallback adapter, protected route, and Prognosticator.
- [x] PRED-04: `02-04` Admin-editable thresholds and research configuration, with configuration-to-adapter persistence proof.
- [x] ADMIN-01: `02-04` Admin users, Nurse status, beds, refresh settings, thresholds, research rules, repository/service wiring, and create-user endpoint.
- [x] ADMIN-02: `02-05` typed server-owned KPI read model and Admin dashboard.

## Blocker Resolution Checklist

- [x] `02-07` owns `backend/app/admin/repository.py`, `backend/app/admin/configuration.py`, and `backend/tests/test_admin_repository.py`; `02-04` consumes that supporting persistence boundary.
- [x] `02-07` names repository operations `get_user`, `create_user`, `update_user`, `update_nurse_status`, and `update_bed`, plus typed configuration persistence operations.
- [x] `02-04` is the primary Admin-01/PRED-04 owner and explicitly specifies `POST /api/v1/admin/users`, `create_admin_user`, `UserCreateRequest`, `UserResponse`, `create_prototype_user`, Admin success, Doctor/Nurse 403, validation, atomicity, persistence wiring, and the Admin frontend create-user form/client/success-error behavior.
- [x] `02-06` is the sole primary UI-01 owner, lists exact frontend test paths, and contains no recursive frontend test glob; `02-02` is supporting UI-01 session behavior.
- [x] Reset/reseed, foreign-key safety, secret preflight, and secret-safe smoke expectations remain assigned to `02-01` and `02-08`.

## Execution Checks

- [ ] Run the blocking PyJWT legitimacy and local secret setup checkpoint in `02-01`.
- [ ] Validate all six plan frontmatters and task structures before execution.
- [ ] Execute plans in declared wave order and run each plan's automated verification.
- [ ] Confirm Phase 2 smoke output never prints secrets, passwords, or tokens.

## Coverage Summary

All 11 Phase 2 requirement IDs have one explicit primary owning plan. `02-02` supports UI-01 session behavior, `02-07` supports Admin persistence, and `02-08` provides cross-plan integration evidence without changing primary requirement ownership. No alert, lifecycle, audit, historian, dispatch, WebSocket, live integration, enterprise identity, tenancy, or other deferred scope is introduced.
