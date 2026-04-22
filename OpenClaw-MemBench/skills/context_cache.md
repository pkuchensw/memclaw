# Context Cache Skill

## Purpose
Maintain lightweight near-field memory for recent constraints and active task state.

## When to Use
- **Trigger**: `capability_type == "context_retention"`
- **Signal**: Recent instructions not yet executed, active format/path constraints
- **Lifetime**: Ephemeral, cleared after task completion

## Storage Structure

```yaml
context_cache:
  recent_raw_span: <last N turns verbatim>
  key_slots:
    - slot: <name>
      value: <current_value>
      source: <turn_id>
      superseded: [<old_value1, old_value2>]
  unfinished_subgoals:
    - subgoal: <description>
      status: <pending|in_progress>
      dependencies: []
  active_constraints:
    format: <format_requirement>
    path: <output_path>
    schema: <column_names>
    filter: <criteria>
```

## Compilation Rules

1. **Extract from episode**: Parse user instructions for fixed slots
2. **Track changes**: Log superseded values with turn references
3. **Preserve recency**: Keep latest 3-5 turns verbatim
4. **Clear on completion**: Flush after task success/failure

## Example

```yaml
# Episode: "Search 2024-2025 arXiv papers on RL+memory, output CSV"
context_cache:
  recent_raw_span: "Search 2024-2025 arXiv papers..."
  key_slots:
    - slot: year_range
      value: "2024-2025"
      source: turn_5
      superseded: ["2023-2025"]
    - slot: topic_filter
      value: ["reinforcement learning", "memory agent"]
      source: turn_5
    - slot: output_format
      value: "CSV"
      source: turn_5
      superseded: ["markdown table"]
  active_constraints:
    format: "CSV with columns: title,authors,year,url,topic_tag"
    path: "/tmp_workspace/results/arxiv_memory_rl.csv"
```

## Why Not Summary?

Summary loses:
- Exact year range boundaries
- Specific column ordering
- Output path precision
- Superseded value history

Context cache preserves these verbatim for deterministic execution.
