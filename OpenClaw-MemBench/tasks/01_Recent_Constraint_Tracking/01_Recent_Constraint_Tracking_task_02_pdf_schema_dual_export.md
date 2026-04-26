---
id: 01_Recent_Constraint_Tracking_task_02_pdf_schema_dual_export
name: PDF selective extraction with dual-format schema lock
category: 01_Recent_Constraint_Tracking
capability: Recent Constraint Tracking
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with filesystem, python, and shell tools.

Primary capability focus: **Recent Constraint Tracking**

Task objective:
From provided paper records, extract structured digest records for only the whitelisted files and export both JSON and CSV under strict schema and naming constraints.

Required output files in `/tmp_workspace/results/`:
- `paper_digest.json`
- `paper_digest.csv`
- `result.json`
- `summary.md`
- `manifest.csv`

Strict slot constraints (latest version wins):
1. Only process the allowlist papers from scenario/evidence.
2. Schema fields must be exactly: `paper_id,problem,method,dataset,result`.
3. Must produce both JSON and CSV.
4. Output names must stay `paper_digest.json` and `paper_digest.csv`.
5. Do not include non-whitelisted records.

Execution rules:
1. Replay `/tmp_workspace/scenario.jsonl`; ignore stale constraints.
2. Use tool outputs (file scan, extraction logs) as evidence.
3. Add constraint arbitration in `result.json`.
4. Keep outputs deterministic.

## Expected Behavior

1. Resolve latest PDF allowlist and field schema from noisy context.
2. Use python/filesystem to extract fields from selected PDFs.
3. Generate schema-aligned JSON+CSV and explain exclusions.
4. Validate row-count parity between JSON and CSV.

## Grading Criteria

- [ ] Required files exist and are parseable.
- [ ] Latest allowlist and schema are honored.
- [ ] JSON and CSV are consistent and deterministic.
- [ ] Non-whitelisted files are excluded.
- [ ] Manifest paths map to real files in results directory.
- [ ] Capability signal is explicit: recent constraint retention.

## Automated Checks

```python
import csv
import json
from pathlib import Path

REQUIRED_FILES = ['paper_digest.json', 'paper_digest.csv', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'selected_pdfs', 'schema_fields', 'artifacts']
REQUIRED_TERMS = ['pdf', 'allowlist', 'schema', 'json', 'csv', 'latest', 'constraint']


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

    parity = 0.0
    jpath = results_dir / "paper_digest.json"
    cpath = results_dir / "paper_digest.csv"
    if jpath.exists() and cpath.exists():
        try:
            j = _load_json(jpath)
            jn = len(j) if isinstance(j, list) else 0
            with cpath.open("r", encoding="utf-8") as f:
                cn = len(list(csv.DictReader(f)))
            parity = 1.0 if jn == cn and jn > 0 else 0.0
        except Exception:
            parity = 0.0

    scores = {
        "required_files": round(_required_files_score(results_dir), 4),
        "result_json_valid": 1.0 if isinstance(obj, dict) else 0.0,
        "json_key_coverage": round(_json_key_score(obj), 4),
        "dual_format_parity": round(parity, 4),
        "summary_capability_signal": round(_summary_term_score(summary_text), 4),
        "manifest_consistency": round(_manifest_score(manifest_csv, results_dir), 4),
        "transcript_evidence_signal": round(_transcript_evidence_score(transcript), 4),
    }
    scores["overall_score"] = round(sum(scores.values()) / len(scores), 4)
    return scores
```

## Workspace Path

```text
workspace/01_Recent_Constraint_Tracking/task_02_pdf_schema_dual_export
```

## Scenario Path

```text
workspace/01_Recent_Constraint_Tracking/task_02_pdf_schema_dual_export/scenario.jsonl
```

## Oracle Path

```text
workspace/01_Recent_Constraint_Tracking/task_02_pdf_schema_dual_export/oracle.yaml
```

## Skills

```text
pdf_selection_tracking
- map latest allowlist constraints to concrete filenames
- reject stale file-selection instructions

schema_dual_export
- enforce shared field schema for JSON and CSV outputs
- verify row-level parity between formats

artifact_determinism
- keep stable file names and stable field order
- avoid adding opportunistic extra fields

memory_routing
- route file-selection constraints to context_cache
- route schema constraints to state_memory
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
