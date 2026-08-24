# Requirements: AcuityNet

**Defined:** 2026-08-24
**Core Value:** A mentor can follow one patient from deteriorating simulated vitals through contextual risk, nurse dispatch, acknowledgement, response, resolution, and an auditable record.

## v1 Requirements

### Foundation and Access

- [ ] **AUTH-01**: A seeded Admin, Doctor, or Nurse can log in with email and password and receive a JWT-backed session.
- [ ] **AUTH-02**: The system supports exactly three roles: Admin, Doctor, and Nurse; unknown or additional roles cannot access protected application behavior.
- [ ] **AUTH-03**: The API enforces role and resource permissions server-side, including patient and assignment ownership; hidden navigation alone is not treated as authorization.
- [ ] **AUTH-04**: A user can log out, and protected requests without a valid session are rejected.
- [ ] **UI-01**: Admin, Doctor, and Nurse each see role-appropriate navigation and dashboards rather than one unrestricted hospital view.
- [x] **DATA-01**: The system provides seeded P-1042 patient, ICU bed, nurse, admission, history, and configuration data for a repeatable demonstration.
- [x] **DATA-02**: The system stores and displays data provenance identifying live monitoring observations as synthetic and any MIMIC-IV material as retrospective research/training data.

### Monitoring and Prediction

- [x] **VITAL-01**: Authorized users can view P-1042's current bed, SpO2, heart rate, respiratory rate, systolic/diastolic blood pressure, temperature, timestamp, and freshness state.
- [x] **VITAL-02**: The synthetic scenario updates P-1042 vitals approximately every 5–10 seconds when automatic refresh is enabled, and the user can manually refresh or choose a supported interval.
- [x] **VITAL-03**: The monitoring UI visibly identifies the feed as simulated and represents disconnected or stale data without implying current bedside truth.
- [ ] **PRED-01**: The prediction API exposes a stable payload containing patient, bed, prediction event, probability, risk score, risk level, horizon, timestamp, provenance, and model/rule version metadata.
- [ ] **PRED-02**: The prediction adapter uses the existing ML pipeline when available and a deterministic, clearly labeled fallback when it is unavailable.
- [ ] **PRED-03**: Authorized users can view P-1042's current risk, predicted event, probability, horizon, and prediction source in the Clinical Prognosticator.
- [ ] **PRED-04**: Risk thresholds and prediction-related research configuration are editable by Admin and are presented as configurable prototype settings, not clinical recommendations.

### Alerts and Audit Lifecycle

- [ ] **ALRT-01**: A prediction crossing the configured research threshold creates a prioritized alert containing patient, bed, risk, event, probability, horizon, and provenance details.
- [ ] **ALRT-02**: The alert engine prevents duplicate alert storms for the same active deterioration episode using configurable deduplication or cooldown behavior.
- [x] **ALRT-03**: An alert follows validated lifecycle transitions from generated to dispatched/assigned, acknowledged, responded, and resolved; invalid or unauthorized transitions are rejected.
- [x] **ALRT-04**: Each alert transition records the acting user, timestamp, resulting state, and relevant outcome data.
- [x] **ALRT-05**: Admin and authorized clinical users can inspect the current alert state and ordered lifecycle evidence for P-1042.
- [x] **AUDT-01**: The system records important authenticated actions, including assignment, configuration changes, alert actions, denied access outcomes, and lifecycle transitions, in an ordered audit view.

### Medical Context and Clinical Review

- [ ] **HIST-01**: An authorized Doctor can retrieve P-1042's demographics, admission, bed, diagnoses, medications, labs, and previous ICU events.
- [ ] **HIST-02**: The Medical Historian displays baseline risk separately from contextual risk and identifies the patient context used to derive the difference.
- [ ] **HIST-03**: The Medical Historian lists each configurable research-rule adjustment with its explanation and delta, and labels the result as a prototype explanation rather than a validated clinical weight.
- [ ] **HIST-04**: A Doctor can review P-1042's current vitals, prediction, history, alert evidence, explanation, and clinical notes without receiving Admin controls or Nurse-only mutations.
- [ ] **HIST-05**: Authorized users can follow a chronological P-1042 timeline linking deterioration, predictions, contextual explanation, alert, dispatch, acknowledgement, response, and resolution.

