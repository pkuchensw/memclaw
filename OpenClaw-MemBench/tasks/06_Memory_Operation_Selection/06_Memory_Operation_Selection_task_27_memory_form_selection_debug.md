---
id: 06_Memory_Operation_Selection_task_27_memory_form_selection_debug
name: Select memory form in debugging workflow
category: 06_Memory_Operation_Selection
capability: Memory Operation Selection
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with real tools (filesystem/shell/python/browser as available).

Primary capability focus: **Memory Operation Selection**

Task objective:
测试是否能根据子任务类型选择正确记忆操作（context/state/procedural/anti/evidence）。

Required output files in `/tmp_workspace/results/`:
- `memory_routing.json`
- `debug_routing.md`
- `result.json`
- `summary.md`
- `manifest.csv`

Execution rules:
1. 对每个子步骤先判定所需 memory operation。
2. 禁止把所有信息塞进单一记忆槽。
3. 记录 operation selection 的触发条件。
4. 最终结果需体现 memory routing 决策有效性。

## Expected Behavior

1. 给出子任务 -> memory operation 映射表。
2. 体现 context_cache/state_memory/procedural_memory/anti_memory/evidence_graph 的分工。
3. 错误路由被识别并修正。
4. 输出可用于分析路由策略质量。

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

REQUIRED_FILES = ['memory_routing.json', 'debug_routing.md', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'memory_forms', 'routing_log', 'artifacts']
REQUIRED_TERMS = ['memory_form', 'debug', 'routing', 'anti_memory', 'state_memory', 'memory_operation_accuracy', 'wrong_form_memory_penalty', 'routing_explainability']


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
workspace/06_Memory_Operation_Selection/task_27_memory_form_selection_debug
```

## Scenario Path

```text
workspace/06_Memory_Operation_Selection/task_27_memory_form_selection_debug/scenario.jsonl
```

## Oracle Path

```text
workspace/06_Memory_Operation_Selection/task_27_memory_form_selection_debug/oracle.yaml
```

## Skills

```text
memory_operation_routing
- choose memory form per subproblem intent and horizon
- avoid single-bucket memory collapse

operation_selection_justification
- explain why each slot uses context/state/procedural/anti/evidence memory
- update routing when task phase changes

routing_quality_control
- detect misrouted facts and relocate to proper memory form
- keep decision trail auditable
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
