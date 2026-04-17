---
id: 08_Staleness_Applicability_Judgment_task_36_stale_procedure_detection
name: Detect stale procedure and adapt
category: 08_Staleness_Applicability_Judgment
capability: Staleness and Applicability Judgment
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

CAPABILITY_KEYWORDS = {
    "01_Recent_Constraint_Tracking": ["constraint", "latest", "path", "schema"],
    "02_Version_Update": ["version", "update", "supersede", "latest"],
    "03_Procedure_Transfer": ["procedure", "pipeline", "reuse", "transfer"],
    "04_Repeated_Mistake_Prevention": ["mistake", "avoid", "guard", "checklist"],
    "05_Source_Conflict_Resolution": ["conflict", "evidence", "source", "priority"],
    "06_Memory_Operation_Selection": ["memory", "select", "operation", "route"],
    "07_Goal_Interruption_Resumption": ["resume", "interruption", "state", "progress"],
    "08_Staleness_Applicability_Judgment": ["stale", "applicable", "scope", "deprecated"],
}


def _safe_read(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _json_valid(path: Path) -> tuple[float, dict]:
    if not path.exists():
        return 0.0, {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return 1.0, data if isinstance(data, dict) else {}
    except Exception:
        return 0.0, {}


def _manifest_score(path: Path, results_dir: Path) -> tuple[float, float]:
    if not path.exists():
        return 0.0, 0.0
    try:
        with path.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return 0.0, 0.0

    if not rows:
        return 0.2, 0.0

    exists = 0
    for r in rows:
        rel = (r.get("path") or "").strip()
        if rel and (results_dir / rel).exists():
            exists += 1
    ratio = exists / max(1, len(rows))
    score = 0.4 + 0.6 * ratio
    return score, ratio


def _capability_signal(summary_text: str, workspace_path: str) -> float:
    parts = Path(workspace_path).parts
    cat = ""
    for p in parts:
        if p.startswith("0") and "_" in p:
            cat = p
    kws = CAPABILITY_KEYWORDS.get(cat, ["task", "result"])
    text = summary_text.lower()
    hits = sum(1 for k in kws if k in text)
    return hits / max(1, len(kws))


def grade(transcript=None, workspace_path="/tmp_workspace"):
    results_dir = Path(workspace_path) / "results"
    result_json_path = results_dir / "result.json"
    summary_md_path = results_dir / "summary.md"
    manifest_csv_path = results_dir / "manifest.csv"

    json_score, json_obj = _json_valid(result_json_path)
    summary_text = _safe_read(summary_md_path)
    summary_len_score = min(1.0, len(summary_text.strip()) / 300.0)

    manifest_score, manifest_exists_ratio = _manifest_score(manifest_csv_path, results_dir)

    transcript = transcript or []
    assistant_text = ""
    for m in transcript:
        if isinstance(m, dict) and m.get("role") == "assistant":
            assistant_text = str(m.get("content", "") or "")
    assistant_score = min(1.0, len(assistant_text.strip()) / 200.0)

    task_id_match = 1.0 if isinstance(json_obj, dict) and json_obj.get("task_id") else 0.0
    capability_signal = _capability_signal(summary_text + "\n" + assistant_text, workspace_path)

    scores = {
        "result_json_valid": round(json_score, 4),
        "summary_length": round(summary_len_score, 4),
        "manifest_quality": round(manifest_score, 4),
        "manifest_paths_exist_ratio": round(manifest_exists_ratio, 4),
        "assistant_substance": round(assistant_score, 4),
        "task_id_presence": round(task_id_match, 4),
        "capability_signal": round(capability_signal, 4),
    }
    scores["overall_score"] = round(sum(scores.values()) / len(scores), 4)
    return scores

## Workspace Path

workspace/08_Staleness_Applicability_Judgment/task_36_stale_procedure_detection

## Skills


## Env


## Warmup


