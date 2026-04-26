# OpenClaw-MemBench Docker Running Guide

This document describes how to run OpenClaw-MemBench evaluation in a Docker environment.

## Quick Start

### 1. Environment Preparation

Ensure the following are installed:
- Docker Desktop 28.0+
- Python 3.10+
- Git Bash (Windows) / Bash (Linux/Mac)

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env file and configure API key
```

Required configuration variables:
```bash
OPENCLAW_BASE_URL=https://api.openai.com/v1
OPENCLAW_API_KEY=your-api-key
OPENCLAW_MODEL=gpt-4
```

### 3. Build Docker Image

```bash
# Use the final Dockerfile
docker build -f docker/Dockerfile -t openclaw-membench:latest .
```

### 4. Run Evaluation

```bash
# Windows (Git Bash)
export MSYS_NO_PATHCONV=1
export OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --runtime openclaw-docker

# Linux/Mac
export OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --runtime openclaw-docker
```

## Docker Image Description

### Dockerfile Used

The project uses `docker/Dockerfile`, based on the official OpenClaw image, with critical issues fixed:

**Issue**: In the original image, `/usr/local/bin/openclaw` is a symbolic link to `/app/openclaw.mjs`. At runtime, the workspace is mounted to `/app`, causing the openclaw command to fail.

**Solution**: Copy openclaw to `/opt/openclaw/`, a location that won't be overwritten by mounting.

### Dockerfile Content

```dockerfile
FROM ghcr.io/openclaw/openclaw:2026.4.15

USER root

# Copy openclaw to a location that won't be overwritten by mounting
RUN mkdir -p /opt/openclaw /tmp_workspace /tmp_output /root/.openclaw && \
    cp -r /app/* /opt/openclaw/ && \
    chmod 777 /tmp_workspace /tmp_output && \
    rm -f /usr/local/bin/openclaw && \
    ln -s /opt/openclaw/openclaw.mjs /usr/local/bin/openclaw && \
    chmod +x /usr/local/bin/openclaw

ENV PATH="/usr/local/bin:${PATH}"
ENV HOME=/root

ENTRYPOINT []

RUN openclaw --version

WORKDIR /root
CMD ["tail", "-f", "/dev/null"]
```

## Running Parameters

### Command Line Arguments

```bash
python eval/run_batch.py \
  --runtime openclaw-docker \      # Use Docker runtime environment
  --category 01_Recent_Constraint_Tracking \  # Task category
  --max-tasks 1 \                   # Maximum number of tasks
  --output outputs/summary.json     # Output file
```

### Environment Variables

| Variable Name | Description | Default Value |
|--------|------|--------|
| `OPENCLAW_DOCKER_IMAGE` | Docker image name | `openclaw-membench:latest` |
| `OPENCLAW_BASE_URL` | API base URL | (required) |
| `OPENCLAW_API_KEY` | API key | (required) |
| `OPENCLAW_MODEL` | Model name | (required) |
| `MSYS_NO_PATHCONV` | Windows path conversion disable | `1` (Required for Windows) |

## Output Results

After successful execution, results are saved in the `outputs/` directory:

```
outputs/
├── summary.json                    # Evaluation results summary
└── 01_Recent_Constraint_Tracking/
    └── 01_Recent_Constraint_Tracking_task_01_arxiv_csv_digest/
        └── 20260424_231021/
            └── attempt_1/
                ├── agent.log       # Agent runtime log
                ├── chat.jsonl      # Complete conversation records
                ├── usage.json      # Token usage statistics
                └── results/        # Task output results
                    ├── arxiv_memory_rl.csv
                    ├── constraint_trace.json
                    ├── result.json
                    └── summary.md
```

## Common Issues

### 1. Windows Path Conversion Issue

**Symptom**: Docker command execution fails

**Solution**: Set `export MSYS_NO_PATHCONV=1`

### 2. openclaw Command Not Found

**Symptom**: `/bin/bash: line 1: openclaw: command not found`

**Solution**: Ensure the image is built with the correct Dockerfile

### 3. API Connection Failure

**Symptom**: Timeout or Connection Error

**Solution**: Check if the API configuration in `.env` is correct

## Baseline Comparison Testing

Use the `scripts/run_all_baselines.py` script to quickly compare performance of different compression methods:

```bash
# Quick mode (3 methods, recommended for environment verification)
python scripts/run_all_baselines.py --quick --category 01_Recent_Constraint_Tracking --task-num 1

# Full mode (6 methods)
python scripts/run_all_baselines.py --category 01_Recent_Constraint_Tracking --task-num 1

# Test all tasks
python scripts/run_all_baselines.py --category 01_Recent_Constraint_Tracking --all-tasks

# Validate structure only (without calling API)
python scripts/run_all_baselines.py --quick --dry-run --category 01_Recent_Constraint_Tracking --task-num 1
```

Output results:
- `outputs/<task_id>/baseline_comparison_*.md` - Markdown comparison report
- `outputs/<task_id>/baseline_comparison_*.json` - Raw data

## Installation Verification

```bash
# 1. Verify Docker image
docker images openclaw-membench:latest

# 2. Verify openclaw availability
docker run --rm openclaw-membench:latest openclaw --version

# 3. Run test task
export OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --runtime openclaw-docker
```

## Available Task Categories

| Category ID | Name |
|---------|------|
| 01_Recent_Constraint_Tracking | Recent Constraint Tracking |
| 02_Version_Update | Version Update |
| 03_Procedure_Transfer | Procedure Transfer |
| 04_Repeated_Mistake_Prevention | Repeated Mistake Prevention |
| 05_Source_Conflict_Resolution | Source Conflict Resolution |
| 06_Memory_Operation_Selection | Memory Operation Selection |
| 07_Goal_Interruption_Resumption | Goal Interruption and Task Resumption |
| 08_Staleness_Applicability_Judgment | Staleness and Applicability Judgment |
