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

- `tasks/`: Task definitions in English markdown (WildClaw-style sections)
- `workspace/`: Per-task isolated workspace stubs
- `configs/`: Budget and capability mapping configs
- `eval/`: Batch runner and validation entrypoint
- `baselines/`: Context compression baselines (native + open-source adapters)
- `utils/`: Task parser and score aggregation helpers
- `docker/`: Docker configurations for containerized execution
- `scripts/`: Build and run scripts
- `docs/`: Bilingual documentation and setup guides
- `assets/`: Multimodal resources (images, videos, PDFs, logs, etc.)

## Quick Start

### 1. Installation

```bash
# Clone and setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: Install open-source baselines for comparison
pip install -r requirements-baselines.txt
python -m spacy download en_core_web_sm
```

### 2. Configuration

```bash
cp .env.example .env
# Edit .env with your API credentials
```

### 3. Test Baselines

```bash
# Test all baselines
python baselines/test_adapters.py

# Run baseline comparison
python eval/run_baselines.py \
    --baselines sliding-window,keyword,llmlingua \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 5
```

### 4. Run Evaluation

```bash
# Structural dry-run (no API calls)
python eval/run_batch.py --dry-run

# Real execution (1 task smoke test)
python eval/run_batch.py \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 1 \
    --output outputs/smoke_summary.json
```

---

## Docker Deployment (Recommended)

The benchmark can be run inside Docker containers for isolated and reproducible execution.

### Prerequisites

- Docker 20.10+ installed and running
- Docker Compose 2.0+ (optional, for docker-compose deployment)
- At least 4GB free RAM for container operations

### Docker Setup Options

#### Option 1: Build and Run with Scripts (Recommended)

```bash
# Step 1: Build the Docker image
bash scripts/build_openclaw_image.sh

# Step 2: Test Docker setup
bash scripts/test_docker_setup.sh

# Step 3: Run benchmark with Docker
bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 1
```

#### Option 2: Manual Docker Build

```bash
# Build the standalone image
docker build -f docker/Dockerfile.standalone -t openclaw-membench:latest .

# Verify installation
docker run --rm openclaw-membench:latest openclaw --version
```

#### Option 3: Docker Compose

```bash
# Start the benchmark environment
docker-compose up -d openclaw-membench

# Execute commands inside container
docker-compose exec openclaw-membench bash

# Inside container, run benchmark
openclaw --version
```

### Docker Environment Variables

Configure these in your `.env` file:

```bash
# Runtime configuration
OPENCLAW_RUNTIME=openclaw-docker
OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest

# API configuration (required)
OPENCLAW_BASE_URL=https://api.openai.com/v1
OPENCLAW_API_KEY=your-api-key-here
OPENCLAW_MODEL=gpt-4

# Docker-specific settings
OPENCLAW_DOCKER_NETWORK=host
OPENCLAW_DOCKER_PRESERVE_CONTAINER=false
OPENCLAW_DOCKER_HIDE_PATTERNS=oracle.yaml,grader.py,gt,answers,solution,expected
```

### Running Benchmarks with Docker

```bash
# Run single category
bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 5

# Run all tasks in a category
bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 100

# Run specific category with custom output
bash scripts/run_openclaw_docker.sh 02_Version_Update 10 outputs/version_results.json
```

### Docker Troubleshooting

**Issue: Docker daemon not running**
```bash
# Start Docker Desktop or Docker service
sudo systemctl start docker  # Linux
# Or open Docker Desktop application  # Windows/Mac
```

**Issue: Image build fails**
```bash
# Check Docker is running
docker info

# Try building with no cache
docker build --no-cache -f docker/Dockerfile.standalone -t openclaw-membench:latest .
```

**Issue: Container cannot connect to API**
```bash
# Use host network mode (default)
# Or configure proper network in docker-compose.yml
export OPENCLAW_DOCKER_NETWORK=host
```

**Issue: Permission denied when running scripts**
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

---

## Available Baselines

### Native Baselines (No Extra Dependencies)

