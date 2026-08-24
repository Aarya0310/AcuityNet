# Domain Pitfalls

**Domain:** ICU predictive monitoring and nurse dispatch research prototype
**Project:** AcuityNet
**Researched:** 2026-08-24
**Overall confidence:** MEDIUM

AcuityNet should be judged as a research demonstration, not as a bedside clinical system. The most dangerous failures are presentation and workflow failures that make simulated predictions look validated, retrospective data look live, or recommendations look like orders. The controls below are therefore product requirements for truthful demonstration, not claims of regulatory compliance or clinical safety.

## Critical Pitfalls

### 1. Clinical claims hidden inside a convincing dashboard

**What goes wrong:** Risk scores, event labels, probability, horizon, and contextual adjustments are displayed with clinical-sounding precision. Viewers infer that the model is validated, calibrated, or appropriate for treatment decisions even though the weights are configurable research rules and the feed is synthetic.

**Warning signs:** Terms such as “diagnosis,” “recommended intervention,” “safe,” or “will deteriorate”; unexplained probability semantics; a green/red clinical visual language without a persistent prototype disclaimer; no visible intended-use statement; demo narration that treats a score as a fact.

**Prevention:** Put a persistent “simulated ICU / research prototype / not for clinical use” label on every monitoring and alert surface. Describe outputs as baseline risk signals and research-rule explanations. Display model version, rule-set version, input timestamp, data provenance, and explicit limitations beside the result. Keep treatment decisions and clinical orders out of scope. Add a content review gate before each demo release.

**Roadmap phase:** Phase 1, Safety framing and data contracts; revisit in the UX/demo hardening phase.

**Confidence:** MEDIUM. FDA’s January 2026 Clinical Decision Support Software guidance says the intended function and information supplied to a clinician matter when distinguishing non-device CDS from device software; AcuityNet should not imply a clinical intended use merely through UI language. Source: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software

### 2. Retrospective data presented as a live bedside feed

**What goes wrong:** MIMIC-IV examples, replayed records, or charts are shown beside streaming vitals without clear separation. A viewer cannot tell whether a value is synthetic, historical, replayed, or current, and may assume the model was evaluated prospectively.

**Warning signs:** “Live” or “real-time” labels on MIMIC-derived content; missing source and event-time metadata; a replay that advances without saying it is a replay; historical data used to claim alert latency or bedside performance; patient identifiers that look operational.

**Prevention:** Make provenance a required field in every feed and prediction payload: `synthetic`, `retrospective`, or `replay`, plus source, generated/event time, and demo scenario ID. Use visibly different UI treatments for synthetic streams and retrospective research context. Keep MIMIC-IV in a training/context lane only. Add tests that reject a retrospective source in the live-vitals endpoint and a demo checklist that verifies the P-1042 scenario is synthetic.

**Roadmap phase:** Phase 1, Data provenance and simulation; Phase 2, prediction integration.

**Confidence:** MEDIUM. MIT’s MIMIC documentation identifies the hosp and icu modules as MIMIC-IV data made available through PhysioNet; the project brief separately requires that it remain retrospective research/training data. Source: https://mimic.mit.edu/docs/iv/modules/

### 3. Alert fatigue from threshold-driven noise

**What goes wrong:** Every threshold crossing creates an alert, repeated samples create duplicates, and low-value alerts compete with urgent deterioration. Users learn to dismiss the system or stop trusting priority levels.

**Warning signs:** Alert storms during a normal simulated fluctuation; duplicate alerts for one episode; no hysteresis, cooldown, deduplication, escalation, or suppression behavior; every alert rendered with the same visual urgency; acknowledgement treated as proof that the patient was assessed.

**Prevention:** Model an alert as an episode with deduplication and explicit states (`generated`, `acknowledged`, `responded`, `resolved`, and where needed `expired` or `suppressed`). Make thresholds and cooldowns configurable demo settings, not clinical recommendations. Show why an alert fired and what changed since the prior evaluation. Track alert counts, duplicate rate, acknowledgement latency, response latency, and resolution latency in the demo. Never silently suppress an alert; record the reason and actor/system version.

