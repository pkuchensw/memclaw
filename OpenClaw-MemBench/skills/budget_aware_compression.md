# Budget-Aware Compression Skill

## Purpose
Select compression strategy based on token budget constraints while preserving capability-critical information.

## Budget Levels

| Level | Token Range | Strategy | Trade-off |
|-------|-------------|----------|-----------|
| **L0: Full** | >50K | No compression, raw context | Maximum accuracy, highest cost |
| **L1: Conservative** | 20K-50K | Preserve all episodes, compress within episode | Minor details lost |
| **L2: Moderate** | 10K-20K | Episode-level summarization | Surface details lost, structure kept |
| **L3: Aggressive** | 5K-10K | Hierarchical summary + key slots | Only critical info kept |
| **L4: Minimal** | <5K | Pointer + current state only | High risk of losing history |

## Capability-Preserving Compression

### For Context Retention Tasks
```yaml
priority: [recent_constraints, active_slots, unfinished_subgoals]
compression_order:
  1. Remove completed subgoals
  2. Truncate earlier episode details
  3. Preserve latest 3 turns verbatim
never_compress: [current_user_instruction, active_format_constraints]
```

### For State Revision Tasks
```yaml
priority: [latest_state, version_chain, source_attribution]
compression_order:
  1. Replace historical states with diff-only
  2. Keep full latest state
  3. Summarize outdated episodes
never_compress: [current_state_value, state_source, version_timestamp]
```

### For Procedural Reuse Tasks
```yaml
priority: [trigger_conditions, step_sequence, verification_points]
compression_order:
  1. Abstract concrete values to parameters
  2. Keep step skeleton, remove details
  3. Preserve success/failure signals
never_compress: [step_order, trigger_pattern, checkpoint_locations]
```

### For Error Avoidance Tasks
```yaml
priority: [error_pattern, veto_rule, checklist]
compression_order:
  1. Compress successful path details
  2. Keep error context and fix
  3. Maintain anti-pattern specificity
never_compress: [error_signature, veto_conditions, prevention_checklist]
```

### For Evidence Arbitration Tasks
```yaml
priority: [conflicting_sources, resolution_logic, confidence_scores]
compression_order:
  1. Summarize agreeing sources
  2. Keep conflicting excerpts
  3. Preserve arbitration rationale
never_compress: [conflict_points, chosen_source, resolution_reasoning]
```

## Budget Sensitivity Metric

Track performance degradation across budget levels:

```python
{
  "budget_tokens": 10000,
  "capability": "state_revision",
  "accuracy": 0.85,
  "accuracy_at_full_context": 0.95,
  "retention_ratio": 0.89,  # 0.85/0.95
  "compression_events": [
    {"type": "episode_summarized", "episode_id": "E1"},
    {"type": "state_diff_only", "episode_id": "E2"}
  ]
}
```

## Dynamic Budget Allocation

Based on task complexity:

```
if task_type == "single_shot":
    budget = min(context_length, 8000)
elif task_type == "multi_episode":
    budget = max(12000, num_episodes * 2000)
elif task_type == "constraint_tracking":
    budget = max(10000, num_active_constraints * 1000)
```
