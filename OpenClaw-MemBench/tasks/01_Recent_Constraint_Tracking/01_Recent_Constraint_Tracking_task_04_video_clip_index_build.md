---
id: 01_Recent_Constraint_Tracking_task_04_video_clip_index_build
name: Build indexed clips from long video
category: 01_Recent_Constraint_Tracking
capability: Recent Constraint Tracking
timeout_seconds: 900
---

## Prompt

You are running in OpenClaw with full tool access.

Your task is to complete a multi-episode workflow and produce final artifacts in /tmp_workspace/results/.

### Episode setup

1. Read prior constraints from /tmp_workspace/episodes/ and /tmp_workspace/evidence/.
2. Continue from the latest state instead of restarting blindly.
3. If source conflicts exist, resolve them with explicit evidence priority.

### Deliverables

- One primary artifact: result.json
- One human-readable report: summary.md
- One machine-checkable manifest: manifest.csv

### Hard constraints

- Preserve the latest constraints, not superseded ones.
- Avoid repeating known mistakes from prior episodes.
- Keep file names and schema exact.

## Expected Behavior

1. Parse prior episode context and active constraints.
2. Execute tool actions and produce deterministic outputs.
3. Validate artifacts and include evidence-based justification.
4. Save all outputs under /tmp_workspace/results/.

## Grading Criteria

- [ ] result.json exists and is parseable.
- [ ] summary.md explains decisions and evidence.
- [ ] manifest.csv matches produced files.
- [ ] Latest constraints are applied.
- [ ] No repeated known failure mode.

## Automated Checks

import csv
import json
from pathlib import Path

def _has_non_empty_text(path: Path) -> float:
    if not path.exists():
        return 0.0
    return 1.0 if path.read_text(encoding="utf-8").strip() else 0.0

def _json_valid(path: Path) -> float:
    if not path.exists():
        return 0.0
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return 1.0
    except Exception:
        return 0.0

def _csv_valid(path: Path) -> float:
    if not path.exists():
        return 0.0
    try:
        with path.open("r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        return 1.0 if len(rows) >= 1 else 0.0
    except Exception:
        return 0.0

def grade(transcript=None, workspace_path="/tmp_workspace"):
    result_json = Path(workspace_path) / "results" / "result.json"
    summary_md = Path(workspace_path) / "results" / "summary.md"
    manifest_csv = Path(workspace_path) / "results" / "manifest.csv"

    scores = {
        "result_json_valid": _json_valid(result_json),
        "summary_present": _has_non_empty_text(summary_md),
        "manifest_valid": _csv_valid(manifest_csv),
        "constraint_retention": 0.0,
        "mistake_avoidance": 0.0,
        "evidence_consistency": 0.0,
    }
    scores["overall_score"] = round(sum(scores.values()) / len(scores), 4)
    return scores

## Workspace Path

workspace/01_Recent_Constraint_Tracking/task_04_video_clip_index_build

## Skills


## Env


## Warmup


