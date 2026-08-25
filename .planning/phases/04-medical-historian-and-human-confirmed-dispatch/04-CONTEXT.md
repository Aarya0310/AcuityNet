# Phase 4: Medical Historian and Human-Confirmed Dispatch - Context

**Gathered:** 2026-08-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the P-1042 Medical Historian and Tactical Dispatcher workflow on top of the completed Phase 2 identity/prediction contracts and Phase 3 alert lifecycle/audit contracts. Doctors must be able to inspect patient context and a clearly non-clinical contextual-risk explanation; authorized Admins and Doctors must be able to review and human-confirm a transparent nurse recommendation; and the assigned Nurse must complete the existing assigned-alert response lifecycle within assignment scope.

This phase does not add new roles, autonomous staffing, clinical diagnosis/treatment advice, global optimization, live device integration, or retrospective MIMIC-IV runtime feeds.

</domain>

<decisions>
## Implementation Decisions

### Medical Historian Explanation
- **D-01:** Use an evidence timeline as the primary contextual-risk presentation, showing baseline score, patient facts, named research-rule deltas, and contextual score as a chronological evidence chain.
- **D-02:** Allow all seeded context categories, including diagnoses, medications, labs, and previous ICU events, to contribute through named configurable research rules.
- **D-03:** Doctors can add annotations, but annotations do not edit rules or alter computed scores. — **Reversibility:** costly — rationale: changing annotation semantics later would affect clinical-note persistence, timeline projections, and audit behavior.
- **D-04:** When context is incomplete, show baseline risk only, mark contextual risk unavailable, and identify the missing evidence rather than fabricating a partial score.
- **D-05:** Put rule mechanics in an expandable research-mode panel that shows each rule name, configurable delta, and rule version alongside an explicit non-clinical disclaimer.
- **D-06:** Attach Doctor annotations to the P-1042 patient timeline as timestamped entries with audit evidence.
- **D-07:** Show the complete seeded record without pagination in the first historian view.

### Dispatch Confirmation
- **D-08:** Both Admin and Doctor may confirm or override a nurse recommendation; Nurse users receive and act on the resulting assignment but do not commit staffing decisions.
- **D-09:** Confirmation and override require a reason plus an evidence snapshot containing actor, selected nurse, score breakdown, freshness, and the recommendation context.
- **D-10:** Present dispatch candidates as a ranked comparison with the recommended nurse first, alternatives afterward, component scores, eligibility reasons, workload, and distance.
- **D-11:** Require a fresh candidate/alert evidence snapshot before confirmation. If status, workload, or alert evidence is stale, block confirmation and require recomputation.

### Nurse Workflow
- **D-12:** Use an action-first assigned-alert view: risk, predicted event, latest vitals, bed, and acknowledgement action first, with relevant context expandable below.
- **D-13:** Require concise notes for response and resolution; acknowledgement remains a quick action without a note requirement.
- **D-14:** Show the assigned Nurse minimal relevant clinical context: current vitals, prediction evidence, key diagnoses, and prior events, not the complete Doctor historian record.
- **D-15:** Keep the Nurse on the patient timeline after response or resolution so the new state and audit entry are immediately visible.

### No Eligible Nurse
- **D-16:** Represent no eligible nurse as a blocked assignment presentation while leaving the alert in `generated` and unassigned state.
- **D-17:** Show why every candidate was excluded and offer a human-triggered status refresh/recompute; never fabricate an assignment or auto-escalate it.
- **D-18:** Record a full exclusion snapshot with timestamp, alert evidence freshness, every candidate exclusion reason, and the retry actor.

### the agent's Discretion
- Exact visual styling, route/component names, API module decomposition, and persistence implementation details remain open to the standard patterns already established in the repository.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project scope and requirements
- `.planning/PROJECT.md` — product boundary, exactly three roles, safety constraints, and core P-1042 value.
- `.planning/REQUIREMENTS.md` — Phase 4 requirements HIST-01 through HIST-05, DISP-01 through DISP-05, and NURS-01 through NURS-03.
- `.planning/ROADMAP.md` — Phase 4 goal, dependencies, and observable success criteria.
- `.planning/STATE.md` — current project position and accumulated Phase 1–3 decisions.

