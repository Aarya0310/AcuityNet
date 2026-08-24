# AcuityNet

## What This Is

AcuityNet is a web-based ICU monitoring, predictive triage, and nurse dispatch research prototype. It turns synthetic vital-sign streams into a baseline risk prediction, adds patient-specific medical context, prioritizes alerts, recommends a nurse, and records the alert lifecycle for Admin, Doctor, and Nurse users.

The live dashboard uses simulated real-time vitals. MIMIC-IV is retrospective research/training data only and is not treated as a live bedside feed. The system must be presented as a simulated ICU environment and research prototype, not a clinically deployable medical device.

## Core Value

A mentor can follow one patient from deteriorating simulated vitals through contextual risk, nurse dispatch, acknowledgement, response, resolution, and an auditable record in one coherent workflow.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] The system supports exactly three roles: Admin, Doctor, and Nurse, with enforced role-based access.
- [ ] Users can authenticate with JWT-backed login using seeded demonstration accounts.
- [ ] The application provides hospital and role-appropriate dashboards for patients, beds, nurses, predictions, and alerts.
- [ ] Synthetic vital streams update patient monitoring views and feed a stable prediction API contract.
- [ ] The Clinical Prognosticator displays risk score, level, predicted event, probability, horizon, and current vitals.
- [ ] A prediction can generate a configurable-threshold risk alert with a complete lifecycle from generated through resolved.
- [ ] The Medical Historian retrieves patient context and explains configurable research-rule adjustments to baseline risk.
- [ ] The Tactical Dispatcher filters unavailable nurses, scores candidates by availability, proximity, workload, and acuity compatibility, and recommends a nurse.
- [ ] Nurses can view assigned patients and alerts, acknowledge alerts, mark responses, and resolve assigned work.
- [ ] Doctors can review patient history, predictions, alerts, explanations, and clinical notes within their permissions.
- [ ] Admins can manage users, nurses, beds, configuration, and audit logs.
- [ ] Every alert state transition and important system action is auditable.
- [ ] The primary demo journey follows patient P-1042 from simulated deterioration to nurse response and resolution.

### Out of Scope

- Live bedside device or hospital integration — the current project uses synthetic/simulated vitals only.
- Clinical deployment, clinical recommendations, or validated clinical risk weights — this is a research prototype with configurable rules.
- Treating MIMIC-IV as real-time data — it is retrospective research/training data.
- A complicated global optimization or Hungarian dispatch algorithm in v1 — start with transparent weighted ranking and leave optimization for a research enhancement.
- Native mobile applications — v1 is a web application.
- OAuth, enterprise identity integration, and production-grade multi-hospital tenancy — seeded JWT accounts are sufficient for the prototype.

## Context

- The intended architecture is a React frontend communicating with a FastAPI/Python backend over REST and WebSockets.
- The backend owns patients, admissions, synthetic vitals, predictions, alerts, nurses, assignments, clinical notes, and audit logs.
- SQLAlchemy boundaries should preserve a migration path from SQLite during prototyping to PostgreSQL for a final application.
- The initial prediction engine should expose a stable baseline risk payload and use the existing ML pipeline when available, with a deterministic fallback for reliable demonstrations.
- The Medical Historian applies configurable research rules to patient context. Any score adjustments must be labeled as prototype explanations rather than validated clinical weights.
- The dispatcher starts with a transparent weighted score: availability 40%, proximity 30%, workload 20%, and acuity compatibility 10%.
- The UI should make role-based visibility obvious: Nurses see assigned work rather than the entire hospital system; Doctors have read-oriented clinical access; Admins have operational control.

## Constraints

- **Safety and research labeling**: Clearly identify simulated data, configurable research rules, and non-clinical prototype status to avoid implying bedside validation.
- **Role boundaries**: Exactly Admin, Doctor, and Nurse roles are in scope; API authorization must not rely only on hidden navigation items.
- **Local usability**: SQLite-first setup and seeded accounts should make the end-to-end demonstration reproducible on a developer machine.
- **Real-time behavior**: Live monitoring uses synthetic values emitted approximately every 5–10 seconds, with manual refresh and configurable automatic refresh options.
- **Auditability**: Alert transitions must be persisted as an ordered lifecycle and important actions must be traceable to a user.
- **Configurable thresholds**: Risk level thresholds and refresh settings are configuration values, not hard-coded clinical recommendations.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Optimize v1 around one end-to-end patient journey | A coherent P-1042 flow best demonstrates how the three agents connect | — Pending |
| Use real JWT authentication with seeded users | Demonstrates meaningful authorization while keeping the prototype easy to run | — Pending |
| Use SQLite first behind SQLAlchemy | Minimizes local setup while preserving a PostgreSQL migration path | — Pending |
| Use a prediction adapter with deterministic fallback | Keeps the demo reliable while allowing the existing ML pipeline to be integrated | — Pending |
| Use synthetic live vitals and retrospective MIMIC-IV research data separately | Prevents retrospective data from being represented as a live bedside feed | — Pending |
| Start dispatch with transparent weighted ranking | Makes recommendations explainable and avoids premature optimization complexity | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-24 after initialization*