**Roadmap phase:** Phase 3, Alert lifecycle and human workflow; Phase 5, evaluation and demo hardening.

**Confidence:** MEDIUM. Alarm-fatigue prevention is an established patient-safety concern, but the AHRQ and Joint Commission pages could not be extracted reliably in this run; treat this as a well-supported safety principle requiring later phase-specific verification.

### 4. Weak RBAC hidden behind navigation

**What goes wrong:** The UI hides screens but APIs accept any authenticated user’s patient, alert, note, user-management, or dispatch requests. A Nurse can query the hospital, a Doctor can mutate operational configuration, or a user can act on another nurse’s assignment.

**Warning signs:** Authorization checks only in React routes; object IDs accepted without ownership or role checks; one broad “authenticated” dependency; predictable seeded credentials exposed outside the demo; audit logs that omit denied requests or the acting user.

**Prevention:** Enforce role and resource authorization in FastAPI dependencies and service-layer checks, with exactly Admin, Doctor, and Nurse roles. Define a permission matrix before endpoint implementation: nurses see assigned work, doctors have read-oriented clinical access, and admins manage operations/configuration. Test both allowed and denied API calls, including cross-patient and cross-assignment access. Use non-production seeded accounts, short-lived JWTs, password hashing, and an obvious demo-only environment warning.

**Roadmap phase:** Phase 2, Authentication and authorization, before role dashboards.

**Confidence:** MEDIUM. HHS describes role-appropriate access, authentication, audit controls, and mechanisms to record/examine activity as technical safeguards under the HIPAA Security Rule. AcuityNet is not thereby HIPAA-compliant, but these are appropriate prototype control patterns. Source: https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html

### 5. Dispatch recommendation treated as an assignment or clinical command

**What goes wrong:** A weighted ranking silently assigns a nurse based on stale availability, approximate location, workload, or acuity compatibility. The UI makes the top candidate appear authoritative and ignores breaks, skill constraints, isolation requirements, emergencies, or local staffing policy.

**Warning signs:** “Dispatch” or “assigned” appears before human confirmation; no timestamp for nurse availability; no reason codes for ranking; unavailable or overloaded staff appear as candidates; no alternative candidate or “no safe recommendation” outcome; a recommendation changes without an audit event.

**Prevention:** Label the output “research recommendation.” Filter hard constraints before scoring, show the four configured score components and their timestamps, and permit a Doctor/Admin-confirmed assignment rather than automatic dispatch. Return “no eligible candidate” when constraints fail. Show stale-data warnings, alternatives, and an override path. Audit the candidate set, score inputs, recommendation, confirmer, override reason, and resulting assignment separately. Do not infer that a nurse’s workload score establishes safe staffing.

**Roadmap phase:** Phase 4, Transparent tactical dispatcher; Phase 3, alert-to-assignment workflow.

**Confidence:** MEDIUM. This is primarily a human-factors and operational-safety inference from the project’s stated weighted-ranking design; it requires local workflow validation before any real-world use.

### 6. Non-reproducible synthetic deterioration

**What goes wrong:** The P-1042 demo depends on wall-clock timing, uncontrolled randomness, browser state, or a mutable seed. A mentor cannot reproduce the same deterioration, score, alert, dispatch result, and resolution, making failures impossible to compare.

**Warning signs:** Different results after refresh; no scenario ID or random seed; client-side generation that diverges between users; missing simulator clock; tests that sleep for real time; prediction values that cannot be regenerated from stored inputs.

**Prevention:** Make simulation deterministic by scenario ID and seed, with an explicit simulator clock and controllable tick/advance operation. Persist generated vitals or the generation parameters used for each event. Include scenario, seed, feed version, model/rule version, and timestamps in prediction and alert records. Provide a reset-to-baseline control that creates an auditable reset event. Test the canonical P-1042 journey from a clean database.

**Roadmap phase:** Phase 1, Simulation and reproducibility; Phase 5, end-to-end verification.

