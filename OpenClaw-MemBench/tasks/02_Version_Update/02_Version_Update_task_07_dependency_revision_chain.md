---
id: 02_Version_Update_task_07_dependency_revision_chain
name: Apply dependency revision chain safely
category: 02_Version_Update
capability: Version Update
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with real tools (filesystem/shell/python/browser as available).

Primary capability focus: **Version Update**

Task objective:
Test whether the agent can correctly execute "new version overrides old version" across multiple update rounds, and avoid reverting to deprecated states.

Required output files in `/tmp_workspace/results/`:
- `dependency_decision.json`
- `dependency_plan.md`
- `result.json`
- `summary.md`
- `manifest.csv`

Execution rules:
1. Replay `scenario.jsonl` first to build the version chain and superseded set.
2. All outputs must be based on the "latest valid version"; mixing old fields or old policies is prohibited.
3. Bind each version arbitration decision to evidence in structured logs.
4. Artifact naming and paths must be stable and reproducible.

## Expected Behavior

1. Identify the final values for each version slot (version number, policy, schema).
2. Explicitly list superseded versions and the reasons for their deprecation.
3. Final artifacts must reflect only the latest state, with no leakage of old states.
4. Complete self-consistency checks and output machine-auditable results.

## Grading Criteria

- [ ] Required files exist and are parseable.
- [ ] Capability-specific decision trace is explicit and internally consistent.
- [ ] Key capability signals are retrievable in summary/result, not generic statements.
- [ ] Manifest paths map to real files in results directory.
- [ ] Final artifacts follow latest valid constraints and reject stale/noise context.

## Automated Checks

```python
import csv
import json
from pathlib import Path

REQUIRED_FILES = ['dependency_decision.json', 'dependency_plan.md', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'state_updates', 'superseded_versions', 'artifacts']
REQUIRED_TERMS = ['dependency', 'revision', 'superseded', 'lock', 'latest', 'latest_state_accuracy', 'superseded_state_avoidance', 'update_chain_grounded']


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _required_files_score(results_dir: Path):
    exists = 0
    for rel in REQUIRED_FILES:
        if (results_dir / rel).exists():
            exists += 1
    return exists / max(1, len(REQUIRED_FILES))


def _manifest_score(manifest_path: Path, results_dir: Path):
    if not manifest_path.exists():
        return 0.0
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return 0.0
    if not rows:
        return 0.0
    ok = 0
    for r in rows:
        p = (r.get("path") or "").strip()
        if p and (results_dir / p).exists():
            ok += 1
    return ok / max(1, len(rows))


def _json_key_score(obj):
    if not isinstance(obj, dict):
        return 0.0
    hits = sum(1 for k in REQUIRED_JSON_KEYS if k in obj)
    return hits / max(1, len(REQUIRED_JSON_KEYS))


def _summary_term_score(text: str):
    low = text.lower()
    hits = sum(1 for t in REQUIRED_TERMS if t in low)
    return hits / max(1, len(REQUIRED_TERMS))


def _transcript_evidence_score(transcript):
    transcript = transcript or []
    blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict)).lower()
    cues = ["source", "latest", "constraint", "evidence", "artifact"]
    hits = sum(1 for c in cues if c in blob)
    return hits / len(cues)


def grade(transcript=None, workspace_path="/tmp_workspace"):
    results_dir = Path(workspace_path) / "results"
    result_json = results_dir / "result.json"
    summary_md = results_dir / "summary.md"
    manifest_csv = results_dir / "manifest.csv"

    obj = _load_json(result_json)
    summary_text = _read(summary_md)

    scores = {
        "required_files": round(_required_files_score(results_dir), 4),
        "result_json_valid": 1.0 if isinstance(obj, dict) else 0.0,
        "json_key_coverage": round(_json_key_score(obj), 4),
        "summary_capability_signal": round(_summary_term_score(summary_text), 4),
        "manifest_consistency": round(_manifest_score(manifest_csv, results_dir), 4),
        "transcript_evidence_signal": round(_transcript_evidence_score(transcript), 4),
    }
    scores["overall_score"] = round(sum(scores.values()) / len(scores), 4)
    return scores
```

## Workspace Path

```text
workspace/02_Version_Update/task_07_dependency_revision_chain
```

## Scenario Path

```text
workspace/02_Version_Update/task_07_dependency_revision_chain/scenario.jsonl
```

## Oracle Path

```text
workspace/02_Version_Update/task_07_dependency_revision_chain/oracle.yaml
```

## Skills

```text
version_chain_tracking
- parse semver/state update packets and build supersession DAG
- reject obsolete pins and deprecated migration branches

supersession_arbitration
- resolve conflicting updates by recency + authority
- record replacement rationale with evidence pointers

state_consistency_guard
- ensure final artifacts only reflect latest version state
- block mixed-version field drift
```

## Env

```text
OPENCLAW_CONTEXT_PROFILE=benchmark
OPENCLAW_COMPRESSION_METHOD=lcm-proxy
OPENCLAW_CONTEXT_BUDGET_CHARS=12000
```

## Warmup

```bash
mkdir -p /tmp_workspace/results
```
