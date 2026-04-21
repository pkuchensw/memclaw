# Workspace for Task 01: ArXiv Digest (Capability-first)

This task is designed to stress **Recent Constraint Tracking** under noisy multi-episode history.

Focus:
- Keep newest slot constraints (year/topic/schema/path).
- Reject stale constraints from old memo/cache snippets.
- Produce deterministic CSV artifact.

Directory roles:
- `episodes/`: context notes and evolving constraints.
- `evidence/`: conflicting source statements with trust hints.
- `results/`: target output directory for final artifacts.

Required outputs (results/):
- `arxiv_memory_rl.csv`
- `constraint_trace.json`
- `result.json`
- `summary.md`
- `manifest.csv`
