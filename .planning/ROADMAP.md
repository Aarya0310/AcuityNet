# Roadmap: AcuityNet

## Overview

AcuityNet v1 delivers one safe, reproducible P-1042 journey: seeded users observe clearly labeled synthetic deterioration, receive a stable research prediction, understand contextual risk, inspect a transparent human-confirmed nurse recommendation, complete the alert response workflow, and reconstruct the result from ordered audit evidence. The roadmap keeps safety and contracts ahead of role workflows, then closes with clean-reset verification and demo hardening.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Safety, Simulation, and Backend Contracts** - Establish truthful provenance, deterministic P-1042 data, persistence, and monitoring contracts. (completed 2026-08-24)
- [x] **Phase 2: Identity, Authorization, and Prediction Adapter** - Make access role-aware and predictions stable, configurable, and honest about fallback behavior. (executed 2026-08-24; verification blockers recorded)
- [ ] **Phase 3: Monitoring, Alerts, Lifecycle, and Audit** - Turn deterioration into deduplicated, recoverable, auditable alert state.
- [ ] **Phase 4: Medical Historian and Human-Confirmed Dispatch** - Explain patient context and complete nurse workflow with explicit human control.
- [ ] **Phase 5: End-to-End Verification and Demo Hardening** - Prove the journey, degraded states, permissions, reset path, and prototype boundaries.

## Phase Details

### Phase 1: Safety, Simulation, and Backend Contracts

**Goal**: As a developer, I can open a reproducible P-1042 synthetic ICU scenario and inspect truthful, typed, migration-backed patient and vital contracts.
**Mode**: mvp
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, VITAL-01, VITAL-02, VITAL-03, SAFE-01
**Success Criteria** (what must be TRUE):

  1. A clean local database presents seeded P-1042 patient, admission, ICU bed, history, nurse, and prototype configuration data.
  2. An authorized viewer can see P-1042's bed, required current vitals, timestamp, and freshness state, with synthetic provenance visible at the point of monitoring.
  3. Automatic refresh produces deterministic scenario updates approximately every 5–10 seconds, while manual refresh and supported interval settings remain usable.
  4. Monitoring and prediction-related surfaces identify the system as a simulated ICU research prototype and do not present the feed as bedside truth or clinical advice.

**Rationale**: Safety labeling, provenance, deterministic simulation, and schema boundaries must exist before risk and alert behavior can be trusted in a demonstration.
**Plans:** 6/6 plans complete
Plans:

- [x] 01-01-PLAN.md - Backend walking skeleton, migration, and minimal P-1042 prerequisite
- [x] 01-02-PLAN.md - Full seed/reset and deterministic five-tick scenario
- [x] 01-03-PLAN.md - Typed monitoring, freshness, and interval contracts
- [x] 01-04-PLAN.md - Frontend bootstrap, typed monitoring, and safety-state presentation
- [x] 01-05-PLAN.md - Server-driven refresh controls and reusable safety presentation on the Plan 04 scaffold
- [x] 01-06-PLAN.md - Safety regression, clean-reset documentation, and full-stack smoke verification

Requirement ownership:

- DATA-01, DATA-02: 01-01
- VITAL-01, VITAL-02: 01-02
- VITAL-03, SAFE-01: 01-04
- 01-03, 01-05, and 01-06 provide dependent contract, UI, and regression expansion without claiming additional Phase 1 requirement IDs.

**UI hint**: yes

### Phase 2: Identity, Authorization, and Prediction Adapter

**Goal**: Admin, Doctor, and Nurse users can access only their permitted application behavior and receive a stable, versioned prediction contract with an explicit model or fallback source.
**Mode**: mvp
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, UI-01, PRED-01, PRED-02, PRED-03, PRED-04, ADMIN-01, ADMIN-02
**Success Criteria** (what must be TRUE):

  1. Seeded Admin, Doctor, and Nurse accounts can log in and out with JWT-backed sessions, while invalid or missing sessions cannot access protected behavior.
  2. Each role sees an appropriate dashboard and navigation, and API checks reject unauthorized role, resource, and assignment access even when a caller bypasses the UI.
  3. An authorized user can inspect P-1042's risk score, level, event, probability, horizon, current vitals, provenance, and model/rule metadata in a stable prediction shape.
  4. The prediction result clearly identifies the existing ML pipeline when available or a deterministic fallback when unavailable, without conflating either with validated clinical output.
  5. An Admin can change prototype thresholds, refresh settings, and research configuration and inspect the operational KPIs and controls available to that role.

**Rationale**: Identity and server-side policy are prerequisites for meaningful role-specific views, while the prediction adapter supplies the stable input to every later workflow.
**Plans:** 8/8 plans executed
Plans:

- [x] 02-01-PLAN.md - Migration-backed seeded identity, JWT sessions, and reset/reseed foundation
- [x] 02-02-PLAN.md - Server authorization matrix, UI bypass protection, and frontend session guard
- [x] 02-03-PLAN.md - Stable prediction adapter, deterministic fallback, and Clinical Prognosticator
- [x] 02-07-PLAN.md - Admin repository and typed configuration persistence expansion
- [x] 02-04-PLAN.md - Admin management, typed configuration, and prediction wiring
- [x] 02-05-PLAN.md - Typed Admin KPI read model and dashboard
- [x] 02-06-PLAN.md - Primary role dashboards and navigation composition
- [x] 02-08-PLAN.md - Phase 2 integration, secret-safe smoke, and reproducibility verification

**UI hint**: yes

### Phase 3: Monitoring, Alerts, Lifecycle, and Audit

