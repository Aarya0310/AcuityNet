---
document_type: verification-checklist
phase: 05-end-to-end-verification-and-demo-hardening
scope: pre-ship content safety and quality review
status: active
---

# VERIFICATION-CHECKLIST.md

## Pre-Ship Content Safety, Quality, and Compliance Review

This checklist ensures AcuityNet meets all clinical safety, UX quality, and compliance requirements before shipping Phase 5.

**Review duration:** 30-45 minutes  
**Reviewer role:** Product/Clinical/Engineering lead  
**Approval required:** ✓ All sections must be checked before merge

---

## Section 1: Clinical Content Safety

### 1.1 No Autonomous Clinical Decisions
- [ ] **Diagnosis never made by system** — Historian displays "contextual risk," not diagnosis
- [ ] **No treatment recommendations** — Dispatch shows nurse candidates, not "recommend antibiotic X"
- [ ] **No prognosis statements** — Timeline shows events, not "patient will recover" or "high mortality risk"
- [ ] **No autonomous escalation triggers** — Alerts require human acknowledgement to dispatch
- [ ] **Search:** Grep for red-flag words in codebase:
  ```bash
  grep -r "recommend\|prescribe\|diagnose\|prognosis\|contraindicated" frontend/ backend/ --include="*.tsx" --include="*.py" | grep -v test | grep -v TODO
  # Result should be: 0 matches (outside comments)
  ```

### 1.2 Language Clarity — No Unvalidated Claims
- [ ] **No "validated" or "proven" language** — Risk model labeled "prototype" where appropriate
- [ ] **No "AI-driven" marketing speak** — Instead: "context-informed candidate ranking"
- [ ] **No certainty language** — Avoid "will," "must," "always" for clinical predictions
- [ ] **Honest disclaimers present** — Footer/about page includes: "Not for autonomous clinical decisions"
- [ ] **Rule explanations transparent** — e.g., "oxygen saturation < 92% for >5 minutes triggers alert" (not "our AI detected critical hypoxia")
- [ ] **Manual verification:** Check pages:
  - [ ] Historian: Rules tab shows plain-language condition triggers (no marketing language)
  - [ ] Risk breakdown: Shows "baseline," "contextual delta," no "validated" claims
  - [ ] Dispatch: Shows ranking reason breakdown (availability, proximity, etc.), not "optimal"
  - [ ] Alert: Shows state (generated, acknowledged, etc.), not "AI-confirmed critical"

### 1.3 Patient Data Privacy — No PHI Leakage
- [ ] **Login required for all patient data** — Unauthenticated users can't see P-1042
- [ ] **Error messages generic** — 403 "Access Denied" never shows patient name or ID
- [ ] **Network logs reviewed** — Check Playwright test failures: no PHI in screenshots
- [ ] **Logs scrubbed** — pytest output doesn't print patient names
- [ ] **Database backups noted** — Backend docs mention: "SQLite file in backend/ contains live data; .gitignore prevents commit"
- [ ] **Search:** Verify .gitignore excludes sensitive files:
  ```bash
  grep -E "\.db|\.env|secrets" .gitignore
  # Result should include: *.db, .env*, *.env
  ```

---

## Section 2: Frontend UX Quality

### 2.1 Component Rendering & Accessibility
- [ ] **All pages load without errors** — No console 500 errors when logged in
- [ ] **Buttons have hover/focus states** — Keyboard navigation works (Tab through buttons)
- [ ] **Loading states visible** — Spinners appear while API calls pending
- [ ] **Error messages helpful** — "Network error" shows retry button, not just blank page
- [ ] **Forms validated** — Login requires non-empty username/password; dispatch form prevents submit on invalid fields
- [ ] **Mobile-responsive check** (optional but recommended):
  ```bash
  # Open DevTools (F12) → Toggle device toolbar (Ctrl+Shift+M)
  # Test on iPhone 12, iPad breakpoints
  ```

### 2.2 State Persistence & Recovery
- [ ] **Refresh doesn't lose form data** — Start typing dispatch confirmation form, refresh, data persists
- [ ] **WebSocket disconnect shows "offline"** — Open DevTools → Network → Throttle to Offline, verify UI shows offline badge
- [ ] **Manual refresh works during disconnect** — Click refresh button, content appears via REST
- [ ] **Re-login after session timeout** — Stay logged out >1 hour, page redirects to login, no errors
- [ ] **Browser back button works** — Navigate alert → dispatch → historian → back → alert loads from cache (if caching enabled)

