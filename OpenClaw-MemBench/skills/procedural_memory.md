# Procedural Memory Skill

## Purpose
Extract reusable procedure templates from successful task executions.

## When to Use
- **Trigger**: `capability_type == "procedural_reuse"`
- **Signal**: Successful completion of structured task, similar task upcoming
- **Lifetime**: Persistent, updated with refinements

## Storage Structure

```yaml
procedural_memory:
  procedures:
    - id: <procedure_id>
      trigger:
        pattern: <task_signature>
        conditions: [<criteria_for_applicability>]
      steps:
        - order: 1
          action: <action_template>
          verification: <success_condition>
          rollback: <undo_action>
        - order: 2
          action: <action_template>
          ...
      parameters:
        - name: <param_name>
          type: <data_type>
          description: <usage>
          required: true/false
      success_rate: <float>
      usage_count: <integer>
      last_used: <timestamp>
```

## Compilation Rules

1. **Abstract concrete values**: Replace specific strings with parameters
2. **Preserve step order**: Critical for correct execution
3. **Add verification**: Each step should have success check
4. **Include rollback**: Enable recovery from failure
5. **Track success**: Update rate based on reuse outcomes

## Example

```yaml
# Extracted from successful arXiv paper search
procedural_memory:
  procedures:
    - id: "arxiv_to_csv_pipeline"
      trigger:
        pattern: "search academic papers AND export to table"
        conditions: ["has_source=arxiv|acl|iclr", "output_format=csv|table"]
      steps:
        - order: 1
          action: "query_papers(source={source}, keywords={keywords}, year_range={year_range})"
          verification: "results.count > 0"
          rollback: "broaden_keywords"
        - order: 2
          action: "filter_by_year(results, {year_range})"
          verification: "filtered.count > 0"
        - order: 3
          action: "filter_by_topic(results, {topics})"
          verification: "filtered.count > 0"
        - order: 4
          action: "deduplicate(results)"
          verification: "no_duplicates_in(results)"
        - order: 5
          action: "export_csv(results, path={output_path}, columns={schema})"
          verification: "file_exists({output_path})"
      parameters:
        - name: source
          type: enum[arxiv, acl, iclr]
          required: true
        - name: keywords
          type: list[string]
          required: true
        - name: year_range
          type: string
          description: "YYYY-YYYY format"
          required: true
        - name: topics
          type: list[string]
          required: true
        - name: output_path
          type: path
          required: true
        - name: schema
          type: list[string]
          default: ["title", "authors", "year", "url"]
      success_rate: 0.95
      usage_count: 12
      last_used: "2024-01-20T14:00:00Z"
```

## Why Not Free Text?

Free text procedure:
- "First search arXiv, then filter by year..."

Misses:
- Parameter boundaries (which parts vary?)
- Verification points (when to know step succeeded?)
- Rollback actions (what if step fails?)
- Trigger conditions (when is this applicable?)

Structured procedural memory enables:
- **Automatic matching**: Check if new task fits trigger
- **Parameter filling**: Extract values from new task
- **Step validation**: Verify each step before proceeding
- **Failure recovery**: Rollback to last known good state
