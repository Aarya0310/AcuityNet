# Phase 5: End-to-End Verification and Demo Hardening - Research

**Researched:** 2026-08-30  
**Domain:** Automated full-stack verification, degraded-state testing, demo reproducibility, clean-reset validation  
**Confidence:** HIGH for backend/smoke patterns (analogs from Phase 2-4); MEDIUM for E2E browser strategy (no existing Playwright/Cypress)

---

## Phase 5 Context

### Locked Requirements (from ROADMAP.md)

**Phase 5 Success Criteria:**

1. **Automated coverage**: Backend, frontend, and browser checks covering login, authorization, synthetic updates, prediction fallback, alert threshold/deduplication, lifecycle actions, historian retrieval, dispatch ranking, nurse actions, and audit recording.
2. **Documented reproducible journey**: Clean local setup, migration, seed, reset path that reproduces P-1042 deterioration through prediction, alert, human-confirmed dispatch, acknowledgement, response, and resolution.
3. **REST recovery verification**: Demonstrates REST recovery after WebSocket disconnect/reload; preserves stale, synthetic, fallback, denied, and no-candidate states.
4. **Content and workflow review**: Confirms integration and traceability only—no clinical diagnosis, treatment advice, validated-risk claims, or autonomous staffing.

### Project Constraints (from locked state)

- REST remains authoritative; WebSockets are additive for synthetic updates and invalidation events. [VERIFIED: .planning/STATE.md:21-22]
- Exactly three roles: Admin, Doctor, and assigned Nurse. [VERIFIED: .planning/REQUIREMENTS.md:10-12]
- The system is a research prototype and must not provide diagnosis or treatment advice. [VERIFIED: .planning/REQUIREMENTS.md:64]
- Phase 1-4 own contracts, auth, alerts, historian, and dispatch; Phase 5 owns end-to-end verification and demo reproducibility only. [VERIFIED: ROADMAP.md:20-130]
- Out of scope: live bedside integration, clinical deployment, validated risk weights, autonomous dispatch, roles beyond the three listed. [VERIFIED: .planning/REQUIREMENTS.md:73-85]

---

## Existing Test Patterns (Phases 1-4)

### Backend Testing Architecture

**Framework & Approach:**
- **Test Runner:** pytest (^9.1.1)
- **API Framework:** FastAPI with TestClient (no subprocess mocking)
- **Database:** Temporary SQLite per test, real Alembic migrations, real seeded data
- **Clock Injection:** Injected fixed datetime for deterministic scenario advancement
- **Auth:** Real JWT generation and bearer validation per test role

**Established Test Files (20+ focused unit/integration suites):**
- `test_auth.py`: JWT login, token expiry, invalid credentials, 401 behavior
- `test_migrations.py`: Schema upgrade/downgrade, FK constraints, indexes
- `test_seed.py`: Idempotent seed fixture, deterministic patient/user counts
- `test_vitals_api.py`: Authorized observation reads, synthetic provenance, freshness states
- `test_alerts.py`: Threshold crossing, deduplication logic, alert snapshots
- `test_lifecycle_audit.py`: State transitions, invalid paths, actor/timestamp recording
- `test_dispatch.py`: Candidate filtering, weighted ranking (40/30/20/10), exclusion reasons
- `test_nurse_workflow.py`: Assignment scope, acknowledge/respond/resolve, denial checks
- `test_phase2_integration.py`: Full auth chain, role/patient isolation, prediction wiring
- `test_phase3_integration.py`: Deterioration → alert → lifecycle → audit journey
- `test_phase4_integration.py`: Historian evaluation, dispatch ranking, human-confirmed assignment

**Test Pattern (from test_phase3_integration.py):**
```python
def make_journey(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'phase3.db'}"
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    app = create_app(database_url, clock=lambda: now[0])
    client = TestClient(app)
    # login each role, return headers dict for subsequent requests
    return client, database_url, now, roles

def test_complete_phase3_journey_is_reconstructable_and_role_scoped(tmp_path):
    client, database_url, now, roles = make_journey(tmp_path)
    # assert HTTP status, response contracts, persisted event counts/order
```

