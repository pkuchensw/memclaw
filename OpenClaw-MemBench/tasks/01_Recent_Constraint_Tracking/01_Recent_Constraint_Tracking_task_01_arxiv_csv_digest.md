---
id: 01_Recent_Constraint_Tracking_task_01_arxiv_csv_digest
name: ArXiv RL-memory digest with hard slot constraints
category: 01_Recent_Constraint_Tracking
capability: Recent Constraint Tracking
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with browser, bash, python, and filesystem tools.

Primary capability focus: **Recent Constraint Tracking**

Task objective:
Build a deterministic paper digest CSV for RL-memory-agent papers, while correctly honoring the **latest** slot constraints after several near-duplicate and misleading instructions.

Required output files in `/tmp_workspace/results/`:
- `arxiv_memory_rl.csv`
- `constraint_trace.json`
- `result.json`
- `summary.md`
- `manifest.csv`

Strict slot constraints (latest version wins):
1. Year range must be `2024-2025` (inclusive).
2. Keep only papers tagged to `reinforcement learning` + `memory agent`.
3. CSV columns must be exactly: `title,authors,year,url,topic_tag`.
4. Output path is fixed to `/tmp_workspace/results/arxiv_memory_rl.csv`.
5. Artifact format must be CSV only (not markdown table, not JSON for the main digest).

Execution rules:
1. Replay `/tmp_workspace/scenario.jsonl` first; apply newest constraints and ignore superseded ones.
2. Use real tools for evidence-producing steps.
3. If sources conflict, add arbitration rationale in `constraint_trace.json`.
4. Return deterministic outputs only.

## Expected Behavior

1. Identify active slot constraints from noisy history and track superseded variants.
2. Use browser/web or local fixtures to collect candidate papers.
3. Enforce slot-level filtering and deterministic CSV schema.
4. Produce `constraint_trace.json` that maps each final slot to evidence.
5. Validate file existence, column order, and year/topic filters before finish.

## Grading Criteria

- [ ] Required files exist and are parseable.
- [ ] CSV schema and order exactly match required slots.
- [ ] Latest slot constraints are used; stale constraints are not applied.
- [ ] `constraint_trace.json` shows evidence-grounded slot arbitration.
- [ ] Manifest paths map to real files in results directory.
- [ ] Capability signal is explicit: constraint retention over noisy turns.

## Automated Checks

```python
import csv
import json
from pathlib import Path

REQUIRED_FILES = ['arxiv_memory_rl.csv', 'constraint_trace.json', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'slot_constraints', 'arbitration', 'artifacts']
REQUIRED_TERMS = ['2024', '2025', 'topic_tag', 'constraint', 'latest', 'superseded', 'slot']


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

    csv_score = 0.0
    csv_path = results_dir / "arxiv_memory_rl.csv"
    if csv_path.exists():
        try:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                expected = ["title", "authors", "year", "url", "topic_tag"]
                if reader.fieldnames == expected:
                    csv_score = 1.0
        except Exception:
            csv_score = 0.0

    scores = {
        "required_files": round(_required_files_score(results_dir), 4),
        "result_json_valid": 1.0 if isinstance(obj, dict) else 0.0,
        "json_key_coverage": round(_json_key_score(obj), 4),
        "csv_schema_exact": round(csv_score, 4),
        "summary_capability_signal": round(_summary_term_score(summary_text), 4),
        "manifest_consistency": round(_manifest_score(manifest_csv, results_dir), 4),
        "transcript_evidence_signal": round(_transcript_evidence_score(transcript), 4),
    }
    scores["overall_score"] = round(sum(scores.values()) / len(scores), 4)
    return scores
```

## Workspace Path

```text
workspace/01_Recent_Constraint_Tracking/task_01_arxiv_csv_digest
```

## Scenario Path

```text
workspace/01_Recent_Constraint_Tracking/task_01_arxiv_csv_digest/scenario.jsonl
```

## Oracle Path

```text
workspace/01_Recent_Constraint_Tracking/task_01_arxiv_csv_digest/oracle.yaml
```

## Skills

```text
constraint_slot_tracking
- extract fixed slots from multi-episode instructions
- maintain latest-value map and superseded-value list

web_research_citation_hygiene
- prefer official arXiv source pages over reposts
- track evidence url per selected row

csv_schema_guard
- enforce exact column order and deterministic quoting
- reject markdown/json fallback output

memory_routing
- route recent hard constraints to context_cache
- keep stale/noise notes out of active slot map
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
