#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p tasks/{01_Recent_Constraint_Tracking,02_Version_Update,03_Procedure_Transfer,04_Repeated_Mistake_Prevention,05_Source_Conflict_Resolution,06_Memory_Operation_Selection,07_Goal_Interruption_Resumption,08_Staleness_Applicability_Judgment}
mkdir -p workspace/{01_Recent_Constraint_Tracking,02_Version_Update,03_Procedure_Transfer,04_Repeated_Mistake_Prevention,05_Source_Conflict_Resolution,06_Memory_Operation_Selection,07_Goal_Interruption_Resumption,08_Staleness_Applicability_Judgment}

cat > /tmp/membench_tasks.tsv << 'TASKS'
01_Recent_Constraint_Tracking|01|arxiv_csv_digest|ArXiv digest to strict CSV|Recent Constraint Tracking
01_Recent_Constraint_Tracking|02|pdf_schema_dual_export|PDF schema extraction to JSON and CSV|Recent Constraint Tracking
01_Recent_Constraint_Tracking|03|image_filter_rename_zip|Filter, rename, and zip product images|Recent Constraint Tracking
01_Recent_Constraint_Tracking|04|video_clip_index_build|Build indexed clips from long video|Recent Constraint Tracking
01_Recent_Constraint_Tracking|05|timezone_email_calendar|Coordinate email and calendar in one timezone|Recent Constraint Tracking
02_Version_Update|06|python_runtime_switch|Switch from Python 3.10 to 3.11 with uv|Version Update
02_Version_Update|07|dependency_revision_chain|Apply dependency revision chain safely|Version Update
02_Version_Update|08|api_contract_migration|Migrate API contract to new schema version|Version Update
02_Version_Update|09|policy_update_enforcement|Enforce late policy update in outputs|Version Update
02_Version_Update|10|dataset_label_revision|Regenerate reports after label revision|Version Update
03_Procedure_Transfer|11|arxiv_to_acl_pipeline_transfer|Transfer literature pipeline from ArXiv to ACL|Procedure Transfer
03_Procedure_Transfer|12|log_triage_pattern_reuse|Reuse successful log triage procedure|Procedure Transfer
03_Procedure_Transfer|13|table_cleaning_template_transfer|Transfer table cleaning template to new data|Procedure Transfer
03_Procedure_Transfer|14|code_patch_workflow_transfer|Transfer patch workflow to parallel repo|Procedure Transfer
03_Procedure_Transfer|15|report_generation_pattern_transfer|Transfer report generation pattern cross domain|Procedure Transfer
04_Repeated_Mistake_Prevention|16|cuda_compatibility_guard|Prevent repeated CUDA mismatch installation|Repeated Mistake Prevention
04_Repeated_Mistake_Prevention|17|path_overwrite_prevention|Avoid destructive overwrite after prior failure|Repeated Mistake Prevention
04_Repeated_Mistake_Prevention|18|csv_delimiter_guard|Avoid repeated CSV delimiter error|Repeated Mistake Prevention
04_Repeated_Mistake_Prevention|19|timezone_shift_guard|Avoid repeated timezone conversion bug|Repeated Mistake Prevention
04_Repeated_Mistake_Prevention|20|unsafe_command_guard|Avoid repeating unsafe shell command pattern|Repeated Mistake Prevention
05_Source_Conflict_Resolution|21|config_vs_user_claim|Resolve config file versus user claim conflict|Source Conflict Resolution
05_Source_Conflict_Resolution|22|doc_vs_runtime_logs|Resolve docs versus runtime logs mismatch|Source Conflict Resolution
05_Source_Conflict_Resolution|23|email_vs_calendar_conflict|Resolve email and calendar schedule conflict|Source Conflict Resolution
05_Source_Conflict_Resolution|24|csv_vs_database_snapshot|Resolve CSV and snapshot disagreement|Source Conflict Resolution
05_Source_Conflict_Resolution|25|spec_vs_tests_conflict|Resolve specification and test conflict|Source Conflict Resolution
06_Memory_Operation_Selection|26|memory_form_selection_research|Select memory form in research workflow|Memory Operation Selection
06_Memory_Operation_Selection|27|memory_form_selection_debug|Select memory form in debugging workflow|Memory Operation Selection
06_Memory_Operation_Selection|28|memory_form_selection_planning|Select memory form in planning workflow|Memory Operation Selection
06_Memory_Operation_Selection|29|memory_form_selection_ops|Select memory form in operations workflow|Memory Operation Selection
06_Memory_Operation_Selection|30|memory_form_selection_review|Select memory form in review workflow|Memory Operation Selection
07_Goal_Interruption_Resumption|31|interrupted_data_pipeline_resume|Resume interrupted data pipeline|Goal Interruption and Task Resumption
07_Goal_Interruption_Resumption|32|interrupted_code_fix_resume|Resume interrupted code fix|Goal Interruption and Task Resumption
07_Goal_Interruption_Resumption|33|interrupted_meeting_task_resume|Resume interrupted meeting coordination|Goal Interruption and Task Resumption
07_Goal_Interruption_Resumption|34|interrupted_media_task_resume|Resume interrupted media processing|Goal Interruption and Task Resumption
07_Goal_Interruption_Resumption|35|interrupted_search_task_resume|Resume interrupted search synthesis|Goal Interruption and Task Resumption
08_Staleness_Applicability_Judgment|36|stale_procedure_detection|Detect stale procedure and adapt|Staleness and Applicability Judgment
08_Staleness_Applicability_Judgment|37|stale_state_invalidation|Invalidate stale state before execution|Staleness and Applicability Judgment
08_Staleness_Applicability_Judgment|38|context_scope_applicability|Judge context scope applicability|Staleness and Applicability Judgment
08_Staleness_Applicability_Judgment|39|legacy_rule_deprecation|Deprecate legacy rule in final output|Staleness and Applicability Judgment
08_Staleness_Applicability_Judgment|40|cross_project_memory_filter|Filter cross-project memory contamination|Staleness and Applicability Judgment
TASKS