**Confidence:** MEDIUM. The exact controls are AcuityNet engineering recommendations derived from its reproducibility requirement; they are not a claim that a specific external standard mandates this implementation.

### 7. Un-auditable alert lifecycle

**What goes wrong:** The current alert row is overwritten as users act. The system cannot establish which score generated it, who acknowledged it, whether a response preceded resolution, or which configuration/model was active at the time.

**Warning signs:** `status` changes without an append-only event record; timestamps are client supplied; audit entries lack actor, target, previous/new state, reason, or correlation ID; deleted alerts disappear from history; WebSocket events are treated as the source of truth.

**Prevention:** Persist an append-only alert event stream with server timestamps, actor or system identity, transition validation, previous and new state, reason, source prediction ID, assignment ID, model/rule/config versions, and correlation ID. Keep the current projection for fast reads, but reconstruct the lifecycle from events in tests and an admin audit view. Make terminal states immutable except through a documented correction event. Include denied actions and configuration changes in the audit trail.

**Roadmap phase:** Phase 3, Alert lifecycle and audit foundation; Phase 5, audit verification.

**Confidence:** MEDIUM. HHS explicitly describes audit controls and access/activity review; the append-only event design is the project’s recommended implementation of traceability. Source: https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html

### 8. Model fallback ambiguity

**What goes wrong:** The existing ML pipeline fails or is unavailable, but the UI presents the deterministic fallback as if it were the trained model. Conversely, a fallback may produce a different payload shape or threshold behavior and silently break the workflow.

**Warning signs:** No `model_source` or fallback reason; identical branding for ML and rules; no model artifact/version; fallback activated by broad exception handling; prediction confidence shown without semantics; demo passes only when a developer machine has an optional model installed.

**Prevention:** Use a typed prediction adapter with a stable contract and explicit sources such as `ml_pipeline` and `deterministic_fallback`. Return model/rule version, input schema version, fallback reason category, and an honest explanation. Do not silently catch all exceptions; log the failure and expose a non-clinical degraded-mode banner. Keep fallback thresholds and output semantics testable and separate from ML calibration. Include both paths in CI and the canonical demo.

**Roadmap phase:** Phase 2, Prediction adapter contract; Phase 5, failure-mode verification.

**Confidence:** MEDIUM. This is an AcuityNet-specific reliability and honesty requirement based on the project decision to use a deterministic fallback.

## Moderate Pitfalls

### Configuration drift disguised as clinical tuning

**What goes wrong:** An admin changes thresholds, refresh interval, dispatcher weights, or historian rules and later results cannot be explained.

**Warning signs:** Mutable settings without versioning; no effective timestamp; UI calls values “recommended”; old alerts are reinterpreted using current settings.

**Prevention:** Version configuration sets, record who changed them and why, attach the active version to every prediction/alert, and distinguish research configuration from clinical guidance. Provide resettable demo defaults.

**Roadmap phase:** Phase 2, Configuration and prediction contracts; Phase 5, audit review.

### Stale or partial feeds mistaken for stability

**What goes wrong:** A WebSocket disconnect, delayed tick, missing vital, or browser suspension leaves a reassuringly unchanged chart and score.

**Warning signs:** No last-seen age; flatline data without warning; prediction continues after feed loss; reconnect duplicates samples; no degraded state.

**Prevention:** Show feed freshness and connection state, distinguish “no new data” from stable vitals, require complete input metadata for prediction, and record feed gaps. Pause or mark predictions stale after a configured demo timeout.

**Roadmap phase:** Phase 1, Simulation transport; Phase 3, monitoring and alerts.

### Privacy and workforce-data overexposure

**What goes wrong:** Demo data includes unnecessary identifiers or exposes nurse location, workload, notes, or availability to roles that do not need them.

**Warning signs:** Full names and free-text notes in fixtures; bulk endpoints return all nurses/patients; logs contain tokens or sensitive payloads; no data retention/reset plan.

**Prevention:** Use synthetic identities, minimum-necessary fields, scoped queries, redacted logs, and a reset script. Treat nurse availability and workload as sensitive operational data. Document that a local research prototype is not approved for real PHI.