**Key Properties:**
- Real SQLAlchemy ORM; no mocking of persistence layer
- Real async event ordering via fixed clock injection
- Isolated temp databases per test (no cleanup conflicts)
- Response contract assertions (status, JSON shape, field values)
- Persisted state assertions (database queries post-request)
- Authorization denials recorded in audit trail

### Smoke Testing Pattern (Phases 1-4)

**Framework:**
- **Language:** Python stdlib (no external HTTP library dependencies)
- **Process:** Subprocess `uvicorn backend.app.main:app` with temporary SQLite database
- **Secret Handling:** Preflight `ACUITYNET_JWT_SECRET` before launching child; pass only to child environment; never print secrets/tokens
- **Assertions:** HTTP status, response JSON, metadata fields, exact counts
- **Cleanup:** `finally` block terminates child process

**Existing Smoke Runners:**
- `scripts/phase1_smoke.py`: `/health` and `/api/v1/patients/P-1042/vitals/current`, synthetic provenance validation
- `scripts/phase2_smoke.py`: All three role logins, prediction contract, Admin KPIs, config changes
- `scripts/phase3_smoke.py`: Deterioration ticks, alert generation, lifecycle transitions, audit reconstruction
- `scripts/phase4_smoke.py`: Historian evaluation, dispatch ranking, human confirmation, nurse workflow

**Key Properties:**
- Child process isolation (secrets, auth state, database mutations do not affect dev environment)
- Minimal dependencies (Python stdlib + installed project packages only)
- Deterministic step sequence (no randomness, no real-time clock dependencies)
- Clear output with failure diagnostics (HTTP status, response excerpt, expected value)
- Exit code indicates success/failure (0 = all checks passed)

### Frontend Testing Pattern (Phases 1-4)

**Framework:**
- **Test Runner:** Vitest (^4.1.11)
- **Component Testing:** @testing-library/react (^16.3.2)
- **Mocking:** Fetch/API mocked at component boundary; no real HTTP to backend
- **State Management:** TanStack Query (^5.102.2) for server-state reads
- **No E2E Browser Testing:** No Playwright, Cypress, or Selenium currently in use

**Established Frontend Tests:**
- `frontend/src/monitoring/MonitoringPage.test.tsx`: Component render, fetch mock responses, error states, reconnect UI
- Similar pattern for other role-specific pages (AdminDashboard, DoctorHistorian, NurseAlert)

**Key Properties:**
- Unit/integration tests at component level
- Fetch mocked; no real API calls
- React Query hooks tested via mock server responses
- Loading/error/success states verified
- No browser automation (no click-based workflows)

---

## Phase 5 Coverage Gaps

### Gap 1: No Full-Stack E2E Browser Tests

**What's Missing:**
- No browser automation framework (Playwright, Cypress, Selenium) installed
- No test cases that login via UI form, navigate, click buttons, submit lifecycle actions
- No visual/interaction verification (alert priority badge color, nurse action button enabled/disabled)
- No browser realtime behavior (WebSocket reconnect, manual page reload, background tab recovery)
- No multi-user concurrent scenario (Admin and Doctor in separate sessions modifying same alert)

**What Success Criteria 1 Requires:**
> "Automated backend, frontend, and browser checks covering login, role/resource authorization, synthetic updates, prediction fallback, alert threshold/deduplication, lifecycle actions, historian retrieval, dispatch ranking, nurse actions, and audit recording."

**Analysis:** Backend and frontend unit/smoke tests cover APIs in isolation. Browser tests must prove the full UI workflow: form submission → authorization → response rendering → state mutation → audit evidence.

---

### Gap 2: No Degraded-State Scenario Coverage

**Identified Degraded States (from REAL-02, D-16, D-17, D-18):**

