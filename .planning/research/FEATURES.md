# Feature Landscape

**Domain:** ICU monitoring, predictive triage, clinical context, and nurse dispatch research prototype
**Project:** AcuityNet
**Researched:** 2026-08-24
**Scope anchor:** End-to-end synthetic P-1042 demonstration from deterioration through nurse response and resolution

## Product Boundary

AcuityNet v1 should demonstrate a coherent research workflow, not simulate a production clinical information system. All patient observations are synthetic or retrospective research/training data, all risk adjustments are configurable research rules, and all predictions and dispatch recommendations are decision-support demonstrations rather than clinical recommendations. The only supported roles are **Admin**, **Doctor**, and **Nurse**.

The smallest credible v1 is a vertical slice: a seeded P-1042 patient produces changing synthetic vitals, a prediction crosses a configurable threshold, contextual rules explain the adjusted risk, a transparent dispatcher recommends an eligible nurse, and that nurse acknowledges, responds to, and resolves the alert. Every meaningful transition must remain visible in the audit trail.

## Table Stakes

These features are required for the prototype to feel complete and for the P-1042 story to be demonstrable. Complexity includes the UI, API, persistence, and role checks needed for the behavior.

| Feature | Role(s) | Complexity | Dependencies | V1 behavior and acceptance boundary |
|---|---|---:|---|---|
| Seeded JWT login and role enforcement | Admin, Doctor, Nurse | Medium | User model, API authorization, seeded data | Demonstration accounts authenticate; backend authorization enforces role permissions rather than relying on hidden navigation. Exactly three roles exist. OAuth, SSO, and enterprise identity are deferred. |
| Role-appropriate dashboards | All | Medium | Authentication, patient/bed/nurse/alert data | Admin sees operational controls and audit data; Doctor sees read-oriented patient context and alert evidence; Nurse sees assigned patients and actionable alerts. Avoid a single unrestricted hospital dashboard. |
| Synthetic live vital stream | All | Medium | Patient/admission seed data, WebSocket or polling channel | P-1042 vitals visibly update about every 5-10 seconds, with manual refresh and configurable automatic refresh. The UI labels the feed as simulated. Device integration is out of scope. |
| Patient and bed monitoring view | All, filtered by role | Medium | Patients, admissions, beds, vitals | Show P-1042 identity, bed, current vitals, timestamp/freshness, and monitoring status. Nurse access remains assignment-scoped; Doctor access remains permission-scoped. |
| Stable baseline prediction contract | All; Admin configures | High | Vital stream, prediction adapter, deterministic fallback | Expose risk score, risk level, predicted event, probability, horizon, current vitals, and prediction timestamp. A deterministic fallback keeps the demo reproducible when the ML pipeline is unavailable. No validated clinical score is claimed. |
| Configurable threshold alert generation | Admin configures; Doctor/Nurse consume | Medium | Prediction contract, configuration, alert persistence | Crossing a configured research threshold creates a prioritized alert without duplicate alert storms for the same event. Thresholds are configuration values, not hard-coded medical advice. |
| Complete alert lifecycle | Doctor, Nurse, Admin | Medium | Alert persistence, assignment, audit log | Preserve ordered states at minimum: generated, dispatched/assigned, acknowledged, responded, and resolved. Store actor and timestamps for each transition; reject unauthorized or invalid transitions. |
| Medical context and explanation | Doctor reviews; Admin configures | High | Patient history, clinical notes, baseline prediction, configurable rules | Display relevant patient history/context and show which research rules changed the baseline risk and by how much. Label adjustments as prototype explanations, never as validated clinical weights. |
| Transparent nurse recommendation | Admin and Doctor inspect; Nurse receives assignment | High | Nurse availability, location/proximity, workload, acuity compatibility, alert acuity | Filter unavailable nurses, rank eligible candidates using the stated weighted score (availability 40%, proximity 30%, workload 20%, acuity compatibility 10%), and show the reason/evidence behind the recommendation. It is a recommendation, not autonomous staffing. |
| Nurse assignment workflow | Nurse acts; Admin/Doctor inspect | Medium | Dispatcher, users, alerts, audit log | Assign or accept the recommended nurse for P-1042, expose the assignment to that Nurse, and keep assignment changes auditable. Include an explicit unavailable/busy exclusion state. |
| Nurse response actions | Nurse | Medium | Assigned alert, lifecycle rules, authentication | The assigned Nurse can acknowledge the alert, mark that a response occurred, add a concise response note if supported by the data model, and resolve the assigned work. Other nurses cannot mutate it. |
| Doctor clinical review | Doctor | Medium | Patient context, predictions, alerts, clinical notes, authorization | Doctor can inspect history, current prediction, alert evidence, explanation, and notes without gaining Admin controls or Nurse-only state mutations. The view should support review of the P-1042 timeline. |
| Admin operations and configuration | Admin | High | Users, nurses, beds, thresholds, refresh settings, audit log | Admin can manage seeded users/nurse availability, beds, research thresholds, refresh settings, and inspect audit events. Keep edits bounded to prototype configuration; no hospital-wide provisioning is needed. |
| Auditable system actions | All, viewed by Admin | Medium | Authenticated actor identity, lifecycle events | Persist alert transitions and important actions such as assignment, configuration change, and login-relevant security events with actor, action, target, timestamp, and outcome. Provide an Admin-readable ordered view. |
| Research and simulation labeling | All | Low | Shared UI shell and data metadata | Clearly identify simulated vitals, retrospective MIMIC-IV material when used, configurable research rules, and non-clinical prototype status at the points where users could mistake output for bedside truth. |

