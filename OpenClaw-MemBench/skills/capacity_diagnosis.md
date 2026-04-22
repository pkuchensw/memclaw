# Capacity Diagnosis Skill

## Purpose
Diagnose which capability is exposed by the current episode to determine memory compilation strategy.

## Diagnosis Framework

### Input Signals
- Episode trajectory (action-observation pairs)
- Environment feedback (success/failure/ambiguous)
- Historical similarity (comparison with past episodes)
- Constraint changes (delta between turns)

### Output: Capability Label
```yaml
capability_type: <category>
confidence: 0.0-1.0
trigger_condition: <description>
recommended_memory_form: <context_cache|state_memory|procedural_memory|anti_memory|evidence_graph>
```

### Five Capability Categories

| Category | Trigger Condition | Failure Pattern | Memory Form |
|----------|------------------|-----------------|-------------|
| **Context Retention** | Recent constraints given but not honored | Uses stale format/path/parameter | context_cache |
| **State Revision** | New information contradicts prior state | Uses old version instead of latest | state_memory |
| **Procedural Reuse** | Similar task structure, different surface | Rediscovers steps instead of reusing | procedural_memory |
| **Error Avoidance** | Repeats past mistake in similar context | Same error pattern, same fix needed | anti_memory |
| **Evidence Arbitration** | Multiple sources with conflicting info | Chooses wrong source or random pick | evidence_graph |

### Example Diagnosis

```
Episode: Environment setup with CUDA
Trajectory: 
  - Action: pip install torch==2.1
  - Observation: CUDA mismatch error
  - Action: check nvidia-smi, reinstall with correct version
  - Observation: success

Diagnosis:
  capability_type: error_avoidance
  confidence: 0.92
  trigger_condition: "environment_setup && has_cuda && install_before_check"
  recommended_memory_form: anti_memory
```

## Compilation Decision

After diagnosis, compile episode into recommended memory form:

- **context_cache**: Keep recent_raw_span + key_slots + unfinished_subgoals
- **state_memory**: Write versioned state object (key, old, new, source, supersedes)
- **procedural_memory**: Extract trigger + steps + checkpoints
- **anti_memory**: Write error_pattern + veto_rule + checklist
- **evidence_graph**: Record sources, timeline, confidence, resolution

## Why Not Generic Summary?

Generic summary loses:
- **Recency** → Context tasks fail
- **Version chain** → State tasks use stale info
- **Step order** → Procedural tasks reinvent
- **Error pattern** → Same mistakes repeat
- **Source provenance** → Arbitrary decisions
