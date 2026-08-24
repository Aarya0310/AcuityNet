# Phase 2 Plan Checker

**Verdict:** FAIL

The four plans cover all 11 Phase 2 requirement IDs and the five roadmap success criteria at a high level, and their declared waves are acyclic (`02-01` -> `02-02` -> `02-03` -> `02-04`). The following issues must be addressed before execution.

## Blockers

1. **[requirement_coverage] ADMIN-01 is not actually planned.** `02-03` claims Admin management, but its tasks only define typed configuration and KPI work. No task specifies endpoints, service symbols, DTOs, persistence mutations, or tests for managing prototype users, nurse status, or beds. This leaves three required management capabilities uncovered.
   - **Plan:** `02-03`, Task 1
   - **Fix:** Add explicit user, nurse-status, and bed management actions with exact route/service/test targets, or split them into a dependent plan. Include Admin success cases, Doctor/Nurse 403 cases, validation, and persistence assertions.

2. **[requirement_coverage] AUTH-03 lacks a verifiable resource/assignment policy contract.** `02-01` says “minimum patient/nurse assignment relationship” and mentions wrong-patient and out-of-assignment tests, but does not identify the policy symbols, protected route matrix, assignment fixture(s), or the concrete behavior for Admin, Doctor, Nurse, and an unassigned Nurse. A single seeded Nurse assigned to P-1042 cannot prove the unassigned path.
   - **Plan:** `02-01`, Task 2
   - **Fix:** Define the exact policy functions and protected route paths, seed a second assignment state or a second Nurse fixture without adding a fourth role, and enumerate expected 401/403 outcomes for anonymous, wrong-role, wrong-patient, and unassigned access/advance calls.

3. **[scope_sanity] `02-01` is oversized for one execution slice.** Its single implementation task names 24 modified files and combines migration, seed/reset, password/JWT security, dependencies, policy, transport, existing-route protection, and a React auth shell. This exceeds the plan checker’s 15-file blocker threshold and makes the identity boundary difficult to validate incrementally.
   - **Plan:** `02-01`, Task 2
   - **Fix:** Split into a migration/seed/auth backend slice and a protected-route/frontend session slice, with an explicit dependency between them. Preserve the human package checkpoint before the backend JWT work.

## Warnings

4. **[key_links_planned] PRED-04 runtime wiring is asserted but not assigned to an implementation file.** `02-03` says effective settings are consumed by the prediction adapter, but `backend/app/prediction/adapter.py` is absent from `02-03`’s files and its action does not name the adapter entry point or a cross-plan integration test. An Admin write could therefore persist successfully while predictions continue using constants.
   - **Fix:** Name the adapter/service symbol and modify it in `02-03`, or add a focused test in `02-03` that proves a configuration update changes the next prediction without changing the adapter’s ownership plan.

5. **[task_completeness] Authorization and setup behavior are not exact enough for the requested safety review.** `02-01` names “existing current-vitals and advance routes” but not their route symbols, and `02-04` describes a Windows smoke runner without specifying how it supplies `ACUITYNET_JWT_SECRET`. The checks are runnable, but the intended protected surface and secret setup are not mechanically unambiguous.
   - **Fix:** List the exact FastAPI route paths/functions, policy dependencies, and smoke environment setup/assertions in the task actions.

6. **[dependency_correctness] Migration/seed reset consistency has no focused reset verification.** The plan includes `reset.py` and says to preserve deletion ordering, but `test_phase2_seed.py` and `test_phase2_migration.py` are the only named persistence checks; no test proves reset succeeds with the new user/assignment foreign keys and reseeding restores exactly the intended rows.
   - **Fix:** Add a reset/reseed assertion to the Phase 2 persistence tests or to the integration smoke path, including foreign-key enforcement and stable IDs/counts.

## Covered Areas

- `AUTH-01`, `AUTH-02`, and `AUTH-04`: seeded JWT, closed roles, current-user lookup, logout, expiry, and client clearing are described and tested in `02-01`.
- `PRED-01` through `PRED-03`: stable DTO, injected ML branch, deterministic fallback, missing-observation behavior, protected route, and Prognosticator coverage are described in `02-02`.
- `PRED-04` and `ADMIN-02`: typed Admin settings and server-owned KPI/unavailable states are substantially covered in `02-03`.
- `UI-01`: role-specific shell/dashboard behavior and frontend tests are covered across `02-01` and `02-04`.
- Safety labeling, fallback source metadata, frontend role presentation, and executable backend/frontend checks are present in the plans. Nyquist is disabled by project configuration, so no VALIDATION.md failure applies.
