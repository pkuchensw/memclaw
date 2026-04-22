# State Memory Skill

## Purpose
Store factual state with version chain for tracking changes over time.

## When to Use
- **Trigger**: `capability_type == "state_revision"`
- **Signal**: Configuration update, rule change, version migration
- **Lifetime**: Persistent until explicitly superseded

## Storage Structure

```yaml
state_memory:
  states:
    - key: <state_name>
      current:
        value: <latest_value>
        source: <source_reference>
        timestamp: <iso_timestamp>
      history:
        - value: <old_value>
          source: <source_reference>
          timestamp: <iso_timestamp>
          superseded_by: <new_state_id>
      version_chain: [state_id_1, state_id_2, ...]
```

## Compilation Rules

1. **Identify state change**: Detect key-value updates in episode
2. **Create version link**: Connect old → new state
3. **Preserve provenance**: Record source and timestamp
4. **Enable rollback**: Keep history for potential reversion

## Example

```yaml
# Episode: "Change Python from 3.10 to 3.11, use uv not conda"
state_memory:
  states:
    - key: python_version
      current:
        value: "3.11"
        source: "user_turn_12"
        timestamp: "2024-01-15T10:30:00Z"
      history:
        - value: "3.10"
          source: "user_turn_3"
          timestamp: "2024-01-15T09:00:00Z"
          superseded_by: "state_12"
      version_chain: [state_3, state_12]
    
    - key: package_manager
      current:
        value: "uv"
        source: "user_turn_12"
        timestamp: "2024-01-15T10:30:00Z"
      history:
        - value: "conda"
          source: "user_turn_3"
          timestamp: "2024-01-15T09:00:00Z"
          superseded_by: "state_12"
```

## Why Version Chain?

- **Traceability**: Know what changed when
- **Conflict resolution**: Latest wins, but history explains why
- **Rollback**: Can revert if new version fails
- **Audit**: Understand decision evolution

## Query Patterns

```python
# Get latest state
get_state("python_version")  # Returns "3.11"

# Get state at specific time
get_state_at("python_version", "2024-01-15T09:30:00Z")  # Returns "3.10"

# Check if state changed between episodes
state_changed("python_version", episode_5, episode_12)  # Returns True
```