### Tactical Dispatch and Nurse Workflow

- [ ] **DISP-01**: The dispatcher filters nurses who are offline, on break, unavailable, or otherwise ineligible before ranking candidates.
- [ ] **DISP-02**: The dispatcher ranks eligible nurses using transparent prototype weights of availability 40%, proximity 30%, workload 20%, and acuity compatibility 10%.
- [ ] **DISP-03**: Admin and Doctor users can inspect the recommended nurse, alternatives, score components, source freshness, and eligibility reasons.
- [ ] **DISP-04**: Dispatch requires an explicit authorized human confirmation or override and records that decision; it is never an autonomous staffing command.
- [ ] **DISP-05**: When no eligible nurse exists, the system displays that outcome, preserves the reason, and does not fabricate an assignment.
- [ ] **NURS-01**: The assigned Nurse can see only assigned patients and alerts, including P-1042's current risk and relevant vitals.
- [ ] **NURS-02**: The assigned Nurse can acknowledge the alert, mark a response, add a concise response note, and resolve the assigned work.
- [ ] **NURS-03**: A Nurse who is not assigned to an alert cannot mutate its lifecycle or view data outside the Nurse's permitted assignment scope.

### Administration, Reliability, and Verification

- [ ] **ADMIN-01**: Admin users can manage prototype users, nurse status, beds, refresh settings, risk thresholds, and research-rule configuration.
- [ ] **ADMIN-02**: Admin users can inspect hospital KPIs for occupancy, monitored patients, active nurses, critical/high-risk patients, alerts, predictions, response time, acknowledgement rate, and system status.
- [x] **REAL-01**: REST is authoritative for reads and mutations, while WebSockets deliver synthetic vital updates or invalidation events and reconnect/reload recovers through REST.
- [x] **REAL-02**: The application provides an honest operational state for loading, stale, disconnected, unavailable-fallback, and no-candidate conditions.
- [ ] **TEST-01**: Automated backend and frontend tests cover login, role/resource authorization, synthetic feed behavior, prediction fallback, alert generation/deduplication, lifecycle transitions, historian retrieval, dispatch ranking, nurse actions, and audit recording.
- [ ] **TEST-02**: A clean local setup using SQLite migrations and seeded data can reproduce the P-1042 journey from deterioration through resolution, including a documented demo reset or setup path.
- [x] **SAFE-01**: User-facing prediction, contextual risk, alert, and dispatch surfaces clearly state that AcuityNet is a research prototype using simulated ICU data and do not provide diagnosis or treatment advice.

## v2 Requirements

### Research Enhancements

- **RESEARCH-01**: User can compare model versions with calibration, drift, fairness, and clinical-utility evaluation views.
- **RESEARCH-02**: User can explore retrospective MIMIC-IV cohorts without mixing them into live synthetic monitoring.
- **RESEARCH-03**: User can replay historical multi-patient scenarios and analyze alert fatigue over time.

### Dispatch Enhancements

- **DISP-06**: Dispatcher can run what-if staffing comparisons or global optimization across multiple simultaneous alerts.
- **DISP-07**: System supports advanced escalation, suppression, batching, and staffing policy controls validated with domain experts.

### Platform Enhancements

