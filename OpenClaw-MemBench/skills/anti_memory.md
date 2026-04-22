# Anti-Memory Skill

## Purpose
Store negative experiences and error patterns to prevent repeated mistakes.

## When to Use
- **Trigger**: `capability_type == "error_avoidance"`
- **Signal**: Failure followed by successful fix, pattern may recur
- **Lifetime**: Persistent until pattern becomes irrelevant

## Storage Structure

```yaml
anti_memory:
  patterns:
    - id: <pattern_id>
      trigger:
        condition: <when_to_check>
        context: <required_context_features>
      error:
        signature: <identifiable_error_pattern>
        cause: <root_cause_description>
      veto_rule:
        action: <action_to_prevent>
        reason: <explanation_for_veto>
      checklist:
        - item: <verification_step>
          command: <optional_command_to_run>
          expected: <expected_result>
      prevention:
        correct_action: <what_to_do_instead>
        preconditions: [<what_to_verify_first>]
      occurrence_count: <integer>
      last_triggered: <timestamp>
      effectiveness: <success_rate_of_prevention>
```

## Compilation Rules

1. **Extract error signature**: What error message/behavior identifies this?
2. **Identify trigger context**: When does this error typically occur?
3. **Define veto**: What action should be blocked?
4. **Create checklist**: Steps to verify before proceeding
5. **Specify alternative**: What to do instead of the vetoed action

## Example

```yaml
# Learned from CUDA installation failure
anti_memory:
  patterns:
    - id: "cuda_install_without_check"
      trigger:
        condition: "environment_setup && has_cuda_gpu"
        context: ["installing_pytorch", "cuda_related_package"]
      error:
        signature: "CUDA mismatch error OR nvcc not found OR GPU not detected"
        cause: "Installed PyTorch without checking CUDA compatibility first"
      veto_rule:
        action: "pip install torch=={any_version}"
        reason: "CUDA version unknown, installation likely to fail"
      checklist:
        - item: "Check NVIDIA driver version"
          command: "nvidia-smi --query-gpu=driver_version --format=csv,noheader"
          expected: "version_string"
        - item: "Check CUDA toolkit version"
          command: "nvcc --version | grep release"
          expected: "release X.X"
        - item: "Check Python version"
          command: "python --version"
          expected: "Python 3.X"
      prevention:
        correct_action: "Install torch with matching CUDA version"
        preconditions: [
          "driver_version >= 450.80.02",
          "cuda_version matches torch_cuda_version"
        ]
      occurrence_count: 3
      last_triggered: "2024-01-18T16:30:00Z"
      effectiveness: 1.0  # Has prevented error 3/3 times
```

## Activation Logic

```python
# Before taking action, check anti-memory
if action_matches_veto_rule(current_action, anti_memory):
    vetoed_pattern = find_matching_pattern(current_action, anti_memory)
    display_warning(vetoed_pattern.veto_rule.reason)
    
    # Run checklist
    checklist_results = run_checklist(vetoed_pattern.checklist)
    if all_passed(checklist_results):
        proceed_with_alternative(vetoed_pattern.prevention.correct_action)
    else:
        block_action("Checklist failed, cannot proceed safely")
```

## Why Separate from Positive Memory?

1. **Fast veto**: Don't need to search all positive procedures
2. **High priority**: Error prevention > success optimization
3. **Pattern specificity**: Error signatures are distinct
4. **Effectiveness tracking**: Monitor if pattern is still relevant

## Forgetting Strategy

Anti-memory should be forgotten when:
- Pattern no longer matches current environment
- Effectiveness drops below threshold (prevention fails)
- Context changes significantly (e.g., CUDA no longer used)
- Superseded by better prevention strategy