### 2.3 Visual Consistency & Branding
- [ ] **Color palette consistent** — Critical alerts red, normal blue, neutral gray
- [ ] **Typography hierarchy** — Page title > section heading > body text (size and weight)
- [ ] **Spacing & alignment** — Cards aligned in grid, no random offsets
- [ ] **Icon clarity** — All icons have tooltips (hover shows "Acknowledge", "Resolve", etc.)
- [ ] **Dark mode (if supported)** — Not required for v1, but if implemented, check all components
- [ ] **Manual verification steps:**
  - [ ] Login page: Form centered, logo visible, colors match design system
  - [ ] Dashboard: Cards arranged in grid, padding consistent
  - [ ] Historian: Risk breakdown layout readable at 1024px and 1440px widths
  - [ ] Dispatch: Candidate ranking score breakdown clear

### 2.4 Responsive Design (Mobile-First Preferred, Desktop Minimum)
- [ ] **Desktop (1440px):** All pages readable, no horizontal scroll
- [ ] **Tablet (768px):** Sidebar may collapse to hamburger, content wraps properly
- [ ] **Mobile (375px):** Text readable (no text <12px), buttons tappable (>44px tall)
- [ ] **Touch targets** — Buttons at least 44x44px (React Testing Library assertion can verify)
- [ ] **Zoom to 200%:** Text remains readable, no overlapping elements
- [ ] **Test command:**
  ```bash
  npm --prefix frontend run test -- responsive # (if test exists)
  # or manual browser DevTools testing
  ```

---

## Section 3: Backend API Quality

### 3.1 Endpoint Security & Authorization
- [ ] **Doctor can't see other doctors' patients** — Login as doctor, try GET `/api/v1/patients/OTHER_PATIENT_ID`, expect 403
- [ ] **Nurse can't access admin endpoints** — Login as nurse, try GET `/api/v1/admin/reset`, expect 403
- [ ] **JWT tokens expire** — Set token expiration to 15 seconds in test, verify unauthorized after expiry
- [ ] **Password hashing verified** — No plaintext passwords in database:
  ```bash
  sqlite3 backend/acuitynet.db "SELECT username, password FROM users LIMIT 1;"
  # Result: password should NOT be "admin-password" (should be hashed)
  ```

### 3.2 Data Validation & Error Handling
- [ ] **Required fields enforced** — POST `/api/v1/alerts` without `patient_id` returns 422
- [ ] **Invalid data rejected** — POST with `priority="ULTRA_CRITICAL"` (invalid enum) returns 422
- [ ] **Database constraints enforced** — Can't insert duplicate patient IDs:
  ```bash
  # Run backend test
  python -m pytest backend/tests/test_phase5_verification.py::test_reset_is_idempotent_and_restores_baseline -v
  ```
- [ ] **Graceful error messages** — User-facing errors don't include stack traces

### 3.3 Performance & Scalability Baselines
- [ ] **Historian endpoint <500ms** — GET `/api/v1/patients/P-1042/historian` completes within 500ms
- [ ] **Alert list paginates** — Large patient lists don't return all alerts (implement pagination)
- [ ] **Database indexes exist** — `EXPLAIN QUERY PLAN` shows index usage (optional for v1 SQLite)
- [ ] **Connection pooling** — No "too many connections" errors under test load
- [ ] **Test command:**
  ```bash
  # Simple load test
  for i in {1..10}; do curl -s http://127.0.0.1:8000/api/v1/patients/P-1042/historian > /dev/null; done
  echo "✓ 10 requests completed"
  ```

### 3.4 Logging & Monitoring
- [ ] **Audit trail for sensitive actions** — Each alert dispatch, acknowledgement, response logged with timestamp and user
- [ ] **No sensitive data in logs** — Logs don't contain patient names or full medical history
- [ ] **Error logs include context** — Failed request logs include endpoint, user, error type
- [ ] **Production-ready format** — Logs structured (JSON or key=value), not unformatted text
- [ ] **Verify logging:**
  ```bash
  # Trigger error and check backend console/logs
  curl -X GET http://127.0.0.1:8000/api/v1/patients/INVALID/alert
  # Backend should log: "GET /api/v1/patients/INVALID/alert - 404"
  ```

---

## Section 4: Test Coverage & Automation

### 4.1 Test Tiers Complete
- [ ] **Unit tests exist and pass:**
  ```bash
  python -m pytest backend/tests/ -v --tb=short
  # Expected: 13+ tests pass, 0 failures
  ```
