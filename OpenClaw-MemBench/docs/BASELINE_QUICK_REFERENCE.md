# Baseline Quick Reference

Quick commands for running baseline comparisons.

## Available Baselines

| Name | Description | Best For |
|------|-------------|----------|
| `sliding-window` | Keep most recent content | Baseline comparison |
| `keyword` | Extract constraint keywords | Constraint-heavy tasks |
| `recursive-summary` | Episode-level summarization | Multi-episode scenarios |
| `hierarchical` | Multi-tier memory system | Long scenarios |
| `mem0` | Fact extraction & categorization | State tracking |
| `vector-retrieval` | Semantic similarity retrieval | Query-adaptive tasks |

## Commands

### List Baselines

```bash
python eval/run_baselines.py --list-baselines
```

### Run Compression Comparison

```bash
# Default baselines on all categories
python eval/run_baselines.py

# Specific category
python eval/run_baselines.py --category 01_Recent_Constraint_Tracking

# Specific baselines
python eval/run_baselines.py --baselines sliding-window,keyword,hierarchical

# Limit tasks
python eval/run_baselines.py --max-tasks 5

# Adjust budget
python eval/run_baselines.py --budget 8000
```

### Run Full Comparison Pipeline

```bash
# Compression only
python eval/run_all_baselines.py \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 5

# With task execution (requires API)
python eval/run_all_baselines.py \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 5 \
    --execute-tasks

# All baselines
python eval/run_all_baselines.py --baselines all --max-tasks 10

# Specific baselines
python eval/run_all_baselines.py \
    --baselines keyword,hierarchical,mem0 \
    --max-tasks 5 \
    --execute-tasks
```

### Generate Visualizations

```bash
python eval/visualize_baselines.py \
    --input outputs/baseline_comparison/comparison_summary.json \
    --output-dir outputs/baseline_comparison/charts \
    --format png
```

### Use in Code

```python
from baselines import get_baseline, list_baselines
from utils.compression_profiles import build_context

# List available baselines
print(list_baselines())

# Use baseline directly
baseline = get_baseline("hierarchical", budget_chars=12000)
result = baseline.compress(
    workspace_files=[("file.md", "content...")],
    scenario_turns=[{"role": "user", "content": "..."}],
)

# Or through compression_profiles (auto-detects method)
result = build_context(
    workspace_path="workspace/01_Recent_Constraint_Tracking/task_01",
    method="mem0",
    budget_chars=12000,
)
```

## Output Files

After running comparison:

```
outputs/baseline_comparison/
├── comparison_summary.json      # Raw comparison data
├── COMPREHENSIVE_REPORT.md      # Full markdown report
├── report.md                    # Summary report
├── task_results_{baseline}.json # Task execution results (if --execute-tasks)
├── compressed_context.txt       # Per-task compressed context
└── charts/
    ├── reduction_comparison.png
    ├── size_comparison.png
    ├── success_rate.png
    └── retention_curve.png
```

## Environment Variables

```bash
# Budget settings
export OPENCLAW_CONTEXT_BUDGET_CHARS=12000

# Compression method
export OPENCLAW_COMPRESSION_METHOD=hierarchical  # or any baseline name

# For task execution
export OPENCLAW_API_KEY=your_key
export OPENCLAW_BASE_URL=http://localhost:18789
```

## Quick Tests

```bash
# Test single baseline
python -c "
from baselines import get_baseline
baseline = get_baseline('keyword')
result = baseline.compress(
    [('test.md', 'constraint: use CSV')],
    [{'role': 'user', 'content': 'year: 2024'}]
)
print(f'Reduction: {result.reduction_ratio:.2%}')
"
```

## Common Patterns

### Compare on Specific Capability

```bash
for category in 01_Recent_Constraint_Tracking 02_Version_Update 03_Procedure_Transfer; do
    python eval/run_baselines.py \
        --category $category \
        --max-tasks 5 \
        --output outputs/baseline_comparison/${category}_results.json
done
```

### Budget Sensitivity Analysis

```bash
for budget in 4000 8000 12000 16000; do
    python eval/run_baselines.py \
        --budget $budget \
        --max-tasks 5 \
        --output outputs/baseline_comparison/budget_${budget}.json
done
```

## Tips

1. **Start small**: Use `--max-tasks 3` for quick iteration
2. **Focus on capability**: Use `--category` to test specific capabilities
3. **Check compression first**: Run without `--execute-tasks` to verify compression
4. **Compare visually**: Always generate charts for presentations
5. **Read reports**: `COMPREHENSIVE_REPORT.md` has detailed analysis
