# Project Research Summary

**Project:** AcuityNet  
**Domain:** ICU monitoring, predictive triage, and nurse dispatch research prototype  
**Researched:** 2026-08-24  
**Confidence:** MEDIUM

## Executive Summary

AcuityNet should be built as a small modular monolith for one reproducible, end-to-end synthetic patient journey. A React 19 and TypeScript SPA built with Vite should consume a FastAPI REST API, with WebSockets used only for patient-scoped live updates and invalidation. SQLAlchemy 2.0 and Alembic should sit behind a SQLite-first persistence boundary that remains portable to PostgreSQL. Backend application services must own prediction, contextual research rules, alert transitions, dispatch, and audit behavior; the frontend should own presentation state only.

The roadmap should optimize for P-1042: synthetic vitals deteriorate, a stable prediction crosses a configurable research threshold, the Medical Historian explains the adjustment, the Tactical Dispatcher recommends an eligible nurse, and the nurse acknowledges, responds, and resolves the alert. JWT authentication and server-enforced access for exactly Admin, Doctor, and Nurse are foundational, not UI polish. A deterministic prediction fallback, explicit data provenance, versioned configuration, append-only lifecycle events, and post-commit realtime notifications make the demonstration reliable and auditable.

The primary risks are misleading clinical presentation, retrospective MIMIC-IV data being mistaken for live telemetry, weak object-level authorization, noisy or unauditable alerts, and dispatch recommendations appearing authoritative. Persistent research-prototype labeling, synthetic/research data separation, deny-by-default API policy, transparent weighted ranking with human confirmation, deterministic simulation, and automated lifecycle/RBAC tests are required safety boundaries. Clinical deployment, treatment advice, live device integration, and validated clinical claims remain out of scope.

## Key Findings

### Recommended Stack

Use Python 3.12, FastAPI, Pydantic 2, Uvicorn, JWT with Argon2 password hashing, and SQLAlchemy 2.0/Alembic over file-based SQLite. Use React 19, TypeScript 5, Vite, TanStack Query, native browser WebSockets, Vitest/Testing Library, Playwright, pytest/httpx/pytest-asyncio, and Ruff. Pin exact versions in lockfiles during bootstrap; the researched SQLAlchemy and Alembic release lines are 2.0.52 and 1.19.2, while React, FastAPI, Vite, and supporting packages should be pinned from the initialization lockfiles.

REST is authoritative for reads and mutations. WebSockets carry synthetic vital updates and invalidation events, with reconnects recovering through REST. Keep one session per request or simulator task, use migrations from the first schema, enable SQLite foreign keys, and preserve a PostgreSQL migration path. Avoid GraphQL, second full-stack frameworks, brokers, orchestration infrastructure, online MLOps, client-only RBAC, and `create_all()` as the schema strategy. See [STACK.md](STACK.md).

### Expected Features

**Must have (table stakes):**
- Seeded JWT login, exactly three roles, and API-level role/resource/assignment enforcement.
- Role-specific Admin, Doctor, and Nurse dashboards; P-1042 patient/bed monitoring; labeled synthetic vitals with freshness state.
- Stable prediction payload containing score, level, event, probability, horizon, vitals, provenance, model/rule versions, and fallback status.
- Configurable threshold alert creation with duplicate prevention and generated, dispatched/assigned, acknowledged, responded, and resolved lifecycle states.
- Medical context and explicit research-rule deltas; transparent nurse recommendation using availability 40%, proximity 30%, workload 20%, and acuity compatibility 10% after hard eligibility filtering.
- Nurse assignment/actions, Doctor read-only clinical review, Admin operations/configuration, and append-only audit records for important actions.

**Should have (competitive):**
- Explainable risk progression, explainable dispatch score components, and one coherent chronological P-1042 timeline.
- Repeatable Admin-controlled deterioration/reset scenarios after the basic stream is reliable.

**Defer (v2+):**
- Multi-patient concurrency, historical playback, model comparison/calibration/drift, MIMIC-IV cohort exploration, what-if dispatch optimization, advanced alert-fatigue controls, global assignment optimization, device integrations, native mobile apps, production identity, and multi-hospital tenancy.