### Existing backend contracts
- `backend/app/persistence/models.py` — current User, Nurse, Patient, Alert, AlertEvent, AuditEvent, and PredictionEvidence persistence shape.
- `backend/app/auth/policy.py` — server-side role, patient-access, and Nurse assignment policy.
- `backend/app/alerts/lifecycle.py` — existing generated-to-resolved lifecycle, assignment evidence, note requirements, and role restrictions.
- `backend/app/audit/service.py` — append-only audit recording and denied-action recording.
- `backend/app/main.py` — application wiring, auth dependencies, prediction/alert/audit/realtime routers, and safety boundaries.

### Existing frontend integration points
- `frontend/src/App.tsx` — role routing and current dashboard composition.
- `frontend/src/api/client.ts` — authenticated REST client, prediction/alert/audit access, and realtime URL helper.
- `frontend/src/alerts/AlertPage.tsx` — current alert, lifecycle evidence, audit, and realtime presentation.
- `frontend/src/dashboards/AdminDashboardView.tsx` — Admin dashboard composition.
- `frontend/src/dashboards/DoctorDashboardView.tsx` — Doctor dashboard composition.
- `frontend/src/dashboards/NurseDashboardView.tsx` — Nurse dashboard composition.

### Prior-phase evidence
- `.planning/phases/03-monitoring-alerts-lifecycle-and-audit/03-02-SUMMARY.md` — lifecycle and assignment-evidence decisions; assignment is reconstructed from ordered audit details.
- `.planning/phases/03-monitoring-alerts-lifecycle-and-audit/03-03-SUMMARY.md` — typed operational states and REST-authoritative realtime recovery.
- `.planning/phases/03-monitoring-alerts-lifecycle-and-audit/03-04-SUMMARY.md` — reset/seed constraints and explicit Phase 4 ownership boundaries.
- `.planning/research/SUMMARY.md` — project-level architecture, feature priorities, and safety risks.

No external specs or ADRs were referenced during this discussion; project requirements and the canonical code paths above are the governing sources.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AlertLifecycleService` already enforces `generated -> assigned -> acknowledged -> responded -> resolved`, requires response/resolution notes, and stores assignment evidence in audit details.
- `AuditService` and the alert/audit repositories provide append-only ordered evidence and denial recording.
- `PredictionEvidence` already stores baseline prediction source/version, threshold, rule version, synthetic provenance, and prototype label fields that historian/dispatch views can consume.
- `App.tsx`, role dashboard components, authenticated API client, and `AlertPage` provide existing composition and transport patterns.

### Established Patterns
- REST remains authoritative for reads and mutations; realtime is additive invalidation only.
- Server-side policies enforce role/resource/assignment access; navigation visibility is not authorization.
- Audit details are structured JSON, and alert assignment is reconstructed from successful lifecycle audit evidence for compatibility with the Phase 3 schema.
- Synthetic, non-clinical prototype labeling must remain visible; explanations are research rules, not clinical weights.

### Integration Points
- Add historian and dispatcher services/routers beside existing prediction, alert, audit, and admin modules.
- Extend the shared authenticated client and role dashboards rather than creating a parallel app shell.
- Reuse the existing alert lifecycle commands for confirmation, assignment, acknowledgement, response, and resolution; add only the Phase 4 candidate/review data needed to drive them.
- Ensure Doctor/Admin confirmation and Nurse mutations pass through current auth policy and append ordered audit evidence.

</code_context>

<specifics>
## Specific Ideas

- The historian should feel like an evidence timeline, with rule mechanics available in a research-mode expandable panel.
- The dispatcher should be a ranked comparison rather than an opaque single recommendation card.
- The Nurse should land on action-first alert information and remain on the patient timeline after completing work.
- No-candidate behavior must be visibly blocked but leave the alert generated and unassigned until a human retries with fresh status data.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 4 scope.

</deferred>

---

*Phase: 4-Medical-Historian-and-Human-Confirmed-Dispatch*
*Context gathered: 2026-08-25*
