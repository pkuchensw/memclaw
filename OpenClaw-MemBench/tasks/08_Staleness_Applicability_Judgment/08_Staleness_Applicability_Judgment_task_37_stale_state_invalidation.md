---
id: 08_Staleness_Applicability_Judgment_task_37_stale_state_invalidation
name: Invalidate stale state before execution
category: 08_Staleness_Applicability_Judgment
capability: Staleness and Applicability Judgment
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with real tools (filesystem/shell/python/browser as available).

Primary capability focus: **Staleness and Applicability Judgment**

Task objective:
Test whether the agent can judge when context is “stale” or “still applicable”, avoiding blind reuse of old memories.

Required output files in `/tmp_workspace/results/`:
- `staleness_decision.json`
- `state_invalidation.md`
- `result.json`
- `summary.md`
- `manifest.csv`

Execution rules:
1. Perform staleness judgment on candidate memories (time, version, scope, compatibility).
2. Only reuse historical rules when applicability conditions are met.
3. Give invalidation reasons for invalid memories.
4. Output must distinguish three states: active / stale / conditional.

## Expected Behavior

1. Establish applicability judgment criteria and apply them item by item.
2. Clearly label which old rules can be reused and which must be deprecated.
3. Final behavior is consistent with judgment results.
4. Results facilitate subsequent automatic auditing.

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

REQUIRED_FILES = ['staleness_decision.json', 'state_invalidation.md', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'staleness_findings', 'state_chain', 'artifacts']
REQUIRED_TERMS = ['stale_state', 'invalidate', 'latest_state', 'superseded', 'applicability', 'staleness_judgment_score', 'stale_reuse_penalty', 'scope_applicability_accuracy']


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
workspace/08_Staleness_Applicability_Judgment/task_37_stale_state_invalidation
```

## Scenario Path

```text
workspace/08_Staleness_Applicability_Judgment/task_37_stale_state_invalidation/scenario.jsonl
```

## Oracle Path

```text
workspace/08_Staleness_Applicability_Judgment/task_37_stale_state_invalidation/oracle.yaml
```

## Skills

```text
staleness_classification
- evaluate memories by recency, version drift, and scope fit
- classify entries into active/stale/conditional sets

applicability_gating
- apply historical rules only when compatibility checks pass
- block stale rules from influencing final outputs

validity_audit_tracing
- log invalidation reasons and applicability evidence
- keep decision trace machine-checkable
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
