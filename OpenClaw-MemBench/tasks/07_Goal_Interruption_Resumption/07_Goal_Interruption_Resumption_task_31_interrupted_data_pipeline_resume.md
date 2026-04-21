---
id: 07_Goal_Interruption_Resumption_task_31_interrupted_data_pipeline_resume
name: Resume interrupted data pipeline
category: 07_Goal_Interruption_Resumption
capability: Goal Interruption and Task Resumption
timeout_seconds: 900
---

## Prompt

You are an OpenClaw benchmark agent running in a WildClawBench/ClawEval-style tool-rich environment.

Primary capability focus: **Goal Interruption and Task Resumption**

Mission:
Resume interrupted data pipeline exactly from checkpoint without redoing completed stages.

Execution requirements:
1. Replay prior turns from `/tmp_workspace/scenario.jsonl` and apply only the latest applicable constraints.
2. Use tools (filesystem, python, bash) rather than pure narration when evidence/action is required.
3. For conflicting or stale context, provide explicit arbitration rationale tied to concrete sources.
4. Produce deterministic artifacts under `/tmp_workspace/results/`.

Required deliverables:
- resume_state.json
- pipeline_progress.md
- result.json
- summary.md
- manifest.csv

Hard constraints:
- Do not collapse all history into one generic summary; route memory by capability.
- Treat superseded/invalid context as non-authoritative.
- Keep artifact names and schemas exactly as requested.
- Final answer must include structured blocks:
  - `<<<RESULT_JSON>>> ... <<<END_RESULT_JSON>>>`
  - `<<<SUMMARY_MD>>> ... <<<END_SUMMARY_MD>>>`
  - `<<<MANIFEST_CSV>>> ... <<<END_MANIFEST_CSV>>>`

## Expected Behavior

1. Capability diagnosis:
- Identify which episode segments drive **Goal Interruption and Task Resumption**.
- Separate active constraints from stale/noise context.

2. Tool-grounded execution:
- Perform concrete actions in workspace and generate required artifacts.
- Record source references (file/log/thread) used for key decisions.

3. Capability-first completion:
- Demonstrate Resume interrupted goal from exact checkpoint with progress integrity.
- Explain why alternatives were rejected.

4. Deterministic closure:
- Validate generated files and schema.
- Emit manifest aligned to actual outputs.

## Grading Criteria

- [ ] Required files exist and are parseable.
- [ ] Result JSON exposes capability-specific decision fields.
- [ ] Summary contains capability evidence, not only generic wording.
- [ ] Manifest paths map to real files in results directory.
- [ ] Capability signal is explicit and consistent with final decision.
- [ ] task_resumption_score
- [ ] progress_recovery_score
- [ ] resume_point_correctness

## Automated Checks

```python
import csv
import json
from pathlib import Path

REQUIRED_FILES = ['resume_state.json', 'pipeline_progress.md', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'resume_state', 'checkpoint_used', 'artifacts']
REQUIRED_TERMS = ['resume', 'checkpoint', 'processed', 'pending', 'continuation_point', 'task_resumption_score', 'progress_recovery_score', 'resume_point_correctness']


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
    blob = "
".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict)).lower()
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
workspace/07_Goal_Interruption_Resumption/task_31_interrupted_data_pipeline_resume
```

## Scenario Path

```text
workspace/07_Goal_Interruption_Resumption/task_31_interrupted_data_pipeline_resume/scenario.jsonl
```

## Oracle Path

```text
workspace/07_Goal_Interruption_Resumption/task_31_interrupted_data_pipeline_resume/oracle.yaml
```

## Skills

```text
interruption_resume
memory_routing
shell_safety
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
