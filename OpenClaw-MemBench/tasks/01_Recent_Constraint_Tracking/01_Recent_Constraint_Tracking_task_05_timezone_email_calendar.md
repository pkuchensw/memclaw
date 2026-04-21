---
id: 01_Recent_Constraint_Tracking_task_05_timezone_email_calendar
name: Timezone-safe meeting coordination with email and ICS draft
category: 01_Recent_Constraint_Tracking
capability: Recent Constraint Tracking
timeout_seconds: 900
---

## Prompt

You are running inside a live OpenClaw workspace with calendar/email-style fixtures, python, and filesystem tools.

Primary capability focus: **Recent Constraint Tracking**

Task objective:
Pick a valid meeting slot from noisy updates, normalize all times to Pacific Time, and output both a plain-text coordination note and ICS draft.

Required output files in `/tmp_workspace/results/`:
- `meeting_summary.txt`
- `meeting_draft.ics`
- `result.json`
- `summary.md`
- `manifest.csv`

Strict slot constraints (latest version wins):
1. Candidate windows and attendees come from latest episode updates.
2. All final times must be expressed in PT.
3. Required CC recipient must be present in summary text.
4. ICS fields must include `DTSTART`, `DTEND`, `SUMMARY`, `ATTENDEE`, `ORGANIZER`.
5. Final selected slot must be one of the valid windows.

Execution rules:
1. Replay scenario and ignore superseded time windows.
2. Use concrete evidence from calendar/email fixture files.
3. Keep outputs deterministic and machine-parseable.

## Expected Behavior

1. Resolve latest slot windows and recipient constraints from noisy thread history.
2. Normalize chosen slot into PT and generate coordination summary.
3. Build valid ICS draft aligned with selected slot.
4. Validate recipient and timezone fields before finish.

## Grading Criteria

- [ ] Required files exist and are parseable.
- [ ] Latest time-window and attendee slots are used.
- [ ] PT normalization is consistent.
- [ ] ICS contains mandatory fields and valid slot.
- [ ] Manifest maps to real files.
- [ ] Capability signal is explicit: recent constraint retention.

## Automated Checks

```python
import csv
import json
from pathlib import Path

REQUIRED_FILES = ['meeting_summary.txt', 'meeting_draft.ics', 'result.json', 'summary.md', 'manifest.csv']
REQUIRED_JSON_KEYS = ['task_id', 'capability', 'timezone_policy', 'chosen_slot', 'artifacts']
REQUIRED_TERMS = ['timezone', 'pacific', 'ics', 'cc', 'latest', 'slot', 'constraint']


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
workspace/01_Recent_Constraint_Tracking/task_05_timezone_email_calendar
```

## Scenario Path

```text
workspace/01_Recent_Constraint_Tracking/task_05_timezone_email_calendar/scenario.jsonl
```

## Oracle Path

```text
workspace/01_Recent_Constraint_Tracking/task_05_timezone_email_calendar/oracle.yaml
```

## Skills

```text
timezone_slot_tracking
- keep latest meeting window constraints in active map
- reject superseded calendar/email windows

calendar_email_reconciliation
- reconcile thread updates with calendar availability files
- preserve required recipients and organizer fields

ics_schema_guard
- emit deterministic ICS fields and ordering
- verify DTSTART/DTEND consistency with chosen slot

memory_routing
- route near-term schedule constraints to context_cache
- keep long-term user preference updates in state_memory
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