while IFS='|' read -r category num short_name title capability; do
  task_file="tasks/${category}/${category}_task_${num}_${short_name}.md"
  ws_dir="workspace/${category}/task_${num}_${short_name}"

  mkdir -p "$ws_dir/results" "$ws_dir/episodes" "$ws_dir/evidence"

  cat > "$ws_dir/README.md" << WEOF
# Workspace for Task ${num}: ${title}

This directory stores task-specific fixtures and expected output slots.

- episodes/: episode notes and interruption/context files
- evidence/: conflicting sources, logs, and references
- results/: expected output location for final artifacts
WEOF

  cat > "$ws_dir/episodes/context_notes.md" << WEOF
# Episode Context Notes

- Prior constraints will be placed here.
- Updated constraints should supersede older ones.
- Add interruption notes for resumption tasks.
WEOF

  cat > "$ws_dir/evidence/sources.md" << WEOF
# Evidence Sources

- Add source A, B, C here for conflict-resolution tasks.
- Include timestamps and reliability notes when possible.
WEOF

  cat > "$task_file" << TEOF
---
id: ${category}_task_${num}_${short_name}
name: ${title}
category: ${category}
capability: ${capability}
timeout_seconds: 900
---

## Prompt

You are running in OpenClaw with full tool access.

Your task is to complete a multi-episode workflow and produce final artifacts in /tmp_workspace/results/.

### Episode setup

1. Read prior constraints from /tmp_workspace/episodes/ and /tmp_workspace/evidence/.
2. Continue from the latest state instead of restarting blindly.
3. If source conflicts exist, resolve them with explicit evidence priority.

### Deliverables

- One primary artifact: result.json
- One human-readable report: summary.md
- One machine-checkable manifest: manifest.csv

### Hard constraints

- Preserve the latest constraints, not superseded ones.
- Avoid repeating known mistakes from prior episodes.
- Keep file names and schema exact.

## Expected Behavior