## Differentiators

These make the prototype compelling beyond a static alert dashboard. The first three are recommended for v1 because they directly strengthen the P-1042 demonstration; the remainder should follow only after the vertical slice is reliable.

| Feature | Complexity | Dependencies | Recommendation |
|---|---:|---|---|
| Explainable risk progression | Medium | Synthetic scenario controls, prediction history, historian rules | **Include in v1.** Show baseline risk, contextual adjustment, and the resulting level over time so the mentor can understand why the alert occurred rather than seeing a mysterious score. |
| Explainable dispatch ranking | Medium | Dispatcher score components and nurse state | **Include in v1.** Show eligible candidates and component scores or concise reasons for the recommendation. This is more valuable for research review than opaque optimization. |
| Single coherent patient timeline | Medium | Vitals, predictions, context, alert events, assignment, audit log | **Include in v1.** Combine the P-1042 deterioration, prediction, dispatch, acknowledgement, response, and resolution into one chronological view or clearly linked views. |
| Scenario controls for repeatable deterioration | Medium | Synthetic vital generator, seeded patient state | Defer until the basic stream is proven, then add Admin-only start/reset controls. A resettable scenario is useful for demos but must not be confused with clinical simulation validation. |
| Historical prediction and alert playback | High | Time-series persistence, timeline UI | Defer. It improves analysis but is not required to prove the live alert lifecycle. |
| Multiple simultaneous high-acuity patients | High | More scenario data, alert prioritization, dispatcher contention | Defer. Add only after P-1042 works; it expands concurrency and triage behavior substantially. |
| Dispatcher what-if comparison | High | Stable scoring model, scenario editing | Defer. Useful for research experiments, but it risks turning v1 into a staffing optimizer. |
| MIMIC-IV cohort exploration | High | Dataset ingestion, de-identification/legal review, research UX | Defer. Keep MIMIC-IV retrospective and separate from live synthetic streams; it is not needed for the end-to-end demo. |
| Model comparison, calibration, and drift views | High | Multiple models, evaluation data, metrics pipeline | Defer. A deterministic fallback plus stable adapter is sufficient for v1 reliability; no clinical performance claim should be implied. |

## Anti-Features

These should be explicitly excluded from v1. They either violate the research/non-clinical boundary, exceed the three-role requirement, or add complexity without improving the P-1042 proof.