| State | Trigger | Expected Behavior | Test Gap |
|-------|---------|-------------------|----------|
| **Stale** | API call delayed >cooldown threshold | Page shows "stale" badge; refresh button available; no state mutation | No test verifies stale presentation persists on refresh |
| **Synthetic** | All observations are P-1042 scenario data | "Simulated" label visible on every clinical surface | Tests verify label in API; no UI label verification |
| **Fallback** | ML provider unavailable or returns error | Prediction shows `deterministic_fallback` source; no clinical model claim | API tests verify fallback reason; no UI warning tested |
| **Denied** | Unauthorized role/patient/assignment access | 403 response; no error state leaks identity detail | Backend test verifies 403; no frontend error messaging tested |
| **No Candidate** | All eligible nurses filtered out; no assignment possible | Alert stays `generated`/`unassigned`; "No eligible nurses" reason visible; retry action available | API test verifies state; no UI blocking presentation tested |
| **Disconnected** | WebSocket closes; client detects loss | Page shows "offline"; REST queries continue; page reload recovers full state | No WebSocket disconnect/recovery scenario tested |
| **Unavailable Fallback** | Fallback prediction computation fails | Page shows operational error state, not clinical error | No unavailable-fallback scenario tested |

**Analysis:** Backend tests check database state changes. Frontend unit tests check component props. E2E tests must verify user sees appropriate messaging and cannot access/mutate beyond their role.

---

### Gap 3: No Clean-Reset Reproducibility Demonstration

**What's Missing:**
- No test that starts with a clean SQLite, applies full setup path (migration, seed, reset), and verifies P-1042 is ready for the demo
- No verification that reset fully removes alert/lifecycle/audit artifacts without leaving orphaned rows
- No test of reset idempotence (reset twice on same database, verify same state)
- No documented step-by-step clean setup instructions (where does the user run `alembic upgrade head`? When? With what environment?)

**What Success Criteria 2 Requires:**
> "A documented clean local setup, migration, seed, reset path reproduces P-1042 deterioration through prediction, alert, human-confirmed dispatch, acknowledgement, response, and resolution."

**Analysis:** Phase 4 has `test_phase4_integration.py` that uses a temporary SQLite. Phase 5 must document the exact PowerShell commands and verify them with a test.

---

### Gap 4: No REST Recovery Verification After Realtime Disruption

**What's Missing:**
- No test that establishes a WebSocket connection, simulates disconnect (client closes), and verifies REST refetch recovers authoritative state
- No test that modifies alert state while WebSocket is disconnected, then reconnects and verifies eventual consistency (REST query returns new state)
- No test of page reload after disconnect (browser refresh requests all queries, no stale cache returned)
- No test of browser background tab recovery (tab becomes active after WebSocket timeout, reconnect succeeds)

**What Success Criteria 3 Requires:**
> "Verification demonstrates REST recovery after WebSocket disconnect or reload and visibly preserves stale, synthetic, fallback, denied, and no-candidate states."

**Analysis:** Phase 3 has WebSocket TestClient tests in `test_phase3_integration.py` that verify socket close behavior. Phase 5 must add browser-level disconnect/recovery simulation.

---

### Gap 5: No Content/Workflow Review Automation

**What's Missing:**
- No automated scan that checks every backend response for clinical claims (diagnosis, treatment, validated risk, autonomous action)
- No automated scan that verifies every UI surface displays "research prototype" / "simulated" / "not for clinical use" label
- No test that traces complete audit trail from initial P-1042 observation through alert acknowledgement to resolution
- No test that verifies every claim in the demo narrative matches persisted evidence

**What Success Criteria 4 Requires:**
> "A final content and workflow review confirms that the demo proves integration and traceability only, with no clinical diagnosis, treatment advice, validated-risk claim, or autonomous staffing command."

**Analysis:** This is a semantic/content check, not a behavior check. Manual review is required, but automated smoke checks can flag missing labels/metadata.

---

## Degraded-State Test Scenarios

### Scenario 1: Stale Prediction Blocks Dispatch Confirmation

**Trigger:** User clicks "Refresh Candidates" after 15+ minutes without update.

**Expected Behavior:**
```
Initial dispatch evaluation created at T=10:00
User waits until T=10:20
User attempts to confirm recommendation without refresh
System returns 409 Conflict: "Dispatch evaluation is stale; please refresh"
User clicks "Refresh Candidates"
Fresh evaluation fetched; confirmation allowed
```

