# OpenClaw-MemBench Grading System

This document describes the capability-based grading system implemented in OpenClaw-MemBench.

## Overview

The grading system evaluates agent performance across 8 memory capabilities using a combination of:

1. **Oracle-based evaluation**: Gold standards defined in `oracle.yaml`
2. **Scenario-aware grading**: Episode structure from `scenario.jsonl`
3. **Artifact validation**: Required output files and their contents
4. **Transcript analysis**: Evidence signals in conversation history

## Grading Architecture

```
utils/grading.py
├── CapabilityGrader (base class)
│   ├── RecentConstraintTrackingGrader (C1)
│   ├── VersionUpdateGrader (C2)
│   ├── ProcedureTransferGrader (C3)
│   ├── RepeatedMistakePreventionGrader (C4)
│   ├── SourceConflictResolutionGrader (C5)
│   ├── MemoryOperationSelectionGrader (C6)
│   ├── GoalInterruptionResumptionGrader (C7)
│   └── StalenessApplicabilityGrader (C8)
├── File checkers (required files, JSON keys, manifest)
└── grade_task() - main entry point
```

## Capability-Specific Scoring

### C1: Recent Constraint Tracking

**Key Metrics:**
- Required files existence (result.json, summary.md, manifest.csv)
- Gold constraint adherence (keywords from oracle)
- Anti-constraint rejection (avoid deprecated patterns)
- Transcript evidence (constraint, latest, correction, update)

**Oracle Fields:**
```yaml
gold_constraints: [year_range_2024_2025, csv_schema_exact]
gold_anti_rule: [do_not_use_2023_range]
```

### C2: Version Update

**Key Metrics:**
- Version chain completeness (version_chain.json)
- Final version correctness
- Supersedence tracking
- Transcript version signals

**Oracle Fields:**
```yaml
gold_version_chain: [{version: v1}, {version: v2}]
gold_final_state: {version: v2}
```

### C3: Procedure Transfer

**Key Metrics:**
- Procedure manifest completeness
- Step count vs gold procedure
- Step name matching
- Transcript procedure signals

**Oracle Fields:**
```yaml
gold_procedure: [parse_slots, filter, export, validate]
```

### C4: Repeated Mistake Prevention

**Key Metrics:**
- Guardrail rule coverage
- Anti-rule capture
- Transcript prevention signals

**Oracle Fields:**
```yaml
gold_anti_rule: [cuda_mismatch, path_overwrite]
```

### C5: Source Conflict Resolution

**Key Metrics:**
- Evidence ranking correctness
- Top source priority
- Transcript conflict signals

**Oracle Fields:**
```yaml
gold_evidence_priority: [latest_user_message, scenario_final_turn, stale_cache]
```

### C6: Memory Operation Selection

**Key Metrics:**
- Operation log completeness
- Operation type coverage
- Transcript memory signals

**Oracle Fields:**
```yaml
gold_memory_operation: [context_cache, evidence_graph]
```

### C7: Goal Interruption and Task Resumption

**Key Metrics:**
- Resume state structure (checkpoint, processed, pending)
- Pipeline progress tracking
- Transcript resumption signals

### C8: Staleness and Applicability Judgment

**Key Metrics:**
- Staleness decision classification (active/stale/conditional)
- Applicability reasoning
- Transcript staleness signals

## Usage

### Command Line

```bash
# Dry run (structural validation only)
python eval/run_batch.py --dry-run

# Run with API
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1

# Run with Docker
python eval/run_batch.py --runtime docker --category 01_Recent_Constraint_Tracking

# Run with OpenClaw Docker
python eval/run_batch.py --runtime openclaw-docker --category 01_Recent_Constraint_Tracking
```

### Programmatic

```python
from utils.grading import grade_task

scores = grade_task(
    task_capability="Recent Constraint Tracking",
    workspace_path="/path/to/workspace",
    oracle_path="/path/to/oracle.yaml",
    scenario_path="/path/to/scenario.jsonl",
    transcript=[...],
)

print(f"Overall score: {scores['overall_score']}")
print(f"Constraint adherence: {scores.get('constraint_year_range_2024_2025', 0)}")
```

## Output Format

The grading system produces a scores dictionary:

```json
{
  "file_result_json": 1.0,
  "file_summary_md": 1.0,
  "file_manifest_csv": 1.0,
  "constraint_year_range_2024_2025": 0.85,
  "anti_constraint_do_not_use_2023_range": 1.0,
  "transcript_evidence": 0.75,
  "manifest_consistency": 1.0,
  "transcript_evidence_signal": 0.8,
  "overall_score": 0.9
}
```

## Integration with run_batch.py

The grading system is automatically invoked by `run_batch.py` after task execution:

1. Task executes and produces artifacts in `workspace/results/`
2. `run_automated_checks()` calls `run_grading_from_task_md()`
3. Appropriate `CapabilityGrader` subclass is instantiated
4. Grading scores are computed and saved to result summary

## Extending the Grading System

To add a new capability:

1. Create a new `CapabilityGrader` subclass
2. Implement `grade()` method with capability-specific logic
3. Add to `CAPABILITY_GRADERS` dictionary
4. Define oracle schema for gold standards

Example:

```python
class NewCapabilityGrader(CapabilityGrader):
    def grade(self, transcript=None):
        scores = {}
        # Check required files
        scores.update(check_required_files(
            self.results_dir,
            ["new_artifact.json", "result.json"]
        ))
        # Capability-specific checks
        scores["custom_metric"] = self._check_custom()
        return scores
```

## Troubleshooting

### Missing Oracle
If `oracle.yaml` is not found, grading falls back to basic file existence checks only.

### Missing Scenario
If `scenario.jsonl` is not found, transcript evidence scoring will be limited.

### Score Calculation
Overall score is the average of all numeric component scores.
