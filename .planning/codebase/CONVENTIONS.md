# Coding Conventions

**Analysis Date:** 2026-08-24

## Naming Patterns

**Files:**
- Python modules use lowercase snake_case, for example `backend/app/vitals/service.py` and `backend/tests/test_vital_contracts.py`.
- React components and their tests use PascalCase names, for example `frontend/src/monitoring/MonitoringPage.tsx` and `frontend/src/monitoring/MonitoringPage.test.tsx`.
- TypeScript contract modules use lowercase names such as `frontend/src/contracts/vitals.ts`.

**Functions:**
- Python functions use snake_case (`create_app`, `resolve_freshness`, `seed_demo_data`).
- React components use PascalCase; local helpers and event-oriented functions use camelCase (`formatTimestamp`, `getCurrentVitals`, `advanceVitals`).
- Test functions use descriptive snake_case behavior statements, usually beginning with `test_`.

**Variables:**
- Python local variables use snake_case (`database_url`, `received_at`, `observations`).
- TypeScript variables use camelCase (`currentObservation`, `selectedInterval`, `fetchMock`).
- Domain identifiers preserve explicit naming in serialized contracts, using snake_case fields such as `patient_id`, `heart_rate_bpm`, and `observed_at`.

**Types:**
- Python uses `PascalCase` for Pydantic models, enums, and service classes (`VitalObservationResponse`, `FreshnessState`, `ObservationService`).
- TypeScript uses `PascalCase` for interfaces and type aliases (`VitalObservation`, `RefreshConfiguration`, `AutomaticRefreshInterval`).
- Literal unions and enum values represent bounded domain states rather than unconstrained strings where practical.

## Code Style

**Formatting:**
- No repository-wide Black, Ruff, Prettier, or ESLint configuration is detected. Preserve the existing four-space Python indentation, double-quoted TypeScript strings, trailing commas in multiline calls, and compact JSX formatting.
- Python type annotations are used throughout application and persistence code, including `Mapped[...]`, `Callable[...]`, and `dict[str, int]`.
- TypeScript is strict with `strict: true`, `noEmit: true`, `isolatedModules: true`, and `forceConsistentCasingInFileNames: true` in `frontend/tsconfig.app.json`.

**Linting:**
- Backend style is not enforced by a dedicated lint command in `backend/pyproject.toml`; pytest is configured at the root `pyproject.toml`.
- Frontend `npm run lint` runs `tsc --noEmit`, so type correctness is the primary automated style gate.
- Keep imports explicit and grouped by external/library imports followed by local application imports, matching `backend/app/main.py` and `frontend/src/monitoring/MonitoringPage.tsx`.

## Import Organization

**Order:**
1. Python standard library imports.
2. Third-party framework, validation, database, or test imports.
3. Local `backend.app` imports.
4. TypeScript third-party imports, then local relative imports; use `import type` for type-only dependencies.

**Path Aliases:**
- No path aliases are configured. Use relative frontend imports and the `backend.app...` package path in backend modules/tests.

## Error Handling

**Patterns:**
- Pydantic models reject invalid input at the contract boundary using `Field`, `Literal`, `ConfigDict(extra="forbid")`, and `model_validator`, as in `backend/app/contracts/vitals.py`.
- FastAPI routes translate known domain/configuration `ValueError` failures into `HTTPException` with explicit 4xx/5xx status codes in `backend/app/main.py`.
- Preserve exception chaining with `raise ... from error` when translating exceptions.
- Frontend API helpers throw `Error` on non-OK responses in `frontend/src/api/client.ts`; UI refresh logic catches expected bounded-scenario `422` responses and switches to manual mode in `frontend/src/monitoring/MonitoringPage.tsx`.
- Tests assert expected failures with `pytest.raises(...)`, response status codes, and negative DOM assertions.

## Logging

**Framework:** console logging is not detected in the sampled application code.

**Patterns:**
- Do not add routine logging for normal fixture or request flow without an established need. Current observability is represented through typed response metadata, freshness state, and explicit HTTP errors.

## Comments

**When to Comment:**
- Code is generally self-explanatory and uses few comments. Prefer descriptive names and small functions over narration.
- Keep comments only for non-obvious domain constraints or operational behavior, such as bounded synthetic scenario rules.

**JSDoc/TSDoc:**
- No JSDoc/TSDoc convention is detected. Public behavior is communicated through TypeScript types, Python annotations, Pydantic contracts, and tests.

## Function Design

**Size:** Keep route handlers and UI effects focused on orchestration; move domain calculations and persistence behavior into modules such as `backend/app/vitals/service.py` and `backend/app/vitals/scenario.py`.

**Parameters:** Use explicit typed parameters. Prefer keyword-only options for policy switches, as `resolve_freshness(..., *, transport_ok=True)` demonstrates.

**Return Values:** Return typed Pydantic responses from API routes and typed promises from frontend API functions. Use `None`/optional values to represent unavailable state rather than sentinel strings.

## Module Design

**Exports:** Export named Python classes/functions and named TypeScript functions/components. Keep implementation details private when they are not part of the module contract, as with `getJson` in `frontend/src/api/client.ts` and `VitalCard` in `frontend/src/monitoring/MonitoringPage.tsx`.

**Barrel Files:** No barrel export convention is detected. Import directly from the owning module.

---

*Convention analysis: 2026-08-24*