**Goal**: A P-1042 deterioration produces an honest, prioritized, deduplicated alert that can be recovered after realtime disruption and reconstructed through an ordered audit trail.
**Planned:** 2026-08-24
**Mode**: mvp
**Depends on**: Phase 2
**Requirements**: ALRT-01, ALRT-02, ALRT-03, ALRT-04, ALRT-05, AUDT-01, REAL-01, REAL-02
**Success Criteria** (what must be TRUE):

  1. Crossing the configured research threshold creates one prioritized P-1042 alert containing its risk, event, probability, horizon, bed, and provenance evidence.
  2. Repeated observations in the same active deterioration episode do not create duplicate alert storms, and the configured deduplication or cooldown outcome is visible.
  3. The alert accepts only valid, authorized lifecycle transitions from generated through dispatched/assigned, acknowledged, responded, and resolved, recording actor, timestamp, state, and outcome data for each.
  4. Admin and authorized clinical users can inspect the current alert and ordered lifecycle/audit evidence, including important assignments, configuration changes, alert actions, and denied access outcomes.
  5. A disconnected, stale, loading, unavailable-fallback, or no-candidate operational state is visible, and a page reload or WebSocket reconnect recovers authoritative state through REST.

**Rationale**: The core value is a traceable deterioration-to-resolution workflow; lifecycle correctness, freshness, and audit persistence must be established before dispatch actions are layered on top.
**Plans:** 4/4 plans executed revised 2026-08-24 after checker blockers
Plans:

- [x] 03-01-PLAN.md - Threshold-backed alert persistence and deduplication
- [x] 03-02-PLAN.md - Validated alert lifecycle and ordered audit evidence
- [x] 03-03-PLAN.md - REST-authoritative realtime recovery and honest operational UI
- [x] 03-04-PLAN.md - Reset/reseed, integration proof, and secret-safe smoke verification

**UI hint**: yes

### Phase 4: Medical Historian and Human-Confirmed Dispatch

**Goal**: Doctors can understand P-1042's contextual research explanation, authorized staff can confirm an explainable nurse recommendation, and the assigned Nurse can complete the response workflow within assignment scope.
**Mode**: mvp
**Depends on**: Phase 3
**Requirements**: HIST-01, HIST-02, HIST-03, HIST-04, HIST-05, DISP-01, DISP-02, DISP-03, DISP-04, DISP-05, NURS-01, NURS-02, NURS-03
**Success Criteria** (what must be TRUE):

  1. A Doctor can review P-1042 demographics, admission, diagnoses, medications, labs, previous ICU events, current prediction, alert evidence, notes, and a chronological journey timeline without Admin controls or Nurse-only mutations.
  2. The Medical Historian separates baseline and contextual risk, lists the patient facts and configurable research-rule deltas used, and labels the explanation as prototype output rather than validated clinical weighting.
  3. The dispatcher excludes ineligible nurses, shows fresh eligibility reasons and alternatives, and ranks eligible candidates using availability 40%, proximity 30%, workload 20%, and acuity compatibility 10%.
  4. An authorized Admin or Doctor can explicitly confirm or override a recommendation, or record that no eligible nurse exists, without an autonomous assignment being created.
  5. The assigned Nurse can see only assigned work, then acknowledge the alert, record a response note, and resolve it; an unassigned Nurse cannot mutate or inspect outside the permitted assignment scope.

**Rationale**: Historian context and dispatch require stable predictions and alert acuity; human confirmation and assignment-scoped nurse actions preserve the project's non-autonomous safety boundary.
**Plans**: TBD
**UI hint**: yes

### Phase 5: End-to-End Verification and Demo Hardening

**Goal**: A developer can reset a clean SQLite environment and demonstrate the complete P-1042 journey with automated evidence for permissions, fallback behavior, lifecycle integrity, recovery, and honest presentation.
**Mode**: mvp
**Depends on**: Phase 4
**Requirements**: TEST-01, TEST-02
**Success Criteria** (what must be TRUE):

  1. Automated backend, frontend, and browser checks cover login, role/resource authorization, synthetic updates, prediction fallback, alert threshold/deduplication, lifecycle actions, historian retrieval, dispatch ranking, nurse actions, and audit recording.
  2. A documented clean local setup, migration, seed, and reset path reproduces P-1042 deterioration through prediction, alert, human-confirmed dispatch, acknowledgement, response, and resolution.
  3. Verification demonstrates REST recovery after WebSocket disconnect or reload and visibly preserves stale, synthetic, fallback, denied, and no-candidate states.
  4. A final content and workflow review confirms that the demo proves integration and traceability only, with no clinical diagnosis, treatment advice, validated-risk claim, or autonomous staffing command.

**Rationale**: The prototype earns credibility through reproducible workflow evidence and explicit degraded-state behavior, not through demo polish or implied model validation.
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Safety, Simulation, and Backend Contracts | 6/6 | Complete    | 2026-08-24 |
| 2. Identity, Authorization, and Prediction Adapter | 8/8 | Executed with verification blockers | 2026-08-24 |
| 3. Monitoring, Alerts, Lifecycle, and Audit | 4/4 | Complete | 2026-08-24 |
| 4. Medical Historian and Human-Confirmed Dispatch | 0/TBD | Not started | - |
| 5. End-to-End Verification and Demo Hardening | 0/TBD | Not started | - |

## Coverage Summary

All 40 v1 requirements map to exactly one phase. No v1 requirement is orphaned or duplicated.

| Phase | Requirement count |
|-------|-------------------:|
| Phase 1 | 6 |
| Phase 2 | 11 |
| Phase 3 | 8 |
| Phase 4 | 13 |
| Phase 5 | 2 |
| **Total** | **40** |
