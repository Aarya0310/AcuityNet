---
schema_version: 1
open_count: 2
waived_count: 0
fixed_count: 0
total_count: 2
last_updated: 2026-08-26T10:37:54.245Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 04 | unrun-verify | backend/tests/test_historian.py |  | Focused historian integration suite could not run because active interpreter lacks pinned PyJWT dependency. | open |  | 2026-08-26T10:11:11.659Z |  |
| 2 | 04 | unrun-verify | backend/tests/test_dispatch.py |  | Backend dispatch and lifecycle verification could not run because PyJWT is missing from the environment during test collection. | open |  | 2026-08-26T10:37:54.245Z |  |

````json
[
  {
    "id": 1,
    "kind": "unrun-verify",
    "phase": "04",
    "file": "backend/tests/test_historian.py",
    "line": null,
    "description": "Focused historian integration suite could not run because active interpreter lacks pinned PyJWT dependency.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-26T10:11:11.659Z",
    "resolved_at": null
  },
  {
    "id": 2,
    "kind": "unrun-verify",
    "phase": "04",
    "file": "backend/tests/test_dispatch.py",
    "line": null,
    "description": "Backend dispatch and lifecycle verification could not run because PyJWT is missing from the environment during test collection.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-26T10:37:54.245Z",
    "resolved_at": null
  }
]
````
