# Phase 4: Medical Historian and Human-Confirmed Dispatch - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-25
**Phase:** 4-Medical Historian and Human-Confirmed Dispatch
**Areas discussed:** Historian explanation, Dispatch confirmation, Nurse workflow, No-candidate handling

---

## Historian explanation

| Option | Description | Selected |
|--------|-------------|----------|
| Evidence timeline | Show baseline score, patient facts, rule deltas, and contextual score as a chronological evidence chain | ✓ |
| Side-by-side review | Show baseline and contextual scores beside grouped diagnoses, medications, labs, and prior events | |
| Both views | Use the evidence chain as primary with a compact side-by-side summary | |

**User's choice:** Evidence timeline
**Notes:** All seeded context categories can contribute through named configurable rules. Doctors can add timeline annotations without editing scores. Incomplete context shows baseline only. Rule mechanics appear in an expandable research-mode panel. The complete seeded record is shown without pagination.

---

## Dispatch confirmation

| Option | Description | Selected |
|--------|-------------|----------|
| Admin and Doctor | Both can confirm/override; Nurse receives and acts on the assignment | ✓ |
| Admin only | Doctors request dispatch; Admin commits staffing decisions | |
| Doctor only | Clinical owner confirms; Admin configures but does not dispatch | |

**User's choice:** Admin and Doctor
**Notes:** Confirmation/override requires a reason and evidence snapshot. Candidates appear as a ranked comparison with component evidence. Confirmation is blocked when candidate or alert evidence is stale.

---

## Nurse workflow

| Option | Description | Selected |
|--------|-------------|----------|
| Action-first alert | Risk, predicted event, latest vitals, bed, acknowledgement first, expandable context below | ✓ |
| Full patient context | Show history and explanation before actions | |
| Queue summary | Show assigned alerts as a compact list before opening one | |

**User's choice:** Action-first alert
**Notes:** Response and resolution require concise notes; acknowledgement does not. Nurse sees minimal relevant context and stays on the patient timeline after completion.

---

## No-candidate handling

| Option | Description | Selected |
|--------|-------------|----------|
| Blocked assignment state | Show every exclusion, keep alert generated/unassigned, and surface a human action | ✓ |
| Empty recommendation | Show no candidates with a short reason | |
| Escalation queue | Move the alert to a separate escalation queue | |

**User's choice:** Blocked assignment state
**Notes:** Human retry refreshes nurse status and recomputes candidates. The alert remains generated until an eligible candidate is confirmed. Record timestamp, freshness, every exclusion reason, and retry actor.

---

## the agent's Discretion

- Exact visual styling, route/component names, API module decomposition, and persistence implementation details remain open to established repository patterns.

## Deferred Ideas

None — discussion stayed within Phase 4 scope.
