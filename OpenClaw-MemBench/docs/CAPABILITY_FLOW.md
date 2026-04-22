# Capability-Based Memory Flow

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EPISODE COMPLETION                              │
│  (Agent finishes task: success, failure, or conflict)                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CAPABILITY DIAGNOSIS                               │
│                                                                         │
│  Input: Episode trajectory + feedback                                   │
│  Question: What kind of memory failure would this episode cause?        │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Forgot      │  │ Used old    │  │ Reinvented  │  │ Repeated    │   │
│  │ recent      │  │ version?    │  │ steps?      │  │ mistake?    │   │
│  │ constraint? │  │             │  │             │  │             │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │           │
│         ▼                ▼                ▼                ▼           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   CONTEXT   │  │    STATE    │  │ PROCEDURAL  │  │    ANTI     │   │
│  │  RETENTION  │  │  REVISION   │  │    REUSE    │  │   MEMORY    │   │
│  │             │  │             │  │             │  │             │   │
│  │ Context     │  │ State       │  │ Procedural  │  │ Anti        │   │
│  │ Cache       │  │ Memory      │  │ Memory      │  │ Memory      │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                         ▲               │
│  ┌─────────────┐                                       │               │
│  │  Multiple   │  Conflicting sources?                  │               │
│  │   sources   │────────────────────────────────────────┘               │
│  │  disagree?  │                                                        │
│  └──────┬──────┘                                                        │
│         ▼                                                               │
│  ┌─────────────┐                                                        │
│  │   EVIDENCE  │                                                        │
│  │ ARBITRATION │                                                        │
│  │             │                                                        │
│  │ Evidence    │                                                        │
│  │ Graph       │                                                        │
│  └─────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MEMORY COMPILATION                                   │
│                                                                         │
│  Not: "Summarize this episode"                                          │
│  But: "Compile episode into appropriate memory object"                  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Context Cache:    recent_raw + key_slots + unfinished_subgoals │   │
│  │ State Memory:     key + value_chain + source + timestamp       │   │
│  │ Procedural:       trigger + steps + params + verification      │   │
│  │ Anti-Memory:      pattern + veto + checklist + prevention      │   │
│  │ Evidence Graph:   sources + resolution + reasoning             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BUDGET-AWARE STORAGE                                 │
│                                                                         │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐              │
│  │ Context │    │  State  │    │Procedural│   │  Anti   │              │
│  │  Cache  │    │ Memory  │    │ Memory  │    │ Memory  │              │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘              │
│       │              │              │              │                    │
│       └──────────────┴──────────────┴──────────────┘                    │
│                          │                                              │
│                          ▼                                              │
│                   ┌─────────────┐                                       │
│                   │   Raw Log   │  (Immutable, for traceability)        │
│                   └─────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    TASK EXECUTION                                       │
│                                                                         │
│  New task arrives...                                                    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Step 1: Classify task capability need                           │   │
│  │         "This needs recent constraints" → Query Context Cache    │   │
│  │         "This needs current state" → Query State Memory        │   │
│  │         "This is similar to past task" → Query Procedural      │   │
│  │         "This might repeat mistake" → Query Anti-Memory        │   │
│  │         "Sources might conflict" → Query Evidence Graph        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Step 2: Retrieve from appropriate memory store                  │   │
│  │         Not: "Find similar text"                                │   │
│  │         But: "Get latest state for key X"                       │   │
│  │             "Get procedure for trigger Y"                       │   │
│  │             "Check anti-pattern for context Z"                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Step 3: Inject into context                                     │   │
│  │         [Retrieved Memory Object] + [Current Task Prompt]       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    EVALUATION                                           │
│                                                                         │
│  Per-Capability Metrics:                                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │   Context   │ │    State    │ │ Procedural  │ │    Anti     │       │
│  │ Retention   │ │  Revision   │ │    Reuse    │ │   Memory    │       │
│  │   Rate      │ │   Rate      │ │    Rate     │ │  Hit Rate   │       │
│  │    0.90     │ │    0.95     │ │    0.85     │ │    0.92     │       │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                                         │
│  Budget Sensitivity:                                                    │
│  Context:  ████████████░░░░░░░░  80% @ 20K tokens                       │
│  State:    ████████████████░░░░  90% @ 20K tokens                       │
│  Procedure:█████████░░░░░░░░░░░  70% @ 20K tokens                       │
│  Anti:     ████████████████░░░░  92% @ 20K tokens                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Diagnose First, Compile Second

```
❌ Wrong:  Episode → Summary → Store
✅ Right:  Episode → Diagnose → Compile → Store
```

### 2. Form Follows Function

```
❌ Wrong:  All episodes → Same summary format
✅ Right:  Episode A → Context Cache
           Episode B → State Memory
           Episode C → Procedural Template
```

### 3. Retrieve by Capability, Not Similarity

```
❌ Wrong:  "Find text similar to current query"
✅ Right:  "Get latest state" / "Get procedure for trigger"
```

### 4. Budget Allocation by Capability Priority

```
If budget < 10K:
    Preserve: State Memory (version chain)
    Compress: Procedural Memory (keep skeleton)
    Drop:     Context Cache details (keep slots only)
```

## Comparison: Before vs After

### Before (Task-Based)

```
Agent: "What was I supposed to do?"
System: [Returns generic summary of past 10 turns]
Agent: [Might miss specific constraint]
```

### After (Capability-Based)

```
Agent: "What was I supposed to do?"
System:
  - From Context Cache: "Active constraints: year=2024-2025, format=CSV"
  - From State Memory: "Current Python version: 3.11"
  - From Anti-Memory: "Warning: Check CUDA before installing torch"
Agent: [Has all necessary information in right form]
```

## Example Walkthrough

### Episode 1: Environment Setup Failure

**Trajectory:**
1. User: "Install PyTorch for this project"
2. Agent: `pip install torch==2.1`
3. Environment: CUDA mismatch error
4. User: "Check CUDA version first!"
5. Agent: `nvidia-smi`, `nvcc --version`
6. Agent: `pip install torch==2.3+cu118`
7. Environment: Success

**Diagnosis:** Error Avoidance pattern

**Compilation:**
```yaml
anti_memory:
  pattern: "cuda_install_without_check"
  trigger: ["environment_setup", "cuda_package"]
  veto: "pip install torch before checking CUDA"
  checklist: ["nvidia-smi", "nvcc --version"]
```

### Episode 2: Similar Setup Task

**New Task:** "Set up environment for the vision project"

**Capability Check:** 
- Trigger matches anti-memory pattern
- Budget: Low (new task, no context yet)

**Retrieval:**
```yaml
from_anti_memory:
  warning: "Similar context: cuda_install_without_check"
  veto: "Don't install CUDA packages before checking driver"
  checklist: ["nvidia-smi", "nvcc --version"]
```

**Result:**
- Agent runs checklist first
- Avoids CUDA mismatch error
- Task succeeds on first try

**This is capability-based memory working.**
