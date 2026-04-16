# Installation Guide (English)

This guide covers environment setup and pre-run validation for OpenClaw-MemBench.

## 1. System Requirements

- OS: Linux (recommended)
- Python: 3.10+
- Optional: Docker and OpenClaw runtime for full end-to-end execution

## 2. Create Python Environment

Use either venv or conda.

### Option A: venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### Option B: conda

```bash
conda create -n openclaw-membench python=3.10 -y
conda activate openclaw-membench
pip install -U pip
pip install -r requirements.txt
```

## 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit .env according to your OpenClaw deployment.

Required fields for API-only execution:

- OPENCLAW_BASE_URL
- OPENCLAW_CHAT_COMPLETIONS_PATH
- OPENCLAW_MODEL
- OPENCLAW_API_KEY (if your gateway requires auth)

Example:

```env
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_CHAT_COMPLETIONS_PATH=/v1/chat/completions
OPENCLAW_MODEL=anthropic/claude-sonnet-4-5
OPENCLAW_API_KEY=
```

## 4. Pre-Run Review Checklist (Required Before Running)

1. Confirm task design: tasks/TASK_INDEX.md
2. Confirm missing external assets: docs/ASSET_TODO.md
3. Confirm workspace structures: workspace/*/task_*
4. Confirm budget profiles: configs/budgets.yaml
5. Confirm capability mapping: configs/capabilities.yaml

## 5. Optional Structural Validation (No Live Agent Execution)

```bash
python eval/run_batch.py --dry-run
```

This only checks task structure (prompt/checks/workspace path), not real OpenClaw execution.

## 6. Real API Execution (Minimal Code Changes)

The runner now supports real execution via API in eval/run_batch.py.

Run one task first:

```bash
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --output outputs/smoke_summary.json
```

Run one full category:

```bash
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --output outputs/c1_summary.json
```

Run all tasks:

```bash
python eval/run_batch.py --output outputs/all_summary.json
```

Generated artifacts per run include:

- request.json
- response.json
- transcript.json
- assistant.txt

These are saved under outputs/<category>/<task_id>/<timestamp>/.

## 7. Docker Guidance

- API-only run: Docker is optional.
- Reproducible benchmark run (recommended): use Docker/OpenClaw isolated runtime.

### Build isolated executor image

```bash
bash scripts/build_executor_image.sh
```

### Enable docker runtime

Set in .env:

```env
OPENCLAW_RUNTIME=docker
DOCKER_IMAGE=openclaw-membench-executor:latest
DOCKER_NETWORK=host
```

Then run (example):

```bash
python eval/run_batch.py --runtime docker --category 01_Recent_Constraint_Tracking --max-tasks 1 --output outputs/docker_smoke_summary.json
```

Per-task docker logs are written to each run output directory:

- docker_stdout.log
- docker_stderr.log

## 8. External Assets

Media files are intentionally excluded and tracked in docs/ASSET_TODO.md for manual import.