1. Parse prior episode context and active constraints.
2. Execute tool actions and produce deterministic outputs.
3. Validate artifacts and include evidence-based justification.
4. Save all outputs under /tmp_workspace/results/.

## Grading Criteria

- [ ] result.json exists and is parseable.
- [ ] summary.md explains decisions and evidence.
- [ ] manifest.csv matches produced files.
- [ ] Latest constraints are applied.
- [ ] No repeated known failure mode.

## Automated Checks

import csv
import json
from pathlib import Path

def _has_non_empty_text(path: Path) -> float:
    if not path.exists():
        return 0.0
    return 1.0 if path.read_text(encoding="utf-8").strip() else 0.0

def _json_valid(path: Path) -> float:
    if not path.exists():
        return 0.0
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return 1.0
    except Exception:
        return 0.0

def _csv_valid(path: Path) -> float:
    if not path.exists():
        return 0.0
    try:
        with path.open("r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        return 1.0 if len(rows) >= 1 else 0.0
    except Exception:
        return 0.0

def grade(transcript=None, workspace_path="/tmp_workspace"):
    result_json = Path(workspace_path) / "results" / "result.json"
    summary_md = Path(workspace_path) / "results" / "summary.md"
    manifest_csv = Path(workspace_path) / "results" / "manifest.csv"

    scores = {
        "result_json_valid": _json_valid(result_json),
        "summary_present": _has_non_empty_text(summary_md),
        "manifest_valid": _csv_valid(manifest_csv),
        "constraint_retention": 0.0,
        "mistake_avoidance": 0.0,
        "evidence_consistency": 0.0,
    }
    scores["overall_score"] = round(sum(scores.values()) / len(scores), 4)
    return scores

## Workspace Path

workspace/${category}/task_${num}_${short_name}

## Skills


## Env


## Warmup


TEOF

done < /tmp/membench_tasks.tsv

cat > tasks/TASK_INDEX.md << 'IEOF'
# OpenClaw-MemBench Task Index

Total tasks: 40

## Capability C1: Recent Constraint Tracking
- 01 arxiv_csv_digest
- 02 pdf_schema_dual_export
- 03 image_filter_rename_zip
- 04 video_clip_index_build
- 05 timezone_email_calendar

## Capability C2: Version Update
- 06 python_runtime_switch
- 07 dependency_revision_chain
- 08 api_contract_migration
- 09 policy_update_enforcement
- 10 dataset_label_revision

## Capability C3: Procedure Transfer
- 11 arxiv_to_acl_pipeline_transfer
- 12 log_triage_pattern_reuse
- 13 table_cleaning_template_transfer
- 14 code_patch_workflow_transfer
- 15 report_generation_pattern_transfer

## Capability C4: Repeated Mistake Prevention
- 16 cuda_compatibility_guard
- 17 path_overwrite_prevention
- 18 csv_delimiter_guard
- 19 timezone_shift_guard
- 20 unsafe_command_guard

## Capability C5: Source Conflict Resolution
- 21 config_vs_user_claim
- 22 doc_vs_runtime_logs
- 23 email_vs_calendar_conflict
- 24 csv_vs_database_snapshot
- 25 spec_vs_tests_conflict

## Capability C6: Memory Operation Selection
- 26 memory_form_selection_research
- 27 memory_form_selection_debug
- 28 memory_form_selection_planning
- 29 memory_form_selection_ops
- 30 memory_form_selection_review

## Capability C7: Goal Interruption and Task Resumption
- 31 interrupted_data_pipeline_resume
- 32 interrupted_code_fix_resume
- 33 interrupted_meeting_task_resume
- 34 interrupted_media_task_resume
- 35 interrupted_search_task_resume

## Capability C8: Staleness and Applicability Judgment
- 36 stale_procedure_detection
- 37 stale_state_invalidation
- 38 context_scope_applicability
- 39 legacy_rule_deprecation
- 40 cross_project_memory_filter
IEOF

echo "Generated 40 tasks and workspace stubs."
