---
id: 07_Goal_Interruption_Resumption_task_35_interrupted_search_task_resume
name: Resume interrupted search synthesis
category: 07_Goal_Interruption_Resumption
capability: Goal Interruption and Task Resumption
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with real tools (filesystem/shell/python/browser as available).

Primary capability focus: **Goal Interruption and Task Resumption**

Task objective:
测试是否能在中断后准确恢复主目标，不丢失进度与约束。

Required output files in `/tmp_workspace/results/`:
- `result.json`
- `summary.md`
- `manifest.csv`

Execution rules:
1. 中断前记录 checkpoint（目标、当前步骤、未完成项）。
2. 处理中断任务后必须恢复到主流程正确位置。
3. 恢复时保持关键约束不漂移。
4. 输出需显示 interruption/resumption 轨迹。

## Expected Behavior

1. 主任务与中断任务边界清晰。
2. 恢复点准确，未重复或跳过关键步骤。
3. 中断期间新增噪声不会污染主目标。
4. 结果包含可机审的恢复证据。

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

REQUIRED_FILES = ['result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'artifacts']
REQUIRED_TERMS = ['capability', 'evidence', 'latest', 'deterministic', 'trace', 'task_resumption_score', 'progress_recovery_score', 'resume_point_correctness']


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
workspace/07_Goal_Interruption_Resumption/task_35_interrupted_search_task_resume
```

## Scenario Path

```text
workspace/07_Goal_Interruption_Resumption/task_35_interrupted_search_task_resume/scenario.jsonl
```

## Oracle Path

```text
workspace/07_Goal_Interruption_Resumption/task_35_interrupted_search_task_resume/oracle.yaml
```

## Skills

```text
checkpointed_interrupt_handling
- snapshot goal state before interruption
- capture pending actions and invariants for exact resume

resumption_pointer_recovery
- restore workflow at the correct unfinished step
- prevent duplicate execution or skipped milestones

goal_invariant_preservation
- keep primary constraints stable across interruption window
- isolate side-task artifacts from main deliverables
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