**Test Case (Backend):**
- Inject fixed clock T=10:00, create dispatch evaluation
- Advance clock to T=10:20
- POST confirm with original evaluation ID
- Assert 409 response with "stale" message
- POST refresh dispatch, get new evaluation ID
- POST confirm with new evaluation ID
- Assert 200 response, assignment created

**Test Case (E2E Browser):**
- Admin logs in, triggers dispatch evaluation
- UI shows "Evaluated at 10:00" timestamp
- Wait 15 minutes or simulate clock advance (browser-side?)
- Click "Confirm" button
- UI shows error toast "Dispatch evaluation is stale"
- Click "Refresh Candidates" button
- Wait for new evaluation request
- Click "Confirm" again
- Assert assignment created, nurse name displayed

---

### Scenario 2: Synthetic Provenance Label Visible on Every Clinical Surface

**Expected Behavior:**
- Vital signs show "(Synthetic simulation)"
- Prediction shows "Source: Deterministic fallback — Research prototype"
- Alert shows "Simulated deterioration detected"
- Historian shows "Scenario ID: p1042-deterioration-v1"
- Nurse assignment shows "Alert: Simulated patient alert"

**Test Case (Backend):**
- GET `/api/v1/patients/P-1042/vitals/current` → assert `provenance.source_name == "acuitynet-simulator"`
- GET `/api/v1/patients/P-1042/prediction` → assert `source_kind == "deterministic_fallback"` and `prototype_label` contains "research"
- GET `/api/v1/patients/P-1042/alert` → assert `provenance.source_kind == "synthetic"`
- GET `/api/v1/patients/P-1042/historian` → assert `scenario_id == "p1042-deterioration-v1"`
- GET `/api/v1/patients/P-1042/dispatch/evaluation` → assert `prototype_label` includes "research"

**Test Case (E2E Browser):**
- Doctor logs in, navigates to monitoring page
- Assert vital signs card displays "(Synthetic)" badge
- Assert prediction card shows "Research prototype" label
- Assert alert card shows "Simulated deterioration"
- Assert historian page shows scenario/rule metadata
- Assert nurse assignment page shows synthetic label

---

### Scenario 3: Fallback Prediction Prevents Model-Based Ranking

**Expected Behavior:**
```
ML provider is unavailable (null or error)
Deterministic fallback returns score 0.75, level "critical"
Dispatch evaluation filters candidates normally
Ranking uses only availability/proximity/workload/acuity (40/30/20/10)
No model component in score breakdown
```

**Test Case (Backend):**
- Create app with null ML provider
- Advance P-1042 to critical threshold
- POST `/api/v1/patients/P-1042/dispatch/evaluation` as Doctor
- Assert `prediction.source_kind == "deterministic_fallback"`
- Assert `prediction.fallback_reason == "ML provider unavailable"`
- Assert evaluation contains ranked candidates
- Assert candidate scores breakdown: `availability: 0.X, proximity: 0.X, workload: 0.X, acuity: 0.X`
- Assert no `model_score` field in breakdown

**Test Case (E2E Browser):**
- Admin sets ML provider to disabled/null (via config page)
- Doctor triggers alert for P-1042
- Doctor navigates to dispatch evaluation
- Assert prediction shows "Fallback: ML provider unavailable"
- Assert dispatch ranking shows component scores without model component
- Assert nurse recommendation still ranked correctly

---

### Scenario 4: Denied Access Recorded in Audit Without Identity Leak

**Expected Behavior:**
```
Unassigned Nurse Alex attempts to read P-1042's alert
System returns 403 Forbidden
No response body leaks patient name, diagnosis, or alert content
Audit event recorded: {actor: "U-ALEX", action: "read", resource: "alert", outcome: "denied", reason: "unassigned"}
Reason is generic (not "you are not assigned to P-1042")
```

**Test Case (Backend):**
- Login as Alex (unassigned nurse)
- GET `/api/v1/patients/P-1042/alert` with Alex's token
- Assert 403 response
- Assert response body does not include patient name or clinical data
- Query audit table: filter by actor "U-ALEX", assert outcome "denied" exists
- Assert audit details do not leak patient-identifying information