- [ ] **Component tests exist and pass:**
  ```bash
  npm --prefix frontend run test -- --run
  # Expected: 33+ tests pass, 0 failures
  ```
- [ ] **E2E tests structure complete:**
  ```bash
  ls -la e2e/test_*.py
  # Expected: 7 files (conftest, admin_reset, doctor_dispatch, nurse_response, degraded_states, websocket_recovery, concurrent_multiuser)
  ```
- [ ] **Smoke test passes:**
  ```bash
  python scripts/phase5_smoke.py
  # Expected: Full journey completes, all checks pass
  ```

### 4.2 Test Quality Checks
- [ ] **No hardcoded timeouts** — All waits use sensible defaults (e.g., 5000ms max)
- [ ] **Tests are isolated** — Running test B after test A doesn't cause test B to fail
- [ ] **No flaky tests** — Run test suite 3x in a row, all pass each time:
  ```bash
  for i in {1..3}; do
    echo "Run $i:"
    npm --prefix frontend run test -- --run
    echo "---"
  done
  ```
- [ ] **Coverage metrics visible** — At least 70% line coverage for critical paths (auth, alert dispatch)

### 4.3 CI/CD Integration Ready
- [ ] **All tests runnable in CI** — No localhost hardcoding, no user-specific paths
- [ ] **Artifacts collectable** — Test reports, coverage, screenshots can be uploaded
- [ ] **Environment variables documented** — `.env.example` lists required vars (ACUITYNET_JWT_SECRET, DATABASE_URL, etc.)
- [ ] **README includes test commands** — Users can run `npm run test` and `pytest` with confidence

---

## Section 5: Documentation & Setup

### 5.1 README.md Updated
- [ ] **Quick start included** — Clone → install → run: <10 lines of commands
- [ ] **Backend setup documented** — Python venv, Alembic migrations, Uvicorn startup
- [ ] **Frontend setup documented** — npm install, npm run dev
- [ ] **Test instructions clear** — How to run unit tests, component tests, E2E tests
- [ ] **Troubleshooting section** — "Port 8000 in use?" → solution provided
- [ ] **Content verified:**
  ```bash
  cat README.md | grep -E "npm install|python -m pytest|playwright" | wc -l
  # Result: Should be ≥3 (at least 3 test/setup commands documented)
  ```

### 5.2 DEMO-RESET-PATH.md Complete
- [ ] **Prerequisite software listed** — Python 3.10+, Node.js 18+, SQLite3
- [ ] **Step-by-step clone and setup** — Exact commands, no guessing
- [ ] **Database reset procedure** — Clear steps to reset and reseed P-1042
- [ ] **Manual demo walkthrough** — Admin login → historian → dispatch → nurse response
- [ ] **Troubleshooting section** — Common issues and fixes included
- [ ] **Quick-reference commands** — Copy-paste friendly reset commands
- [ ] **Verify completeness:**
  ```bash
  grep -c "Step\|#" DEMO-RESET-PATH.md
  # Result: Should be ≥30 (comprehensive documentation)
  ```

### 5.3 VERIFICATION-CHECKLIST.md (This Document)
- [ ] **All sections present** — 5 major sections (Clinical, UX, Backend, Tests, Docs)
- [ ] **Actionable items** — Each checkbox links to clear verification step
- [ ] **Coverage against ROADMAP** — Checklist mirrors success criteria from ROADMAP.md

### 5.4 Code Comments & Docstrings
- [ ] **Complex functions documented** — dispatch_candidates(), calculate_risk_score() have docstrings
- [ ] **Endpoints documented** — FastAPI docstrings explain request/response format
- [ ] **Test intent clear** — Test function names and docstrings explain what they verify
- [ ] **No TODO/FIXME for shipping** — All TODO items either completed or explicitly marked "post-v1"

---

## Section 6: Compliance & Legal

### 6.1 License & Attribution
- [ ] **LICENSE file present** — e.g., MIT, Apache 2.0, or proprietary
- [ ] **Third-party licenses** — `pip list` and `npm ls --depth=0` show all dependencies
- [ ] **License compatibility** — No GPL dependencies if closed-source (if applicable)
- [ ] **Attribution included** — README.md mentions key libraries (FastAPI, React, Playwright)