### Architecture Approach

Use a modular monolith with transport, auth, patients, vitals, prediction, historian, alerts, dispatch, audit, realtime, configuration, and persistence modules. A patient-journey application service should orchestrate observation validation, prediction, contextual explanation, alert deduplication, dispatch recommendation, atomic persistence, and post-commit notification. Prediction, historian, and dispatch should be typed, testable ports or services. Alert state transitions should be an explicit state machine with append-only events; current alert state is only a read projection. See [ARCHITECTURE.md](ARCHITECTURE.md).

### Critical Pitfalls

1. **Clinical claims hidden in a convincing dashboard** — persist a non-clinical disclaimer and provenance/model/rule metadata on every relevant surface; exclude diagnosis and treatment advice.
2. **Retrospective data presented as live telemetry** — require `synthetic`, `retrospective`, or `replay` provenance and keep MIMIC-IV offline and separate from the live synthetic feed.
3. **Weak RBAC and object access** — enforce deny-by-default checks on every REST route and WebSocket handshake, including patient and assignment ownership, and test denied paths.
4. **Alert noise and overwritten history** — deduplicate episodes, make thresholds/cooldowns configurable, validate transitions, and commit append-only lifecycle and audit events atomically.
5. **Dispatch treated as an assignment or command** — filter hard constraints, show score evidence and freshness, support no-candidate and override outcomes, and require explicit human confirmation.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Safety, Simulation, and Backend Contracts
**Rationale:** Provenance, reproducibility, schema boundaries, and truthful terminology must exist before a dashboard can safely display risk.  
**Delivers:** SQLite/Alembic foundation, seeded P-1042/users/nurses/beds/configuration, deterministic scenario clock/seed, typed DTOs, synthetic observation contract, persistent prototype labeling, and health/setup checks.  
**Addresses:** Seed data, synthetic vitals, patient monitoring, research labeling, and the foundation for every table-stakes feature.  
**Avoids:** Live/retrospective confusion, irreproducible deterioration, schema drift, and clinical overclaiming.

### Phase 2: Identity, Authorization, and Prediction Adapter
**Rationale:** All later workflows depend on trustworthy actor identity and a stable prediction contract.  
**Delivers:** Seeded JWT login, password hashing, exact three-role permission matrix, object-level policy checks, role-aware read surfaces, baseline prediction adapter, deterministic fallback, and versioned research configuration.  
**Uses:** FastAPI dependencies, Pydantic schemas, React/Vite shell, TanStack Query, and the ML/fallback adapter boundary.  
**Implements:** `auth`, `patients`, `prediction`, `configuration`, and persistence boundaries.  
**Avoids:** UI-only RBAC, fallback ambiguity, configuration drift, and privacy overexposure.

### Phase 3: Monitoring, Alerts, Lifecycle, and Audit
**Rationale:** The core value is a traceable deterioration-to-resolution workflow; alert behavior must be correct before dispatch polish.  
**Delivers:** WebSocket snapshots/updates with REST recovery, freshness/disconnected states, threshold evaluation, deduplication, alert state machine, transition commands, latency metadata, and ordered audit reconstruction.  
**Avoids:** Alert fatigue, stale feeds, invalid transitions, silent state changes, and treating WebSockets as the source of truth.

### Phase 4: Medical Historian and Human-Confirmed Dispatch
**Rationale:** Contextual explanation and staffing recommendation depend on stable predictions, alert acuity, and authenticated workflow state.  
**Delivers:** Separate baseline/effective research scores, rule explanations, candidate hard filters, weighted ranking, score breakdowns, no-eligible-candidate handling, explicit confirmation/override, nurse assignment, and Nurse acknowledge/respond/resolve actions.  
**Addresses:** Historian, dispatcher, assignment, Doctor review, and role-specific clinical workflow features.  
**Avoids:** Research rules looking clinical and recommendations becoming autonomous staffing commands.

