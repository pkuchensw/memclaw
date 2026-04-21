---
id: 01_Recent_Constraint_Tracking_task_04_video_clip_index_build
name: Multi-clip extraction with strict timeline and encoding slots
category: 01_Recent_Constraint_Tracking
capability: Recent Constraint Tracking
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with ffmpeg, bash, python, and filesystem tools.

Primary capability focus: **Recent Constraint Tracking**

Task objective:
Extract required clips from a long source video while preserving newest constraints for time windows, output naming, and encoding profile.

Required output files in `/tmp_workspace/results/`:
- `clip_01.mp4`
- `clip_02.mp4`
- `clip_03.mp4`
- `clips_index.json`
- `result.json`
- `summary.md`
- `manifest.csv`

Strict slot constraints (latest version wins):
1. Clip windows come from latest turn in `scenario.jsonl`.
2. Output names fixed to `clip_01.mp4`, `clip_02.mp4`, `clip_03.mp4`.
3. Resolution must be `1280x720`.
4. Video codec must be `h264`.
5. `clips_index.json` fields: `clip_name,start,end,duration,source_video,encoding`.

Execution rules:
1. Replay scenario and filter superseded timeline constraints.
2. Use ffmpeg/ffprobe evidence and record decisions.
3. Keep deterministic command sequence and outputs.

## Expected Behavior

1. Resolve latest time-window slots and ignore outdated ranges.
2. Run ffmpeg clip extraction under strict naming/encoding constraints.
3. Generate index JSON from actual clip metadata.
4. Validate resolution/codec for each produced clip.

## Grading Criteria

- [ ] Required files exist and are parseable.
- [ ] Latest clip windows are applied.
- [ ] Naming and encoding slots are exact.
- [ ] Index matches produced clips.
- [ ] Manifest paths map to real files.
- [ ] Capability signal is explicit: recent constraint retention.

## Automated Checks

```python
import csv
import json
from pathlib import Path

REQUIRED_FILES = ['clips_index.json', 'clip_01.mp4', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'clip_windows', 'encoding_policy', 'artifacts']
REQUIRED_TERMS = ['ffmpeg', 'clip', '720', 'h264', 'index', 'latest', 'constraint']


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
workspace/01_Recent_Constraint_Tracking/task_04_video_clip_index_build
```

## Scenario Path

```text
workspace/01_Recent_Constraint_Tracking/task_04_video_clip_index_build/scenario.jsonl
```

## Oracle Path

```text
workspace/01_Recent_Constraint_Tracking/task_04_video_clip_index_build/oracle.yaml
```

## Skills

```text
timeline_slot_tracking
- bind latest clip windows to execution plan
- reject stale timeline packets

ffmpeg_validation
- verify codec/resolution with ffprobe
- cross-check durations against requested windows

artifact_indexing
- build index from produced files, not from planned values only

memory_routing
- keep near-term output slots in context_cache
- prevent stale encoding policy reuse
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