**Test Case (E2E Browser):**
- Login as Alex (unassigned nurse)
- Try to navigate to P-1042's dashboard (e.g., via URL bar or navigation)
- Assert UI shows generic "Access Denied" without patient details
- Assert no confidential data visible (e.g., bed number, diagnosis)

---

### Scenario 5: No-Candidate Alert Stays Generated/Unassigned

**Expected Behavior:**
```
All available nurses are ineligible (on break, in surgery, acuity mismatch)
Dispatch evaluation returns no candidates and explicit exclusions
Alert remains in "generated" state (not "assigned")
Admin/Doctor see "No eligible nurses found" reason and "Retry" action
Nurse Sarah does not receive alert
```

**Test Case (Backend):**
- Seed Sarah as "on break"
- Create alert for P-1042
- POST `/api/v1/patients/P-1042/dispatch/evaluation` as Doctor
- Assert response.candidates is empty array
- Assert response.exclusions lists Sarah with reason "on break"
- Assert response.outcome == "no_candidate_available"
- GET `/api/v1/patients/P-1042/alert` → assert state == "generated", assignment_id is null
- Verify Sarah does NOT receive alert assignment

**Test Case (E2E Browser):**
- Admin navigates to P-1042's alert
- Alert shows "Pending Assignment" state
- Admin clicks "Evaluate Candidates"
- UI shows "No eligible nurses available"
- List of candidates with exclusion reasons visible
- "Retry Evaluation" button available
- Sarah's nurse dashboard does not list P-1042

---

### Scenario 6: WebSocket Disconnect/Reconnect Recovery

**Expected Behavior:**
```
Doctor opens monitoring dashboard (establishes WebSocket)
WebSocket receives synthetic vital update notification
Page displays: "Vitals updated at T"
Network disruption closes WebSocket
Page shows: "Offline — reconnecting..."
Doctor clicks refresh or waits 30 seconds
WebSocket reconnects
Page refetches alert/audit via REST
Page shows: "Back online"
```

**Test Case (Backend - WebSocket Behavior):**
- Client connects to `/api/v1/patients/P-1042/realtime?access_token=...`
- Send malformed JSON
- Assert connection closes
- Reconnect
- Advance vital ticks
- Assert WebSocket receives invalidation message
- Assert REST query refetch returns new data

**Test Case (E2E Browser):**
- Doctor logs in, navigates to monitoring page
- UI shows WebSocket status: "Connected"
- Simulate network disconnect (Chrome DevTools network throttle or offline mode)
- Assert UI shows "Offline — Reconnecting..."
- Simulate network reconnect
- Assert UI shows "Back online"
- Assert vital signs updated with latest data

---

## Testing Strategy Recommendation

