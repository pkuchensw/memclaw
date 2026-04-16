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

## Not Yet Connected

- Real task-specific grading logic per scenario
- Ground-truth files for deterministic scoring
- Real external media/data assets

## Review-First Workflow

Per your requirement, no benchmark execution was performed.

Recommended review order:

1. tasks/TASK_INDEX.md
2. tasks/*/*.md
3. docs/ASSET_TODO.md
4. docs/INSTALL_EN.md or docs/INSTALL_ZH.md
5. eval/run_batch.py