**Roadmap phase:** Phase 2, RBAC and seeded data; Phase 5, security review.

**Confidence:** MEDIUM. HHS requires role-appropriate access and risk management for regulated entities; NIST describes its Privacy Framework as a voluntary tool for identifying and managing privacy risk. Sources: https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html and https://www.nist.gov/privacy-framework

## Minor Pitfalls

### Demo theater overstates validation

**What goes wrong:** A polished P-1042 walkthrough is mistaken for evidence of sensitivity, specificity, calibration, fairness, or clinical utility.

**Prevention:** Separate workflow success metrics from model evaluation metrics. State that the demo validates integration and traceability only. Keep a research evaluation backlog for retrospective validation, cohort definition, calibration, subgroup analysis, and prospective study design.

**Roadmap phase:** Phase 5, Evaluation and demo hardening.

### Accessibility and urgency cues are too dependent on color or motion

**What goes wrong:** Alert level, assignment state, or stale-feed status is missed by users with visual, cognitive, or motion sensitivities.

**Prevention:** Pair color with text and icons, preserve keyboard access, provide stable status text, and avoid flashing or auto-advancing urgent UI. Test at desktop and mobile widths even though mobile native apps are out of scope.

**Roadmap phase:** Phase 3, Alert workflow UI; Phase 5, usability verification.

## Phase-Specific Warnings

| Roadmap phase | Likely pitfall | Required mitigation |
|---|---|---|
| Phase 1: Safety framing, synthetic data, and contracts | Live/retrospective confusion; misleading claims; irreproducible simulation | Provenance fields, persistent labels, scenario seed/clock, canonical synthetic P-1042 scenario, non-clinical terminology |
| Phase 2: Auth, RBAC, and prediction adapter | UI-only authorization; fallback ambiguity; configuration drift | Server-side permission matrix, denied-path tests, typed adapter, explicit model source and versions, configuration audit |
| Phase 3: Monitoring, alerts, and lifecycle | Alert fatigue; stale feed; overwritten history | Deduplication/cooldown, freshness state, valid transitions, append-only lifecycle events, latency metrics |
| Phase 4: Medical Historian and transparent dispatcher | Research rules look clinical; dispatch looks authoritative | Explainable rule deltas, recommendation language, hard eligibility filters, human confirmation, no-candidate state, override audit |
| Phase 5: End-to-end verification and demo hardening | Demo theater; untested degraded paths; privacy leakage | Clean-reset reproducibility test, ML and fallback paths, RBAC matrix tests, audit reconstruction, content/privacy review, workflow-vs-model claims separation |

## Sources

- FDA, **Clinical Decision Support Software**, January 2026: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- HHS OCR, **Summary of the HIPAA Security Rule**: https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html
- MIT Laboratory for Computational Physiology, **MIMIC-IV modules**: https://mimic.mit.edu/docs/iv/modules/
- NIST, **Privacy Framework**: https://www.nist.gov/privacy-framework
- AHRQ PSNet, **Alarm Fatigue**: https://psnet.ahrq.gov/primer/alarm-fatigue (page extraction unavailable during research; follow-up verification recommended)
- AHRQ PSNet, **Human Factors**: https://psnet.ahrq.gov/primer/human-factors (page extraction unavailable during research; follow-up verification recommended)
- Joint Commission, **Alarm Management**: https://www.jointcommission.org/resources/patient-safety-topics/alarm-management/ (page extraction unavailable during research; follow-up verification recommended)

## Research Gaps

- Validate the alert-fatigue recommendations against current AHRQ/Joint Commission material during Phase 3 planning.
- Decide whether AcuityNet will ever handle real PHI; if so, perform a formal threat model and legal/compliance review rather than treating this prototype artifact as compliance evidence.
- Define the intended evaluation target for the prediction engine before discussing accuracy, calibration, fairness, or clinical utility.
- Validate dispatcher constraints and override policy with an ICU nursing workflow subject-matter expert before presenting recommendations to real users.
