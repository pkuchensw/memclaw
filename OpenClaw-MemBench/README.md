# OpenClaw-MemBench

Capability-first benchmark for evaluating memory and context management of OpenClaw agents under context compression.

## Overview

OpenClaw-MemBench focuses on long-horizon, multi-episode agent tasks where failures are often caused by memory mistakes rather than tool incapability.

This benchmark is inspired by the task organization style of WildClawBench, but targets memory-specific capability gaps:

1. Recent Constraint Tracking
2. Version Update
3. Procedure Transfer
4. Repeated Mistake Prevention
5. Source Conflict Resolution
6. Memory Operation Selection
7. Goal Interruption and Task Resumption
8. Staleness and Applicability Judgment

Each capability currently contains 5 scenarios, for 40 scenarios in total.

## Repository Structure

- tasks/: Task definitions in English markdown (WildClaw-style sections)
- workspace/: Per-task isolated workspace stubs
- configs/: Budget and capability mapping configs
- eval/: Batch runner and validation entrypoint
- utils/: Task parser and score aggregation helpers
- docs/: Bilingual documentation and setup guides
- assets/: Placeholder for external media files (manual import)

## Task Format

Each task markdown contains:

- Prompt
- Expected Behavior
- Grading Criteria
- Automated Checks (Python)
- Workspace Path
- Skills / Env / Warmup

Reference template: tasks/task_template.md

## Quick Start (No Execution)

This project supports a safe pre-run inspection workflow.

1. Review benchmark scope in docs/PROJECT_STATUS.md
2. Review setup prerequisites in docs/INSTALL_EN.md or docs/INSTALL_ZH.md
3. Review missing assets in docs/ASSET_TODO.md
4. Review scenario list in tasks/TASK_INDEX.md
5. Review any task file under tasks/*/*.md

No benchmark command needs to be executed before this review.

## Optional Validation Commands (Run Only After Your Approval)

```bash
# Structural dry-run only (no OpenClaw live execution)
python eval/run_batch.py --dry-run

# Category-level structural check
python eval/run_batch.py --dry-run --category 01_Recent_Constraint_Tracking
```

## Real Execution by API (Only Modify .env)

The runner supports API-backed execution now. You only need to configure API fields in .env:

- OPENCLAW_BASE_URL
- OPENCLAW_CHAT_COMPLETIONS_PATH
- OPENCLAW_MODEL
- OPENCLAW_API_KEY (if required)

Then run a smoke test:

```bash
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --output outputs/smoke_summary.json
```

## Docker Isolated Runtime

Build executor image once:

```bash
bash scripts/build_executor_image.sh
```

Enable docker runtime in `.env` and run:

```bash
python eval/run_batch.py --runtime docker --category 01_Recent_Constraint_Tracking --max-tasks 1 --output outputs/docker_smoke_summary.json
```

## Real OpenClaw Runtime (WildClawBench-like)

This mode runs tasks inside an isolated container and calls OpenClaw gateway + agent directly.

1. Build an OpenClaw-capable image:

```bash
bash scripts/build_openclaw_image.sh
```

2. Set runtime in `.env`:

- `OPENCLAW_RUNTIME=openclaw-docker`
- `OPENCLAW_DOCKER_IMAGE=openclaw-membench-openclaw:latest`

3. Run capability-focused smoke test:

```bash
bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 1 outputs/openclaw_smoke.json
```

### Anti-leak safeguards

- Task workspace is copied into a sandbox before execution.
- Hidden files are removed before agent starts (`OPENCLAW_DOCKER_HIDE_PATTERNS`).
- Grading runs after execution against copied outputs.
- Agent never sees injected grading runtime code.

### Capability-first enforcement

Runner validates every task maps to one primary capability by category.
If category-capability mapping is inconsistent, task is marked `task_schema_error`.

## Context Compression Profiles

Compression profile placeholders are in configs/budgets.yaml:

- full-context
- lcm-medium-budget
- lcm-low-budget
- lcm-stress-budget

These can be connected to lossless-claw/LCM runtime policies in your OpenClaw deployment.

## Current Status

- Task files generated: 40 scenarios (+ template and index)
- Workspace stubs generated: 40
- Bilingual docs prepared: yes
- External assets included: no (tracked in docs/ASSET_TODO.md)

## Acknowledgement

Design references:

- OpenClaw
- WildClawBench
- lossless-claw / LCM
