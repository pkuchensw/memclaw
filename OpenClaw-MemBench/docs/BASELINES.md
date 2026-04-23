# Baseline Methods for OpenClaw-MemBench

This document describes the baseline memory management and context compression methods available in OpenClaw-MemBench.

## Available Baselines

### 1. Sliding Window (`sliding-window`)

**Description**: Simple truncation that keeps the most recent context up to the budget.

**Strategy**:
- Concatenate all context (workspace files + scenario turns)
- Truncate from the beginning, keeping only the end (most recent)

**Pros**:
- Extremely fast, no computation overhead
- Natural recency preservation
- Simple to understand and implement

**Cons**:
- Loses important historical constraints
- No semantic understanding
- Poor performance on constraint-tracking tasks

**Use Case**: Baseline for comparison, simple tasks with only recent relevance.

---

### 2. Keyword Extraction (`keyword`)

**Description**: Extracts lines containing important keywords indicating constraints, requirements, or key information.

**Strategy**:
- Define set of important keywords (constraint, must, version, output, etc.)
- Keep lines containing any keyword
- Include surrounding context lines
- Prioritize by keyword density

**Pros**:
- Fast, rule-based
- Preserves constraint-related content
- Good signal-to-noise ratio

**Cons**:
- Requires curated keyword list
- No semantic understanding
- May miss implicit constraints

**Use Case**: Constraint-heavy tasks where explicit signals are important.

---

### 3. Recursive Summarization (`recursive-summary`)

**Description**: Hierarchical summarization that creates episode-level summaries.

**Strategy**:
- Group turns by episode
- Summarize older episodes (extractive)
- Keep latest episode in full
- Combine summaries hierarchically

**Pros**:
- Preserves hierarchical structure
- Captures episode-level semantics
- Natural fit for multi-episode scenarios

**Cons**:
- May lose fine-grained details
- Requires episode annotations
- Summarization quality varies

**Use Case**: Multi-episode scenarios with clear episode boundaries.

---

### 4. Hierarchical Memory (`hierarchical`)

**Description**: Maintains multiple memory tiers (working, short-term, long-term) with different compression levels.

**Strategy**:
- Working memory: Latest episode (full fidelity, ~40% budget)
- Short-term memory: Previous 2-3 episodes (moderate compression, ~35% budget)
- Long-term memory: Older episodes (heavy compression to key facts, ~25% budget)

**Pros**:
- Preserves recent information at high fidelity
- Older information is not lost, just compressed
- Mimics human memory organization

**Cons**:
- Fixed allocation may not match task needs
- May lose procedural details in long-term tier
- Requires tuning of tier boundaries

**Use Case**: Long scenarios with mix of recent and historical information.

---

### 5. Mem0 (`mem0`)

**Description**: Simulates Mem0-style memory with fact extraction and categorization.

**Strategy**:
- Extract structured facts from content:
  - Preferences: User preferences and requirements
  - Constraints: Rules and limitations
  - Procedures: Steps and processes
  - Errors: Mistakes and resolutions
  - Facts: General factual information
- Deduplicate facts within categories
- Include most relevant facts within budget

**Pros**:
- Structured fact storage
- Automatic deduplication
- Good for state tracking

**Cons**:
- May lose procedural flow
- Fact extraction can miss implicit information
- No episode structure preservation

**Use Case**: State-tracking tasks with clear factual information.

---

### 6. Vector Retrieval (`vector-retrieval`)

**Description**: Semantic retrieval using TF-IDF similarity (simulating vector search).

**Strategy**:
- Chunk content into segments
- Compute TF-IDF vectors
- Calculate similarity to task query
- Retrieve top-k most relevant chunks

**Pros**:
- Query-adaptive retrieval
- Semantic similarity matching
- Good for finding relevant context

**Cons**:
- No episode structure preservation
- Requires good query representation
- May miss implicit relationships

**Use Case**: Tasks where semantic relevance is more important than recency.