### Architecture: Three-Tier Verification

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 5 Testing Stack                    │
├──────────────────┬──────────────────┬──────────────────────┤
│   BACKEND (7-8)  │   FRONTEND (4-5) │   E2E BROWSER (6-8)  │
├──────────────────┼──────────────────┼──────────────────────┤
│ • pytest + DB    │ • Vitest + React │ • Playwright +       │
│ • Deterministic  │ • Query mocking   │   browser automation │
│ • Role/resource  │ • Component       │ • Real WebSocket     │
│ • Audit trail    │   state, fetch    │ • Degraded states    │
│                  │   mocks           │ • Multi-user flows   │
├──────────────────┼──────────────────┼──────────────────────┤
│ BACKEND FOCUS    │ FRONTEND FOCUS   │ E2E FOCUS            │
│ • Auth/authz     │ • UI render       │ • Full workflow      │
│ • DB integrity   │ • Loading/error   │ • WebSocket recover  │
│ • State machine  │ • Form validation │ • Visual feedback    │
│ • Audit events   │ • Accessibility   │ • Content safety     │
└──────────────────┴──────────────────┴──────────────────────┘
```

### Backend Tests (7-8 tests)

**Target Coverage:** Verify all Phase 1-4 features remain intact and Phase 5 scenarios work end-to-end.

**Test Suite Breakdown:**

| Test File | Purpose | Estimated # |
|-----------|---------|-------------|
| `test_phase5_clean_reset.py` | Reset/reseed idempotence, no orphaned rows, fresh state | 3 |
| `test_phase5_degraded_states.py` | Stale dispatch, fallback ranking, denied audit, no-candidate preservation | 4 |
| `test_phase5_full_journey.py` | End-to-end P-1042 deterioration through nurse resolution | 1 |
| **Total** | | **8** |

**Key Assertions per Test:**
- HTTP status codes (200, 401, 403, 409, 422)
- Response contract validation (Pydantic shape, required fields, no extra fields)
- Database state (counts, ordering, foreign keys, audit trail)
- Timestamp determinism (clock injection consistency)
- Secret safety (no passwords/tokens in logs/responses)

---

### Frontend Tests (4-5 tests)

**Target Coverage:** Verify React components render correctly with API responses and handle error/loading states.

**Test Suite Breakdown:**

| Component / Hook | Purpose | Estimated # |
|------------------|---------|-------------|
| `MonitoringPage` | Vital display, stale badge, refresh action | 1 |
| `AlertPage` | Alert priority, lifecycle buttons, denied state | 1 |
| `HistorianPage` | Rule explanation, annotation form, timeline rendering | 1 |
| `DispatchPage` | Candidate ranking, confirmation form, no-candidate message | 1 |
| `useAlertRealtime` | WebSocket connect/disconnect, invalidation, reconnect backoff | 1 |
| **Total** | | **5** |

**Key Assertions per Test:**
- Component renders without error
- Correct text/badge visible for given state
- Form submission calls correct API endpoint
- Error toast displays on 403/409/422
- Loading state shown during fetch
- Accessibility queries (role, label, button)

---

### E2E Browser Tests (6-8 tests)

**Tool:** Playwright (^1.45.0) — cross-platform, TypeScript support, WebSocket recording.

**Target Coverage:** Verify complete user workflows from login through role-specific actions.

**Test Suite Breakdown:**

| Workflow | Purpose | Estimated # |
|----------|---------|-------------|
| `Admin completes setup and resets for demo` | Clean reset, fresh database, P-1042 ready | 1 |
| `Doctor logs in, reviews historian, evaluates dispatch` | Full historian + dispatch workflow | 1 |
| `Doctor confirms dispatch, Sarah acknowledges alert` | Multi-role workflow, assignment handoff | 1 |
| `Nurse Sarah completes response/resolution workflow` | Nurse-scoped alert actions, audit trail | 1 |
| `Alert shows stale/fallback/denied/no-candidate states` | Degraded state presentation and messaging | 1 |
| `WebSocket disconnect and page reload recovery` | Network resilience, REST recovery | 1 |
| `Admin modifies config; prediction recomputes fallback` | Configuration effect on prediction source | 1 |
| `Concurrent users modify same alert (Admin + Doctor)` | Race condition and consistency handling | 1 |
| **Total** | | **8** |

**Key Assertions per Test:**
- Page title / URL matches expected route
- Form submits and response shows success toast
- Role-specific UI visible (Admin sees "Reset" button; Nurse doesn't)
- Lifecycle state transition reflects in UI (badge color, button disabled)
- Audit trail populates after each action
- Synthetic/Fallback/Denied labels visible
- WebSocket status shows online/offline/reconnecting
- Database state consistent after workflow completes

---

### Smoke Tests (1 expanded script)

**Extend `scripts/phase5_smoke.py`:**

```python
# 1. Setup phase
#    - Clean SQLite database
#    - Run migrations
#    - Run reset (if exists)
#    - Run seed

# 2. Full demo journey
#    - Login Admin, Doctor, Sarah
#    - Advance vitals ticks 0-4 (P-1042 deterioration)
#    - Fetch prediction (assert fallback source)
#    - Fetch alert (assert threshold crossed)
#    - Advance again, verify deduplication
#    - Fetch historian
#    - POST dispatch evaluation (assert candidates)
#    - POST confirm dispatch (assign to Sarah)
#    - Login Sarah
#    - POST acknowledge, respond, resolve
#    - Fetch audit trail
#    - Assert ordered lifecycle events
#    - Verify synthetic provenance on all responses