| Anti-feature | Why avoid it | V1 alternative |
|---|---|---|
| Live bedside device integration | Requires vendor protocols, connectivity, safety controls, and operational validation; it would falsely imply deployment readiness. | Use clearly labeled synthetic vitals with a stable stream contract. |
| Clinical diagnosis or treatment recommendations | Risk score and predicted event are research outputs, not medical advice; treatment guidance creates unacceptable clinical claims. | Show risk, evidence, uncertainty/probability, horizon, and prototype explanations only. |
| Validated clinical risk weights or hidden hard-coded thresholds | The prototype has no validation basis and opaque weights undermine research interpretation. | Make thresholds and rule adjustments configurable, visible, and labeled as research configuration. |
| Autonomous nurse dispatch or automatic escalation to a real person | Staffing decisions need human and institutional context; automation would overstate the dispatcher’s authority. | Recommend a nurse with transparent ranking and require authenticated workflow actions. |
| More than Admin, Doctor, and Nurse | Extra roles create authorization and navigation scope that the project explicitly excludes. | Model needed permissions within the three roles. |
| Unrestricted cross-hospital or cross-role data access | Violates least privilege and makes the role demonstration meaningless. | Enforce API-level scopes: Nurse assignment view, Doctor review, Admin operations. |
| Global optimal assignment/Hungarian optimization in v1 | It adds algorithmic complexity and makes recommendations harder to explain without helping the single-patient demo. | Use transparent weighted ranking with availability, proximity, workload, and acuity compatibility. |
| Production multi-hospital tenancy | Adds tenant isolation, billing/configuration, and deployment concerns unrelated to the research prototype. | Keep one SQLite-first demonstration environment behind SQLAlchemy boundaries. |
| Native mobile apps | Duplicates UI and release work while v1 is explicitly a web application. | Make the web workflow usable at the target desktop demonstration size; defer responsive/mobile productization. |
| Treating MIMIC-IV as real-time bedside data | Retrospective data cannot support the live monitoring story and misrepresents its provenance. | Keep retrospective research data separate and labeled, if used at all. |
| Alert fatigue features before the lifecycle works | Batching, suppression, and complex escalation can hide whether the core alert was handled correctly. | First prevent duplicate generation and make every state transition auditable; study advanced fatigue controls later. |

## Feature Dependencies

```text
Seeded users + JWT authentication
  -> API role enforcement
  -> role-appropriate dashboards

Seeded P-1042 patient/admission/bed
  -> synthetic vitals
  -> baseline prediction contract
  -> configurable threshold alert

Patient context + configurable research rules
  -> explained contextual risk
  -> Doctor review

Alert acuity + nurse availability/location/workload/compatibility
  -> transparent dispatcher ranking
  -> nurse assignment

Alert + authenticated actor + assignment
  -> generated -> dispatched -> acknowledged -> responded -> resolved
  -> ordered audit trail

Prediction history + alert events + assignment events
  -> coherent P-1042 timeline
```

## MVP Recommendation

Prioritize these capabilities in order:

1. Seeded authentication, exact three-role authorization, and role-specific views.
2. P-1042 seed data with labeled synthetic vitals and a repeatable live update mechanism.
3. Stable prediction payload with deterministic fallback and visible risk fields.
4. Configurable threshold alert generation with duplicate prevention and persisted lifecycle.
5. Patient context and explicitly labeled research-rule explanation.
6. Transparent nurse ranking, assignment, and Nurse acknowledgement/response/resolution.
7. Admin configuration and an ordered audit view that proves the full flow.
8. Explainable risk/dispatch evidence and a linked P-1042 timeline to make the demo persuasive.

Defer multi-patient concurrency, historical playback, model evaluation, cohort exploration, advanced alert fatigue logic, global dispatch optimization, integrations, mobile clients, and production identity/tenancy. These are valuable research directions only after the single-patient workflow is reliable and testable.

## Research Gaps

- The user PRD referenced by the research request was not present in the workspace or available in the conversation context beyond the project brief. Exact P-1042 thresholds, predicted event wording, note fields, and UI acceptance criteria therefore remain to be confirmed before phase planning.
- The project brief does not define whether dispatch is automatically assigned or requires an Admin/Doctor confirmation. V1 should default to explicit confirmation or assignment with an auditable actor until the PRD decides otherwise.
- The brief does not define retention, correction, or deletion behavior for audit events. For the prototype, append-only lifecycle events are the least ambiguous behavior; production retention policy requires separate research.

## Sources

- [AcuityNet project brief](../PROJECT.md) - authoritative project scope, active requirements, constraints, and out-of-scope decisions; HIGH confidence for project-specific feature boundaries.
- User-provided research scope in the current request - P-1042 end-to-end demo anchor and exactly-three-role constraint; HIGH confidence for requested research scope.
