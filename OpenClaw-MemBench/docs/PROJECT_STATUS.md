# Project Status

Date: 2026-04-16

## Delivered

- Benchmark scaffold with English-first task construction
- 8 capability categories under tasks/
- 40 scenario task files generated
- 40 workspace stubs generated
- Capability mapping and budget config files
- Batch eval entrypoint with dry-run validation and API-backed real execution
- Docker-isolated runtime mode (per-task container execution)
- Bilingual documentation (English + Chinese)
- External asset tracking doc
- Scenario replay support via workspace scenario.jsonl
- Skill-card injection system with registry and defaults
- Long-context generator for all 40 tasks (scenario + oracle)
- Multi-method compression comparison (full/lcm-proxy/window/keyword/episode)
- Compression trace metrics in usage logs

## Not Yet Connected

- Real task-specific grading logic per scenario
- Ground-truth files for deterministic scoring
- Real external media/data assets
- Native OpenClaw LCM API hooks (currently lcm-proxy abstraction)
- Real tool-level multi-step execution trace grading (beyond artifact checks)

## Review-First Workflow

Per your requirement, no benchmark execution was performed.

Recommended review order:

1. tasks/TASK_INDEX.md
2. tasks/*/*.md
3. docs/ASSET_TODO.md
4. docs/INSTALL_EN.md or docs/INSTALL_ZH.md
5. eval/run_batch.py