- **PLAT-01**: System integrates with live bedside devices or hospital EHR systems after formal safety, privacy, and operational validation.
- **PLAT-02**: System supports enterprise identity, multi-hospital tenancy, and native mobile applications.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Clinical diagnosis or treatment recommendations | The prototype demonstrates decision-support workflow, not medical advice. |
| Live bedside device integration | Synthetic vitals are required for the current implementation and live integration would imply deployment readiness. |
| Validated clinical risk weights or claims | Thresholds and historian deltas are configurable research rules without clinical validation. |
| Autonomous nurse dispatch | Staffing recommendations require explicit human confirmation and auditability. |
| Roles beyond Admin, Doctor, and Nurse | Exactly three roles are a project constraint. |
| Hungarian/global optimization in v1 | Transparent weighted ranking is sufficient for the single-patient journey. |
| Production PHI handling and multi-hospital tenancy | The prototype uses synthetic data and a local SQLite-first environment. |

## User Stories

- **US-01**: As a mentor, I can watch P-1042 deteriorate in a simulated feed and see why the system raises an alert.
- **US-02**: As a Doctor, I can connect the prediction to patient history and review a clearly labeled contextual explanation.
- **US-03**: As a dispatcher, I can inspect eligible nurses and confirm or override a transparent recommendation.
- **US-04**: As Nurse Sarah, I can receive the assigned alert, acknowledge it, record a response, and resolve it.
- **US-05**: As an Admin, I can configure prototype thresholds and reconstruct the full workflow from audit events.

## Definition of Done

- The P-1042 journey runs from seeded setup through simulated deterioration, prediction, alert, context, human-confirmed dispatch, Nurse acknowledgement/response/resolution, and audit reconstruction.
- Backend authorization tests prove that each role can perform only permitted actions and that assignment-scoped Nurse access is enforced server-side.
- The prediction fallback, threshold behavior, alert deduplication, dispatch scoring, no-candidate path, and lifecycle transitions are deterministic and tested.
- REST recovery works after a WebSocket disconnect or page reload, and stale/synthetic/fallback states remain visible.
- SQLite migrations and seed instructions reproduce the demonstration locally.
- All relevant UI surfaces carry accurate synthetic-data, research-rule, and non-clinical prototype labeling.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 2 | Pending |
| AUTH-02 | Phase 2 | Pending |
| AUTH-03 | Phase 2 | Pending |
| AUTH-04 | Phase 2 | Pending |
| UI-01 | Phase 2 | Pending |
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| VITAL-01 | Phase 1 | Complete |
| VITAL-02 | Phase 1 | Complete |
| VITAL-03 | Phase 1 | Complete |
| PRED-01 | Phase 2 | Pending |
| PRED-02 | Phase 2 | Pending |
| PRED-03 | Phase 2 | Pending |
| PRED-04 | Phase 2 | Pending |
| ALRT-01 | Phase 3 | Pending |
| ALRT-02 | Phase 3 | Pending |
| ALRT-03 | Phase 3 | Complete |
| ALRT-04 | Phase 3 | Complete |
| ALRT-05 | Phase 3 | Complete |
| AUDT-01 | Phase 3 | Complete |
| HIST-01 | Phase 4 | Pending |
| HIST-02 | Phase 4 | Pending |
| HIST-03 | Phase 4 | Pending |
| HIST-04 | Phase 4 | Pending |
| HIST-05 | Phase 4 | Pending |
| DISP-01 | Phase 4 | Pending |
| DISP-02 | Phase 4 | Pending |
| DISP-03 | Phase 4 | Pending |
| DISP-04 | Phase 4 | Pending |
| DISP-05 | Phase 4 | Pending |
| NURS-01 | Phase 4 | Pending |
| NURS-02 | Phase 4 | Pending |
| NURS-03 | Phase 4 | Pending |
| ADMIN-01 | Phase 2 | Pending |
| ADMIN-02 | Phase 2 | Pending |
| REAL-01 | Phase 3 | Complete |
| REAL-02 | Phase 3 | Complete |
| TEST-01 | Phase 5 | Pending |
| TEST-02 | Phase 5 | Pending |
| SAFE-01 | Phase 1 | Complete |

**Coverage:**

- v1 requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0

---
*Requirements defined: 2026-08-24*
*Last updated: 2026-08-24 after initial definition*
