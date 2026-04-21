---
id: 02_Version_Update_task_08_api_contract_migration
name: Migrate API contract to new schema version
category: 02_Version_Update
capability: Version Update
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with real tools (filesystem/shell/python/browser as available).

Primary capability focus: **Version Update**

Task objective:
测试是否能在多轮更新链中正确执行“新版本覆盖旧版本”，并避免回退到已废弃状态。

Required output files in `/tmp_workspace/results/`:
- `api_contract_vNext.json`
- `migration_report.md`
- `result.json`
- `summary.md`
- `manifest.csv`

Execution rules:
1. 先回放 `scenario.jsonl`，建立版本链和 superseded 集合。
2. 所有输出基于“最新有效版本”，不得混用旧字段或旧策略。
3. 将每次版本裁决与证据绑定到结构化日志。
4. 产物命名与路径必须稳定、可复现。

## Expected Behavior

1. 识别每个版本槽位（版本号、策略、schema）最终值。
2. 明确列出被废弃版本及废弃原因。
3. 在最终产物中仅体现最新状态，不出现旧状态泄漏。
4. 完成一致性自检并输出可机审结果。

## Grading Criteria

- [ ] Required files exist and are parseable.
- [ ] Capability-specific decision trace is explicit and internally consistent.
- [ ] 关键能力信号在 summary/result 中可检索，不是泛化表述。
- [ ] Manifest paths map to real files in results directory.
- [ ] Final artifacts follow latest valid constraints and reject stale/noise context.

## Automated Checks

```python
import csv
import json
from pathlib import Path

REQUIRED_FILES = ['api_contract_vNext.json', 'migration_report.md', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'state_updates', 'schema_migration', 'artifacts']
REQUIRED_TERMS = ['api_contract', 'migration', 'deprecated_field', 'latest_schema', 'validation', 'latest_state_accuracy', 'superseded_state_avoidance', 'update_chain_grounded']


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
workspace/02_Version_Update/task_08_api_contract_migration
```

## Scenario Path

```text
workspace/02_Version_Update/task_08_api_contract_migration/scenario.jsonl
```

## Oracle Path

```text
workspace/02_Version_Update/task_08_api_contract_migration/oracle.yaml
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