---

## Usage

### Command Line

```bash
# List available baselines
python eval/run_baselines.py --list-baselines

# Run comparison of selected baselines
python eval/run_baselines.py \
    --baselines sliding-window,keyword,recursive-summary,hierarchical \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 5 \
    --budget 12000

# Include Mem0 and Vector Retrieval (if dependencies available)
python eval/run_baselines.py \
    --baselines sliding-window,keyword,mem0,vector-retrieval \
    --category 02_Version_Update
```

### In Code

```python
from baselines import get_baseline

# Initialize baseline
baseline = get_baseline("hierarchical", budget_chars=12000)

# Run compression
result = baseline.compress(
    workspace_files=[("path/to/file.md", "content...")],
    scenario_turns=[{"role": "user", "content": "...", "episode_id": "E1"}],
    task_prompt="Your task is to...",
)

print(f"Reduction: {result.reduction_ratio:.2%}")
print(f"Compressed context: {result.context[:500]}...")
```

### With Compression Profiles

The baselines are integrated into the compression profile system:

```python
from utils.compression_profiles import build_context

# Uses new baseline system automatically
result = build_context(
    workspace_path="workspace/01_Recent_Constraint_Tracking/task_01",
    method="hierarchical",  # or "mem0", "vector-retrieval", etc.
    budget_chars=12000,
)
```

---

## Comparison Metrics

When running baseline comparison, the following metrics are collected:

### Compression Metrics
- **Reduction Ratio**: Proportion of context removed (0.0 to 1.0)
- **Raw Characters**: Original context size
- **Compressed Characters**: Final context size
- **Compression Time**: Time to compress

### Retrieval Metrics (method-specific)
- **Facts Extracted**: Number of facts found (Mem0)
- **Facts Included**: Number of facts in final context (Mem0)
- **Chunks Selected**: Number of chunks retrieved (Vector Retrieval)
- **Retrieval Score**: Average similarity score (Vector Retrieval)

### Task Performance
- **Success Rate**: Percentage of successful compressions
- **Task Accuracy**: Would require running full task with compressed context

---

## Visualization

Generate comparison visualizations:

```bash
python eval/visualize_baselines.py \
    --input outputs/baseline_comparison/comparison_summary.json \
    --output-dir outputs/baseline_comparison/charts \
    --format png
```

This produces:
- `reduction_comparison.png`: Average compression by baseline
- `size_comparison.png`: Raw vs compressed sizes
- `success_rate.png`: Success rates
- `retention_curve.png`: Performance vs compression trade-off
- `report.md`: Markdown summary report

---

## Adding New Baselines

To add a new baseline:

1. Create a new file in `baselines/`:

```python
# baselines/my_baseline.py
from baselines.base import BaseBaseline, BaselineResult

class MyBaseline(BaseBaseline):
    def compress(self, workspace_files, scenario_turns, task_prompt=""):
        # Your compression logic
        context = "..."
        return BaselineResult(
            context=context,
            raw_chars=10000,
            compressed_chars=5000,
            reduction_ratio=0.5,
            method="my-baseline",
        )
```

2. Register in `baselines/__init__.py`:

```python
from baselines.my_baseline import MyBaseline

BASELINE_REGISTRY["my-baseline"] = MyBaseline
```

3. Use via command line or API.

---

## Research Questions

These baselines enable investigation of:

1. **Which compression strategy works best for which capability?**
   - Sliding window for recency
   - Keyword extraction for constraints
   - Hierarchical for mixed scenarios

2. **How does compression affect different memory capabilities?**
   - Recent Constraint Tracking: Needs recency preservation
   - Version Update: Needs state tracking
   - Procedure Transfer: Needs step sequence preservation

3. **What's the optimal budget allocation across memory tiers?**
   - Hierarchical baseline allows testing different ratios

4. **Can we combine multiple strategies?**
   - Hybrid approaches (e.g., hierarchical + keyword boost)
