---
id: 01_Recent_Constraint_Tracking_task_03_image_filter_rename_zip
name: Image subset curation with deterministic rename and zip audit
category: 01_Recent_Constraint_Tracking
capability: Recent Constraint Tracking
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with python, bash, and filesystem tools.

Primary capability focus: **Recent Constraint Tracking**

Task objective:
Filter a noisy image dataset according to the latest category constraints, rename files using a strict slot format, then package and audit the subset.

Required output files in `/tmp_workspace/results/`:
- `image_manifest.csv`
- `fashion_subset.zip`
- `result.json`
- `summary.md`
- `manifest.csv`

Strict slot constraints (latest version wins):
1. Keep only categories: `shoes` and `bags`.
2. Rename pattern: `category_index_brand.jpg`.
3. `index` must be 3-digit zero-padded per category.
4. Zip name fixed: `fashion_subset.zip`.
5. `image_manifest.csv` columns: `old_name,new_name,category,brand,width,height`.

Execution rules:
1. Replay `/tmp_workspace/scenario.jsonl`; ignore superseded constraints.
2. Use tool-generated evidence (file listings, image metadata) for decisions.
3. Keep deterministic ordering and naming.

## Expected Behavior

1. Resolve latest category and naming constraints.
2. Inspect metadata to support manifest fields.
3. Apply deterministic rename and build zip package.
4. Validate zip contents and manifest consistency.

## Grading Criteria

- [ ] Required files exist and are parseable.
- [ ] Latest filter slots are applied.
- [ ] Rename format and zero-padding are correct.
- [ ] Manifest matches actual renamed files.
- [ ] Zip content equals filtered subset.
- [ ] Capability signal is explicit: constraint retention under noise.

## Automated Checks

```python
import csv
import json
from pathlib import Path

REQUIRED_FILES = ['image_manifest.csv', 'fashion_subset.zip', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'filter_policy', 'rename_rule', 'artifacts']
REQUIRED_TERMS = ['image', 'filter', 'rename', 'zip', 'manifest', 'latest', 'constraint']


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
workspace/01_Recent_Constraint_Tracking/task_03_image_filter_rename_zip
```

## Scenario Path

```text
workspace/01_Recent_Constraint_Tracking/task_03_image_filter_rename_zip/scenario.jsonl
```

## Oracle Path

```text
workspace/01_Recent_Constraint_Tracking/task_03_image_filter_rename_zip/oracle.yaml
```

## Skills

```text
category_slot_tracking
- keep newest category constraints over stale instructions

image_manifest_integrity
- extract image metadata and bind to renamed filename
- ensure manifest rows match zip payload

deterministic_renaming
- apply stable sorted ordering
- enforce exact naming template and zero padding

memory_routing
- route recent rename slots to context_cache
- prevent stale category bleed-through
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
