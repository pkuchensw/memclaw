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

```env
OPENCLAW_RUNTIME=openclaw-docker
OPENCLAW_DOCKER_IMAGE=openclaw-membench-openclaw:latest
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

Some assets may benefit from supplementation. See [docs/ASSET_TODO.md](docs/ASSET_TODO.md) for details.

## Documentation

- [INSTALL_EN.md](docs/INSTALL_EN.md) / [INSTALL_ZH.md](docs/INSTALL_ZH.md) - Installation guides
- [BASELINES.md](docs/BASELINES.md) - Baseline detailed documentation
- [BASELINE_INTEGRATION_GUIDE.md](docs/BASELINE_INTEGRATION_GUIDE.md) - Open-source baseline integration
- [ASSET_TODO.md](docs/ASSET_TODO.md) - Assets preparation guide
- [CAPABILITY_BASED_DESIGN.md](docs/CAPABILITY_BASED_DESIGN.md) - Capability design

## Current Status

- Task files generated: 40 scenarios (+ template and index)
- Workspace stubs generated: 40
- Native baselines: 6 implemented
- Open-source baseline adapters: 3 implemented (LLMLingua, Selective Context, Mem0)
- Bilingual docs prepared: yes
- External assets included: yes (see ASSET_TODO.md for supplement suggestions)

## Acknowledgement

Design references:

- OpenClaw
- WildClawBench
- lossless-claw / LCM