# 3. Cleanup
#    - Terminate Uvicorn child process
#    - Report success/failure
#    - Exit with 0/1
```

---

## Infrastructure Needs

### Package Additions

| Package | Version | Purpose | Install |
|---------|---------|---------|---------|
| playwright | ^1.45.0 | E2E browser automation | `pip install playwright==1.45.0` + `playwright install chromium` |
| (optional) pytest-playwright | ^0.5.0 | pytest integration for Playwright | `pip install pytest-playwright==0.5.0` |
| (optional) @playwright/test | ^1.45.0 | TypeScript E2E alternative | `npm install --save-dev @playwright/test@1.45.0` |

**Note:** No new backend runtime dependencies. Playwright is test-only and optional (Python-based or TypeScript-based; use Python for consistency with existing smoke tests).

### CI/CD Integration (Optional, Not Blocking)

- GitHub Actions workflow to run all three test tiers on every commit
- Parallel job execution: backend tests (2min), frontend tests (1min), E2E tests (5min)
- Artifact upload for video/trace on failure

### Local Development Setup (Required)

**Windows PowerShell Setup Instructions:**

```powershell
# 1. Install Playwright (if using Python E2E tests)
cd c:\Users\ADMIN\Downloads\AcuityNet
python -m pip install "playwright==1.45.0"
playwright install chromium

# 2. Run all tests
python -m pytest backend/tests/test_phase5_*.py -q
npm --prefix frontend run test -- --run
python e2e/phase5_browser.py  # or: npx playwright test e2e/

# 3. Run smoke
$env:ACUITYNET_JWT_SECRET = "your-local-secret"
python scripts/phase5_smoke.py

# 4. Verify clean reset
cd backend
alembic --config alembic.ini upgrade head
python -c "from app.persistence.database import make_engine, session_factory; from app.seed.reset import reset_demo_data; from app.seed.demo_data import seed_demo_data; engine=make_engine('sqlite:///acuitynet-phase5.db'); s=session_factory(engine)(); reset_demo_data(s); s.commit(); seed_demo_data(s()); s.commit()"
cd ..
# Database ready; no alert/audit artifacts present
```

---

## Test Artifact Locations

```
backend/tests/
├── test_phase5_clean_reset.py       # Reset idempotence, cleanup verification
├── test_phase5_degraded_states.py   # Stale, fallback, denied, no-candidate
├── test_phase5_full_journey.py      # End-to-end P-1042 lifecycle
├── conftest.py                      # Shared fixtures (temp DB, clock injection)

frontend/src/
├── App.test.tsx                     # Placeholder (existing tests updated)
├── (no new frontend unit tests; use existing patterns)

e2e/ (new directory)
├── conftest.py                      # Playwright fixtures (browser, auth)
├── test_admin_setup.spec.ts         # Admin reset/setup workflow
├── test_doctor_dispatch.spec.ts     # Doctor historian + dispatch
├── test_nurse_workflow.spec.ts      # Nurse alert response
├── test_degraded_states.spec.ts     # Stale, fallback, denied, no-candidate
├── test_websocket_recovery.spec.ts  # WebSocket disconnect/reconnect
└── test_concurrent_users.spec.ts    # Multi-user race conditions

scripts/
├── phase5_smoke.py                  # Full deterministic journey (upgrade from phase4)
└── phase5_setup.ps1                 # PowerShell setup instructions

