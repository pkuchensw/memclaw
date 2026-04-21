---
id: 03_Procedure_Transfer_task_13_table_cleaning_template_transfer
name: Transfer table cleaning template to new data
category: 03_Procedure_Transfer
capability: Procedure Transfer
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with real tools (filesystem/shell/python/browser as available).

Primary capability focus: **Procedure Transfer**

Task objective:
测试是否能把“已验证流程骨架”迁移到新任务域，并仅做必要适配。

Required output files in `/tmp_workspace/results/`:
- `clean_table.csv`
- `cleaning_template.md`
- `result.json`
- `summary.md`
- `manifest.csv`

Execution rules:
1. 先抽取旧任务中的可复用步骤模板。
2. 针对新域输入做步骤映射，不允许无关重写。
3. 显式标注“复用步骤”与“适配步骤”。
4. 输出应体现减少试错次数和稳定流程迁移。

## Expected Behavior

1. 给出源流程到目标流程的步骤对齐关系。
2. 保留核心 procedure skeleton，仅修改必要参数。
3. 解释为什么不采用从零重建方案。
4. 产物可重放且字段一致。

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

REQUIRED_FILES = ['clean_table.csv', 'cleaning_template.md', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'reused_procedure', 'adapted_validators', 'artifacts']
REQUIRED_TERMS = ['table_cleaning', 'template', 'reuse', 'validator', 'adaptation', 'procedure_reuse_score', 'adaptation_correctness', 'trial_reduction']


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
workspace/03_Procedure_Transfer/task_13_table_cleaning_template_transfer
```

## Scenario Path

```text
workspace/03_Procedure_Transfer/task_13_table_cleaning_template_transfer/scenario.jsonl
```

## Oracle Path

```text
workspace/03_Procedure_Transfer/task_13_table_cleaning_template_transfer/oracle.yaml
```

## Skills

```text
procedure_skeleton_reuse
- extract validated step template from prior solved workflow
- preserve invariant step order during transfer

domain_adaptation_mapping
- map source-domain steps to target-domain inputs/outputs
- isolate minimal adaptations and avoid full rewrite

trial_reduction_execution
- execute transferred plan with fewer exploratory retries
- log which steps were reused vs adapted
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
