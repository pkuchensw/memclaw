---
id: <category>_task_<N>_<short_name>
name: Human-readable task name
category: <category>
capability: <capability_name>
timeout_seconds: 900
---

## Prompt

You are running in an OpenClaw workspace.

Use tools (browser, bash, python, file system) to complete the task.
Save all deliverables to /tmp_workspace/results/ unless otherwise specified.

Before execution, replay prior turns from /tmp_workspace/scenario.jsonl and apply latest constraints.
If compression checkpoints are present, maintain traceability of what was retained vs compacted.

### Constraints

- Keep outputs deterministic.
- Follow schema and file naming exactly.
- Do not skip validation steps.

## Expected Behavior

1. Read constraints from prior episode notes and files.
2. Execute tool-driven steps.
3. Produce required outputs.
4. Validate outputs before finishing.

## Grading Criteria

- [ ] Output files exist in required paths.
- [ ] Required schema is satisfied.
- [ ] Constraints from prior episodes are preserved.
- [ ] Final result is consistent with tool evidence.

## Automated Checks

```python
import json
from pathlib import Path

def _exists(path: str) -> float:
    return 1.0 if Path(path).exists() else 0.0

def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    # Replace with task-specific checks.
    scores = {
        "files_exist": _exists(f"{workspace_path}/results"),
        "format_valid": 0.0,
        "constraint_preserved": 0.0,
        "evidence_consistent": 0.0,
    }
    scores["overall_score"] = round(sum(scores.values()) / len(scores), 4)
    return scores
```

## Workspace Path

```text
workspace/<category>/task_<N>_<short_name>
```

## Scenario Path

```text
workspace/<category>/task_<N>_<short_name>/scenario.jsonl
```

## Oracle Path

```text
workspace/<category>/task_<N>_<short_name>/oracle.yaml
```

## Skills

```text
memory_routing
shell_safety
```

## Env

```text
```

## Warmup

```bash
```
