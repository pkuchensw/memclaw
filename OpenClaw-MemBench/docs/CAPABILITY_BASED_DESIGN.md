# Capability-Based Memory Compilation: Design Philosophy

## Core Argument

**Not all long context should be compressed the same way.**

Traditional approaches treat context compression as a **task-agnostic** problem:
- "How do we make this text shorter?"
- "How do we preserve the most important information?"

We treat it as a **capability-specific** problem:
- "What kind of memory failure is this episode exposing?"
- "What memory form best addresses this failure mode?"

## Comparison: Task-Based vs Capability-Based

### Task-Based Approach

```
Task: "Search arXiv papers and export to CSV"
↓
Compress all history into summary
↓
Retrieve summary for similar tasks
```

**Problems:**
1. Loses recent constraints → Context retention tasks fail
2. Loses version chain → State revision tasks use stale info
3. Loses step order → Procedural tasks reinvent
4. Loses error pattern → Same mistakes repeat
5. Loses source provenance → Arbitrary decisions

### Capability-Based Approach

```
Episode: "Search arXiv papers and export to CSV"
↓
Diagnose: Recent constraints not yet executed
Capability: Context Retention
↓
Compile to: Context Cache (not summary!)
  - recent_raw_span: verbatim
  - key_slots: year_range, topic_filter, output_format
  - active_constraints: format, path, schema
↓
Retrieve: Context Cache for constraint-heavy tasks
```

## The Five Memory Forms

| Capability | Failure Pattern | Memory Form | Why This Form? |
|------------|----------------|-------------|----------------|
| **Context Retention** | Forgets recent constraints | **Context Cache** | Keeps verbatim recency + active slots |
| **State Revision** | Uses stale state | **State Memory** | Version chain enables "latest wins" |
| **Procedural Reuse** | Reinvents steps | **Procedural Memory** | Template enables direct reuse |
| **Error Avoidance** | Repeats mistakes | **Anti-Memory** | Veto rules prevent recurrence |
| **Evidence Arbitration** | Chooses wrong source | **Evidence Graph** | Provenance enables justified decisions |

## Key Insight: Compression Happens at Episode Level

**Not:** "Compress tokens to fit budget"

**But:** "Compile episode into appropriate memory object"

### Example: Same Episode, Different Compilations

**Episode:** "Configure Python 3.10 environment → Error: CUDA mismatch → Fix: Check CUDA first → Success with 3.11"

**Task-Based Compression:**
```
Summary: "Configured Python environment, encountered CUDA issue, 
resolved by checking compatibility first, used Python 3.11"
```
**Loss:** Specific error pattern, prevention steps

**Capability-Based Compilation:**

Option A - State Revision focus:
```yaml
state_memory:
  python_version: 3.11 (supersedes 3.10)
  package_manager: uv (supersedes conda)
```

Option B - Error Avoidance focus:
```yaml
anti_memory:
  pattern: "cuda_install_without_check"
  veto: "Install CUDA package without checking driver"
  checklist: ["nvidia-smi", "nvcc --version"]
```

Option C - Procedural focus:
```yaml
procedural_memory:
  trigger: "environment_setup with CUDA"
  steps: ["check_driver", "check_cuda", "select_torch_version", "install"]
```

**Same episode, different compilations based on diagnosed capability.**

## Why This Matters for Evaluation

### Traditional Benchmarks

Measure: "Can the model do this task?"

**Problem:** Confuses multiple failure modes:
- Failed because forgot constraint? (Context issue)
- Failed because used old version? (State issue)
- Failed because reinvented steps? (Procedural issue)

### Our Benchmark

Measures: "Which capability is failing under which conditions?"

**Enables:**
1. **Targeted interventions**: Fix specific capability, not generic performance
2. **Compression strategy selection**: Different forms for different failures
3. **Budget allocation**: Prioritize memory forms for frequently failing capabilities

## Experimental Design Implications

### Required: Budget Sensitivity Curves

Show performance degradation as context grows:

```
Tokens →    2K    10K    20K    50K
           ━━━    ━━━    ━━━    ━━━
Context    95%    90%    80%    60%    ← Needs recency preservation
State      95%    93%    90%    85%    ← Needs version chain
Procedure  95%    85%    70%    50%    ← Needs step skeleton
Anti       95%    94%    92%    88%    ← Needs error signature
Evidence   95%    88%    75%    65%    ← Needs source provenance
```

### Required: Capability-Specific Metrics

Not just "accuracy" but:

```yaml
context_retention:
  slot_preservation_rate: 0.95
  recency_fidelity: 0.90
  constraint_violations: 2

state_revision:
  version_accuracy: 0.95
  staleness_incidents: 1
  chain_completeness: 0.98

procedural_reuse:
  step_order_accuracy: 0.85
  reinvention_rate: 0.15
  template_match_rate: 0.80

error_avoidance:
  prevention_rate: 0.92
  repeated_errors: 3
  checklist_completion: 0.95

evidence_arbitration:
  source_selection_accuracy: 0.88
  justification_quality: 0.82
  conflict_resolution_rate: 0.90
```

## Architecture Implications

### Not: Unified Memory Store

```
[Raw History] → [Compress] → [Vector DB] → [Retrieve by similarity]
```

### But: Capability-Routed Memory Compiler

```
[Episode] → [Diagnose Capability] → [Compile to Form] → [Store in Typed Memory]
                                              ↓
[Task] → [Match Capability] → [Retrieve from Typed Memory] → [Playback]
```

## Summary: What Makes Us Different

| Dimension | Traditional | Ours |
|-----------|-------------|------|
**Compression Unit** | Tokens | Episodes |
**Compression Target** | Generic summary | Capability-specific object |
**Storage** | Unified | Heterogeneous (5 forms) |
**Retrieval** | Similarity search | Capability routing |
**Evaluation** | Task accuracy | Capability retention curves |
**Innovation** | Better compression | Better *compilation* |

## Research Questions This Enables

1. Which capabilities degrade fastest under budget pressure?
2. Can we learn optimal compilation strategies from failure patterns?
3. How to dynamically allocate budget across memory forms?
4. When to consolidate vs. preserve verbatim?
5. How to transfer compiled memory across different agents?

These questions are only visible when you adopt a **capability-based** perspective.