.github/workflows/
└── phase5-tests.yml                 # (Optional) CI/CD job for all tiers
```

---

## Estimated Test Count Breakdown

| Tier | Category | Count | Rationale |
|------|----------|-------|-----------|
| **Backend** | Reset/idempotence | 3 | Cleanup ordering (Phase 4 children), reset twice, verify state |
| | Degraded states | 4 | Stale dispatch, fallback, denied, no-candidate |
| | Full journey | 1 | End-to-end vitals→alert→dispatch→resolve |
| **Subtotal** | | **8** | |
| **Frontend** | Components | 5 | Monitoring, Alert, Historian, Dispatch pages + useAlertRealtime hook |
| **Subtotal** | | **5** | |
| **E2E Browser** | Workflows | 8 | Setup, dispatch, nurse workflow, degraded states, WebSocket, config effect, concurrency |
| **Subtotal** | | **8** | |
| **Smoke** | Full journey | 1 | Deterministic setup→demo→cleanup |
| **Subtotal** | | **1** | |
| **TOTAL** | | **22** | Across all tiers |

---

## Known Unknowns & Recommendations

### Unknown 1: WebSocket Browser Testing

**Status:** Playwright has built-in WebSocket inspection; no third-party library required.

**Recommendation:** Use Playwright's page.on('websocket') to intercept and mock WebSocket frames, or let real WebSocket connect and capture disconnect events via page.on('close').

### Unknown 2: Frontend E2E Language (Python vs TypeScript)

**Status:** Existing smoke tests are Python. Frontend tests are TypeScript (Vitest).

**Options:**
- **Option A (Recommended):** Write E2E tests in Python using Playwright (matches existing smoke patterns)
- **Option B:** Write E2E tests in TypeScript using @playwright/test (matches frontend patterns)

**Recommendation:** Use Option A (Python) to keep all infrastructure code in one language and reuse the smoke test patterns. Pytest-playwright integration exists.

### Unknown 3: Database Isolation for E2E Tests

**Status:** Unclear if E2E tests should use isolated temp SQLite or connect to a shared running backend.

**Options:**
- **Option A:** E2E tests spawn their own Uvicorn child (like smoke tests)
- **Option B:** E2E tests connect to a persistent dev backend
- **Option C:** Hybrid — smoke test spawns backend; E2E tests use browser to connect

**Recommendation:** Use Option A for reproducibility (isolated database per test run, no cross-test leakage). Accepts slower E2E test runtime (~5 min for 8 tests) in exchange for determinism.

### Unknown 4: Multi-User Concurrency Testing

**Status:** Playwright supports multiple browser contexts in one test.

**Recommendation:** Use separate Playwright contexts for Admin and Doctor, login each role, make concurrent mutations to the same alert, and verify no race conditions.

---

## Summary: Testing Recommendation for Phase 5

**Adopt a three-tier testing pyramid:**

1. **Backend (8 tests, ~2 min):** Extend existing pytest patterns to cover reset, degraded states, and end-to-end journey. Reuse temp SQLite, clock injection, TestClient.

2. **Frontend (5 tests, ~1 min):** Extend existing Vitest patterns for key page components and hooks. Mock fetch at component boundary.

3. **E2E Browser (8 tests, ~5 min):** Add new Playwright tests for complete workflows. Use Python + pytest-playwright for consistency. Each test uses isolated Uvicorn child + temp SQLite.

4. **Smoke (1 script, ~3 min):** Extend existing phase4_smoke.py pattern to demonstrate full P-1042 journey and clean reset.

**Total Execution Time (parallel): ~5-7 minutes**  
**Total New Test Code: ~1500 lines (500 backend + 300 frontend + 700 E2E)**  
**Breaking Changes: None (all backward compatible with Phase 1-4)**

---

## Next Steps for Planning

1. **Review this RESEARCH.md** with the planner to confirm recommendation aligns with project goals.
2. **Create PLAN.md** with detailed task breakdown for each test tier.
3. **Update README.md** with clean-reset instructions and test-running commands.
4. **Document expected test times** and CI/CD job configuration (if applicable).

---

## References

**Existing Patterns:**
- Phase 1-4 backend test structure: `.planning/phases/0X-*/PATTERNS.md`
- Phase 2-4 integration test examples: `backend/tests/test_phase*.py`
- Smoke test pattern: `scripts/phase{2,3,4}_smoke.py`
- Frontend testing: `frontend/src/**/*.test.tsx`

**External Standards:**
- Playwright docs: https://playwright.dev
- Pytest docs: https://docs.pytest.org
- Vitest docs: https://vitest.dev

**Project Artifacts:**
- ROADMAP.md: Phase 5 success criteria
- REQUIREMENTS.md: TEST-01, TEST-02 (Phase 5 ownership)
- .planning/STATE.md: REST authority, WebSocket additive
- README.md: Current setup/run instructions (update for Phase 5)
