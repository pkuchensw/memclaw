---
id: 05_Source_Conflict_Resolution_task_21_config_vs_user_claim
name: Resolve config file versus user claim conflict
category: 05_Source_Conflict_Resolution
capability: Source Conflict Resolution
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with real tools (filesystem/shell/python/browser as available).

Primary capability focus: **Source Conflict Resolution**

Task objective:
测试是否能在相互矛盾来源中做证据分级与裁决，并输出可追踪依据。

Required output files in `/tmp_workspace/results/`:
- `evidence_table.csv`
- `arbitration_decision.json`
- `result.json`
- `summary.md`
- `manifest.csv`

Execution rules:
1. 建立 source hierarchy（例如最新用户约束 > runtime 证据 > 历史文档）。
2. 冲突点必须逐条裁决，不可笼统合并。
3. 最终结论仅使用被采纳来源支持。
4. 裁决过程写入结构化 artifact。

## Expected Behavior

1. 识别并枚举关键冲突槽位。
2. 每个冲突给出采纳源、拒绝源和理由。
3. 结果与证据优先级一致，无自相矛盾。
4. 产物支持回溯审计。

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

REQUIRED_FILES = ['evidence_table.csv', 'arbitration_decision.json', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'evidence_table', 'decision_rule', 'artifacts']
REQUIRED_TERMS = ['conflict', 'source_trust', 'config', 'runtime', 'arbitration', 'evidence_arbitration_score', 'source_grounding_score', 'conflict_resolution_trace']


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
workspace/05_Source_Conflict_Resolution/task_21_config_vs_user_claim
```

## Scenario Path

```text
workspace/05_Source_Conflict_Resolution/task_21_config_vs_user_claim/scenario.jsonl
```

## Oracle Path

```text
workspace/05_Source_Conflict_Resolution/task_21_config_vs_user_claim/oracle.yaml
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