### 6.2 Data Handling & Privacy Policy
- [ ] **Terms of use drafted** — If user-facing, privacy policy and ToS link in footer
- [ ] **Data retention policy** — Docs explain how long patient data retained, deletion process
- [ ] **PHI handling documented** — Backend docs note: "Database file contains live patient data; encrypt at rest in production"
- [ ] **HIPAA/GDPR considerations noted** — If applicable, document compliance gaps for post-v1

### 6.3 Security Review Checklist
- [ ] **Secrets not in code** — No `ACUITYNET_JWT_SECRET="hardcoded-value"` in source (use env vars)
- [ ] **Dependencies up-to-date** — No known CVEs:
  ```bash
  pip audit # Python
  npm audit # Node.js
  ```
- [ ] **SQL injection prevented** — All queries use ORM or parameterized statements (SQLAlchemy, no f-strings)
- [ ] **XSS prevention** — React escapes by default; no `dangerouslySetInnerHTML` without review
- [ ] **CORS configured correctly** — Frontend can reach backend, but not overly permissive (not `*`)

---

## Section 7: Final Sign-Off

### Approval Gates

**This section must be completed by designated reviewers before Phase 5-05 is marked COMPLETE and ready to ship.**

| Reviewer Role | Name | Date | Sign-Off |
|---------------|------|------|----------|
| Clinical/Product | _________________ | ________ | ✓ ☐ |
| Engineering Lead | _________________ | ________ | ✓ ☐ |
| QA/Test Lead | _________________ | ________ | ✓ ☐ |
| Security/Compliance | _________________ | ________ | ✓ ☐ |

### Known Limitations & Accepted Risks

List any known issues, TODOs, or scope limitations for v1 (to be addressed in v2):

```
Example:
- [ ] Dark mode not implemented (v2 feature)
- [ ] No real-time WebSocket yet (scheduled for v2)
- [ ] Multi-patient dashboard not supported (single patient v1)
- [ ] Mobile app not tested (desktop/tablet only v1)
```

**Limitations recorded:**
- [ ] ___________________________________________________________________
- [ ] ___________________________________________________________________
- [ ] ___________________________________________________________________

### Ship Decision

**Ready to ship Phase 5-05?**

- ☐ YES — All checkboxes passed, risks accepted, approve merge to main
- ☐ NO — Blockers remain, return to development

**Final comments:**

```
_________________________________________________________________________________
_________________________________________________________________________________
_________________________________________________________________________________
```

---

## Quick Checklist Summary (Printable)

```
[ ] 1.1 No autonomous clinical decisions
[ ] 1.2 Language clarity — no unvalidated claims
[ ] 1.3 Patient data privacy — no PHI leakage
[ ] 2.1 Component rendering & accessibility
[ ] 2.2 State persistence & recovery
[ ] 2.3 Visual consistency & branding
[ ] 2.4 Responsive design
[ ] 3.1 Endpoint security & authorization
[ ] 3.2 Data validation & error handling
[ ] 3.3 Performance & scalability baselines
[ ] 3.4 Logging & monitoring
[ ] 4.1 Test tiers complete (unit, component, E2E)
[ ] 4.2 Test quality checks (no flakes, isolation)
[ ] 4.3 CI/CD integration ready
[ ] 5.1 README.md updated
[ ] 5.2 DEMO-RESET-PATH.md complete
[ ] 5.3 VERIFICATION-CHECKLIST.md present
[ ] 5.4 Code comments & docstrings
[ ] 6.1 License & attribution
[ ] 6.2 Data handling & privacy policy
[ ] 6.3 Security review
[ ] 7 Final sign-off from all reviewers
```

---

## Appendix: Test Command Cheat Sheet

```bash
# Run all unit tests
python -m pytest backend/tests/ -v

# Run all component tests
npm --prefix frontend run test -- --run

# Run specific E2E test file
python -m pytest e2e/test_admin_reset_setup.py -v

# Run with headful Playwright (see browser)
PLAYWRIGHT_HEADLESS=false python -m pytest e2e/test_admin_reset_setup.py -v -s

# Quick lint check
pip install flake8
flake8 backend/app --max-line-length=120 --ignore=E501,E203

# Frontend linting
npm --prefix frontend run lint

# Generate coverage report
python -m pytest backend/tests/ --cov=backend/app --cov-report=html
# Open htmlcov/index.html in browser
```

---

**Document Status:** ✓ Active  
**Last Updated:** 2026-08-30  
**Review Cycle:** Every Phase  
**Owner:** Engineering Lead + Clinical Reviewer
