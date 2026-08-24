# Testing Patterns

**Analysis Date:** 2026-08-24

## Test Framework

**Runner:**
- Backend: `pytest==9.1.1`, configured by `[tool.pytest.ini_options]` in `pyproject.toml` with `backend/tests` as `testpaths` and the repository root on `pythonpath`.
- Frontend: `vitest==4.1.11` with `@testing-library/react==16.3.2`, `@testing-library/jest-dom==6.9.1`, and `jsdom==27.1.0`; configuration is in `frontend/vite.config.ts`.

**Assertion Library:**
- Backend uses native `assert` statements and `pytest.raises`.
- Frontend uses Vitest `expect` plus Testing Library DOM matchers loaded by `frontend/src/test-setup.ts`.

**Run Commands:**
```bash
python -m pytest                         # All backend tests from repository root
python -m pytest backend/tests/test_vitals_api.py -q  # One backend slice
python scripts/phase1_smoke.py           # End-to-end smoke runner
npm --prefix frontend run test -- --run  # All frontend tests once
npm --prefix frontend run test           # Vitest watch mode
npm --prefix frontend run build          # Typecheck and production build
npm --prefix frontend run lint           # TypeScript no-emit check
```

## Test File Organization

**Location:**
- Backend tests are separate from implementation under `backend/tests/`.
- Frontend tests are colocated with the component under test, currently `frontend/src/monitoring/MonitoringPage.test.tsx`.

**Naming:**
- Backend files use `test_<subject>.py`; test functions use `test_<behavior>`.
- Frontend files use `<Component>.test.tsx`; suites use `describe("Component", ...)` and cases use `it("...")`.

**Structure:**
```text
backend/tests/test_*.py
frontend/src/**/*.test.tsx
frontend/src/test-setup.ts
```

## Test Structure

**Suite Organization:**
```typescript
describe("MonitoringPage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn(...));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("renders ...", () => {
    render(<MonitoringPage observation={observation} />);
    expect(screen.getByRole("heading", { name: /Avery Morgan/i })).toBeInTheDocument();
  });
});
```

**Patterns:**
- Backend tests arrange a temporary SQLite URL, create/migrate the app or engine, execute one focused behavior, then assert contracts, persistence, or HTTP results.
- Use `tmp_path` for database isolation; do not share mutable database state between tests.
- Use injected clocks (`create_app(..., clock=lambda: ...)`) for freshness and timestamp assertions.
- Frontend tests call `render`, await asynchronous effects inside `act`, and use semantic queries such as `getByRole`, `getByText`, and `queryByText`.
- Parameterize repeated state coverage with `it.each`, as freshness-state rendering does in `frontend/src/monitoring/MonitoringPage.test.tsx`.

## Mocking

**Framework:**
- Backend tests prefer real FastAPI `TestClient`, SQLAlchemy, migrations, and SQLite. No backend mocking library or mock-heavy fixture layer is detected.
- Frontend uses Vitest `vi.stubGlobal`, `vi.fn`, fake timers, and a small local `response` helper to mock `fetch`.

**Patterns:**
```typescript
vi.stubGlobal("fetch", vi.fn((url: string) => {
  if (url.endsWith("/api/v1/configuration")) {
    return response({ supported_intervals: [5, 10, 30, "manual"], default_interval: 10 });
  }
  return response(observation);
}));
```

**What to Mock:**
- Mock browser network boundaries in component tests, especially configuration, advance, and current-vitals requests.
- Stub time when testing interval-driven behavior; use `vi.advanceTimersByTimeAsync` inside `act`.

**What NOT to Mock:**
- Keep backend persistence, migration, seed, contract validation, and FastAPI routing real in integration tests. The existing tests intentionally verify foreign keys, idempotent seed behavior, and response serialization.
- Do not mock the component DOM; assert the rendered accessible interface.

## Fixtures and Factories

**Test Data:**
```python
database_url = f"sqlite:///{tmp_path / 'acuitynet.db'}"
app = create_app(database_url, clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))
with TestClient(app) as client:
    response = client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0})
```

```typescript
const observation: VitalObservation = {
  patient_id: "P-1042",
  patient: { patient_id: "P-1042", display_name: "Avery Morgan", bed_id: "ICU-07", unit: "ICU" },
  // Remaining fields provide a complete typed response fixture.
};
```

**Location:**
- Python test fixtures are local to each test; shared production fixture construction lives in `backend/app/seed/demo_data.py`.
- The frontend observation fixture is module-local in `frontend/src/monitoring/MonitoringPage.test.tsx`.

## Coverage

**Requirements:** No coverage threshold or coverage configuration is detected. Existing tests cover the Phase 1 scenario, contracts, safety boundary, migration constraints, seed/reset behavior, API flows, and monitoring refresh behavior, but there is no automated percentage gate.

**View Coverage:** No repository coverage command is configured. Add a runner-specific coverage command only with corresponding configuration and dependency changes.

## Test Types

**Unit Tests:**
- Pure/domain unit coverage includes `P1042Scenario` bounds and exact tuples, freshness boundary resolution, and Pydantic validation in `backend/tests/test_scenario.py` and `backend/tests/test_vital_contracts.py`.

**Integration Tests:**
- `backend/tests/test_vitals_api.py` and `backend/tests/test_walking_skeleton.py` exercise FastAPI routes with real migration, seed, SQLite persistence, and serialized responses.
- `backend/tests/test_migrations.py` checks schema initialization, foreign-key enforcement, and reset ordering.

**E2E Tests:**
- `scripts/phase1_smoke.py` launches a Uvicorn child process and checks health/current-vitals behavior over HTTP. No browser E2E framework is detected.

## Common Patterns

**Async Testing:**
```typescript
await act(async () => {
  await vi.advanceTimersByTimeAsync(5000);
  await Promise.resolve();
  await Promise.resolve();
});
```

**Error Testing:**
```python
with pytest.raises(ValidationError):
    SyntheticProvenance(source_kind="retrospective", ...)
```

- HTTP failures are asserted through status codes (`404`, `422`) and frontend behavior is verified by stubbing a failed response and checking that automatic refresh returns to `manual`.
- Keep assertions focused on observable contracts: exact safety metadata, bounded sequences, persistence counts, status transitions, and accessible UI output.

---

*Testing analysis: 2026-08-24*