| Baseline | Description | Best For |
|----------|-------------|----------|
| `sliding-window` | Simple recency truncation | Quick baseline |
| `keyword` | Keyword-based filtering | Constraint-heavy tasks |
| `recursive-summary` | Episode summarization | Multi-episode scenarios |
| `hierarchical` | Multi-tier memory | Mixed recency scenarios |
| `mem0` | Native Mem0 simulation | Quick testing without setup |
| `vector-retrieval` | TF-IDF retrieval | Semantic similarity |

### Open-Source Baselines (Real Implementations)

| Baseline | Source | Paper | Why Use |
|----------|--------|-------|---------|
| `llmlingua` | [Microsoft](https://github.com/microsoft/LLMLingua) | EMNLP'23, ACL'24 | SOTA prompt compression (up to 20x) |
| `selective-context` | [liyucheng](https://github.com/liyucheng09/Selective_Context) | EMNLP'23 | Information-theoretic filtering |
| `mem0-lib` | [Mem0](https://github.com/mem0ai/mem0) | arXiv'25 | Real memory system (41K+ stars) |

Install open-source baselines:
```bash
pip install llmlingua selective-context
# Optional: For Mem0
pip install mem0ai chromadb
export OPENAI_API_KEY="your-key"
```

## Task Format

Each task markdown contains:

- Prompt
- Expected Behavior
- Grading Criteria
- Automated Checks (Python)
- Workspace Path
- Skills / Env / Warmup

Reference template: [tasks/task_template.md](tasks/task_template.md)

## Real OpenClaw Runtime (WildClawBench-like)

This mode runs tasks inside an isolated container and calls OpenClaw gateway + agent directly.

1. Build an OpenClaw-capable image:

```bash
bash scripts/build_openclaw_image.sh
```

2. Set runtime in `.env`:

```bash
OPENCLAW_RUNTIME=openclaw-docker
OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest
```

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

Compression profile placeholders are in [configs/budgets.yaml](configs/budgets.yaml):

- `full-context` - No compression
- `lcm-medium-budget` - Moderate compression
- `lcm-low-budget` - Aggressive compression
- `lcm-stress-budget` - Extreme compression

These can be connected to lossless-claw/LCM runtime policies in your OpenClaw deployment.

## Assets Status

The benchmark includes multimodal assets for realistic evaluation:

| Asset Type | Current | Status |
|-----------|---------|--------|
| Conflicts | 5 groups | Available |
| Email/Calendar | 25 emails, 4 ICS | Available |
| Images | ~20 images | Available |
| PDFs | 24 files | Available |
| Videos | 6 videos | Available |
| Logs | 10 logs | Available |
| Screenshots | 8 images | Available |
| Tables | 5 files | Available |

## Documentation

- [INSTALL_EN.md](docs/INSTALL_EN.md) / [INSTALL_ZH.md](docs/INSTALL_ZH.md) - Installation guides
- [BASELINES.md](docs/BASELINES.md) - Baseline detailed documentation
- [CAPABILITY_BASED_DESIGN.md](docs/CAPABILITY_BASED_DESIGN.md) - Capability design

## Current Status

- Task files generated: 40 scenarios (+ template and index)
- Workspace stubs generated: 40
- Native baselines: 6 implemented
- Open-source baseline adapters: 3 implemented (LLMLingua, Selective Context, Mem0)
- Bilingual docs prepared: yes
- External assets included: yes
- Docker support: Full containerized execution

## Docker Architecture

The benchmark supports multiple Docker deployment modes:

### 1. Standalone Mode (`docker/Dockerfile.standalone`)

Self-contained image with:
- Ubuntu 22.04 base
- Node.js 20.x and OpenClaw CLI
- Python 3 with required dependencies
- No external base image dependencies

### 2. Executor Mode (`docker/Dockerfile.executor`)

Full project image for development:
- Extends standalone image
- Includes complete project code
- Can run benchmarks directly

### 3. Docker Compose (`docker-compose.yml`)

Orchestrated deployment with:
- Volume mounts for development
- Host network access for API calls
- Health checks and resource limits

## Benchmark Execution Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Task Parser   │────▶│  OpenClaw Agent  │────▶│    Grading      │
│  (load .md)     │     │  (in container)  │     │  (automated)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Load scenario  │     │  Run in sandbox  │     │  Score output   │
│  workspace      │     │  with skills     │     │  against oracle │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Acknowledgement

Design references:

- OpenClaw
- WildClawBench
- lossless-claw / LCM