### Phase 5: End-to-End Verification and Demo Hardening
**Rationale:** The prototype is credible only when a clean reset reproducibly demonstrates the whole P-1042 story and degraded paths remain honest.  
**Delivers:** Playwright journey coverage, backend authorization/lifecycle/fallback tests, migration checks, reconnect/reload recovery, audit verification, content/privacy review, and a repeatable demo script.  
**Addresses:** Explainable risk progression, explainable dispatch, linked patient timeline, and operational reproducibility.  
**Avoids:** Demo theater being mistaken for model validation, untested fallback behavior, privacy leakage, and accessibility failures.

### Phase Ordering Rationale

- Contracts and safety metadata precede features because every prediction, alert, and UI surface must identify its source and non-clinical status.
- Authentication precedes dashboards and mutations because role visibility is meaningless without server-enforced resource boundaries.
- Prediction and alert state precede dispatch because dispatch needs stable acuity, deduplicated episodes, and auditable actors.
- Dispatch and role workflows follow the lifecycle so recommendations can be confirmed and transitions can be tested as one journey.
- Verification comes last as a cross-cutting gate, but tests should be added with each phase rather than postponed entirely.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** Alert fatigue, cooldown/deduplication semantics, freshness behavior, and lifecycle retention need domain validation; verify current AHRQ/Joint Commission material.
- **Phase 4:** ICU staffing constraints, nurse availability/workload privacy, confirmation and override policy need a nursing workflow subject-matter expert.
- **Phase 5:** Define what workflow integration evidence may claim separately from prediction accuracy, calibration, fairness, or clinical utility.

Phases with standard patterns (skip research-phase):
- **Phase 1:** SQLite/Alembic setup, typed REST DTOs, and deterministic fixture design are established engineering patterns, subject to the project’s safety labels.
- **Phase 2:** FastAPI JWT dependency patterns, password hashing, React/Vite, and SQLAlchemy session boundaries are well documented; validate exact package pins at bootstrap.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Official documentation supports the choices, but exact React/FastAPI/Vite/supporting pins must be confirmed in lockfiles. |
| Features | HIGH | Boundaries and P-1042 acceptance direction are strongly anchored in PROJECT.md; exact thresholds, wording, and some note/assignment details remain open. |
| Architecture | HIGH | Modular-monolith, session, REST/WebSocket, state-machine, and persistence boundaries are consistently supported by official docs and the project brief. |
| Pitfalls | MEDIUM | Safety, provenance, authorization, audit, and fallback risks are clear; alert-fatigue and dispatcher workflow guidance needs local validation. |

**Overall confidence:** MEDIUM

### Gaps to Address

- Confirm exact P-1042 deterioration values, risk thresholds, event wording, horizon, note fields, and UI acceptance criteria during requirements definition.
- Decide whether dispatch requires Admin/Doctor confirmation or permits Nurse acceptance; default to explicit confirmation and audit it.
- Define audit retention, correction, deletion, and denied-action visibility for this prototype.
- Define the prediction evaluation target before discussing accuracy, calibration, fairness, or clinical utility.
- Decide whether real PHI is permanently excluded; if not, perform a formal threat model and compliance/legal review.
- Validate ICU dispatch constraints and override policy with a domain expert.

## Sources

### Primary (HIGH confidence)
- [PROJECT.md](../PROJECT.md) — authoritative scope, active requirements, decisions, constraints, and out-of-scope boundaries.
- [ARCHITECTURE.md](ARCHITECTURE.md) — recommended modular-monolith boundaries, contracts, data flow, and build order.
- Official FastAPI, SQLAlchemy, Alembic, React, Vite, OWASP, PhysioNet, and MIT-LCP documentation cited in [STACK.md](STACK.md).

### Secondary (MEDIUM confidence)
- [FEATURES.md](FEATURES.md) — table stakes, differentiators, anti-features, MVP sequence, and unresolved product details.
- [PITFALLS.md](PITFALLS.md) — safety, human-factors, authorization, audit, reproducibility, and prototype honesty risks.
- FDA Clinical Decision Support Software, HHS OCR Security Rule, NIST Privacy Framework, and the AHRQ/Joint Commission alarm-management sources cited in [PITFALLS.md](PITFALLS.md).

---
*Research completed: 2026-08-24*  
*Ready for roadmap: yes*