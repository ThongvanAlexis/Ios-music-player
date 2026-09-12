---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-09-12T18:27:21.120Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01 | deviation | MusicPlayerTests/NativeTracerTests.swift |  | Native tests passed after implementation; an intentional behavior RED run before implementation was not performed. | open |  | 2026-09-12T18:27:21.120Z |  |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "01",
    "file": "MusicPlayerTests/NativeTracerTests.swift",
    "line": null,
    "description": "Native tests passed after implementation; an intentional behavior RED run before implementation was not performed.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-12T18:27:21.120Z",
    "resolved_at": null
  }
]
````
