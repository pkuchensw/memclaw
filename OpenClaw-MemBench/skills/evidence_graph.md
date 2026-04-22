# Evidence Graph Skill

## Purpose
Track conflicting information sources and record arbitration decisions.

## When to Use
- **Trigger**: `capability_type == "evidence_arbitration"`
- **Signal**: Multiple sources provide conflicting information
- **Lifetime**: Persistent for audit and future similar conflicts

## Storage Structure

```yaml
evidence_graph:
  conflicts:
    - id: <conflict_id>
      topic: <what_is_being_disputed>
      sources:
        - id: source_1
          type: <user|file|log|tool_output>
          content: <excerpt_or_summary>
          timestamp: <when_recorded>
          reliability: <high|medium|low>
          provenance: <where_from>
        - id: source_2
          ...
      resolution:
        chosen_source: <source_id>
        reasoning: <why_this_source_chosen>
        confidence: <0.0-1.0>
        timestamp: <when_decided>
      arbitration_rules_applied:
        - rule: <which_heuristic_used>
          description: <why_applicable>
      related_conflicts: [<conflict_ids>]
```

## Compilation Rules

1. **Capture all sources**: Don't discard conflicting info prematurely
2. **Record provenance**: Where did each claim come from?
3. **Assess reliability**: User > file > log > assumption
4. **Document reasoning**: Why was one source chosen?
5. **Link related conflicts**: Build graph of similar disputes

## Example

```yaml
# Conflict: PyTorch version requirement
evidence_graph:
  conflicts:
    - id: "conflict_torch_version_20240115"
      topic: "Required PyTorch version"
      sources:
        - id: "user_statement"
          type: user
          content: "We need torch==2.1"
          timestamp: "2024-01-15T09:00:00Z"
          reliability: medium
          provenance: "user_turn_3"
        - id: "pyproject_toml"
          type: file
          content: "torch==2.3.0"
          timestamp: "2024-01-15T09:05:00Z"
          reliability: high
          provenance: "workspace/pyproject.toml"
        - id: "error_log"
          type: log
          content: "RuntimeError: CUDA error... requires torch>=2.3"
          timestamp: "2024-01-15T09:10:00Z"
          reliability: high
          provenance: "execution_stderr"
      resolution:
        chosen_source: "pyproject_toml"
        reasoning: "File is authoritative source of truth; error log confirms incompatibility with 2.1; user statement was approximate/outdated"
        confidence: 0.95
        timestamp: "2024-01-15T09:15:00Z"
      arbitration_rules_applied:
        - rule: "file_over_verbal"
          description: "Configuration files supersede verbal statements"
        - rule: "error_log_confirms"
          description: "Runtime errors validate file requirements"
      related_conflicts: ["conflict_python_version_20240110"]
```

## Arbitration Heuristics

| Priority | Rule | Description |
|----------|------|-------------|
| 1 | file_over_verbal | Config files > user statements |
| 2 | runtime_over_static | Error logs > declared requirements |
| 3 | recent_over_old | Newer timestamp > older |
| 4 | specific_over_general | Detailed spec > vague mention |
| 5 | authored_over_derived | Original source > secondary mention |

## Why Graph Structure?

- **Traceability**: Know why each decision was made
- **Learning**: Identify recurring conflict patterns
- **Consistency**: Apply same resolution to similar conflicts
- **Audit**: Review and justify past decisions

## Query Patterns

```python
# Find similar conflicts
find_conflicts(topic="python_version")  # Returns related conflicts

# Get resolution history
get_resolution_pattern(source_type="user", vs="file")  # "usually choose file"

# Check for recurring source reliability
get_source_reliability("user", topic="version_requirements")  # 0.6
get_source_reliability("pyproject.toml", topic="version_requirements")  # 0.95
```
