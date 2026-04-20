I'll start by examining the workspace structure and reading the prior constraints to understand the current state before producing the final artifacts. Let me check the episodes and evidence directories.```python
import os
import json
import csv

# Define workspace paths
workspace = "/jizhicfs/pkuhetu/siwei/Memclaw/OpenClaw-MemBench/workspace/07_Goal_Interruption_Resumption/task_34_interrupted_media_task_resume"
episodes_dir = os.path.join(workspace, "episodes")
evidence_dir = os.path.join(workspace, "evidence")
results_dir = os.path.join(workspace, "results")

# Create results directory if it doesn't exist
os.makedirs(results_dir, exist_ok=True)

# List files in episodes and evidence directories
print("=== Episodes Directory ===")
if os.path.exists(episodes_dir):
    for f in os.listdir(episodes_dir):
        print(f"  {f}")
else:
    print("  Directory does not exist")

print("\n=== Evidence Directory ===")
if os.path.exists(evidence_dir):
    for f in os.listdir(evidence_dir):
        print(f"  {f}")
else:
    print("  Directory does not exist")

# Read context_notes.md
context_notes_path = os.path.join(episodes_dir, "context_notes.md")
if os.path.exists(context_notes_path):
    with open(context_notes_path, 'r') as f:
        print("\n=== context_notes.md ===")
        print(f.read())

# Read sources.md
sources_path = os.path.join(evidence_dir, "sources.md")
if os.path.exists(sources_path):
    with open(sources_path, 'r') as f:
        print("\n=== sources.md ===")
        print(f.read())
```
