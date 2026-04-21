---
id: 05_Source_Conflict_Resolution_task_22_doc_vs_runtime_logs
name: Resolve docs versus runtime logs mismatch
category: 05_Source_Conflict_Resolution
capability: Source Conflict Resolution
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with real tools (filesystem/shell/python/browser as available).

Primary capability focus: **Source Conflict Resolution**

Task objective:
Test whether the agent can perform evidence ranking and arbitration among conflicting sources, and output traceable justifications.

Required output files in `/tmp_workspace/results/`:
- `evidence_table.csv`
- `runtime_grounded_decision.md`
- `result.json`
- `summary.md`
- `manifest.csv`

Execution rules:
1. Establish source hierarchy (e.g., latest user constraints > runtime evidence > historical docs).
2. Conflicts must be resolved claim-by-claim; no general merging allowed.
3. Final conclusions must only use supported sources that were adopted.
4. Arbitration process must be written to structured artifacts.

## Expected Behavior

1. Identify and enumerate key conflicting slots.
2. For each conflict, give adopted source, rejected source, and rationale.
3. Results are consistent with evidence priority, with no contradictions.
4. Artifacts support backtracking audit.

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

REQUIRED_FILES = ['evidence_table.csv', 'runtime_grounded_decision.md', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'evidence_table', 'chosen_source', 'artifacts']
REQUIRED_TERMS = ['conflict', 'runtime_log', 'timestamp', 'doc_stale', 'arbitration', 'evidence_arbitration_score', 'source_grounding_score', 'conflict_resolution_trace']


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
workspace/05_Source_Conflict_Resolution/task_22_doc_vs_runtime_logs
```

## Scenario Path

```text
workspace/05_Source_Conflict_Resolution/task_22_doc_vs_runtime_logs/scenario.jsonl
```

## Oracle Path

```text
workspace/05_Source_Conflict_Resolution/task_22_doc_vs_runtime_logs/oracle.yaml
```

## Skills

```text
evidence_hierarchy_building
- rank sources by recency, authority, and executability
- normalize conflicting claims into comparable slots

conflict_slot_arbitration
- resolve claim-by-claim contradictions with explicit rationale
- reject low-trust stale sources when contradicted

verdict_traceability
- bind each final decision to concrete source references
- keep arbitration log machine-checkable
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
