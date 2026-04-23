# OpenClaw-MemBench Installation and Configuration Guide

This document covers environment setup, baseline configuration, and pre-run checks for OpenClaw-MemBench.

## 1. System Requirements

### Basic Requirements
- **OS**: Linux (recommended) / Windows 10+ / macOS
- **Python**: 3.10 or higher
- **RAM**: At least 8GB (16GB recommended)
- **Disk**: At least 5GB free space

### Optional Requirements (for Open-Source Baselines)
- **NVIDIA GPU**: For accelerating GPU-dependent baselines like LLMLingua (recommended but not required)
- **Docker**: For isolated runtime environment
- **OpenAI API Key**: For Mem0 baseline and real task execution

## 2. Create Python Environment

### Option A: venv (Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
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

## 3. Install Baseline Dependencies

### Native Baselines (Included in requirements.txt)

Basic native baselines require no extra installation:
- `sliding-window` - Sliding window truncation
- `keyword` - Keyword extraction
- `recursive-summary` - Recursive summarization
- `hierarchical` - Hierarchical memory
- `mem0` (native) - Mem0 simplified version
- `vector-retrieval` - Vector retrieval

### Open-Source Baselines (Recommended)

For comparison with real open-source implementations, **strongly recommended** to install:

#### 3.1 LLMLingua (Microsoft Prompt Compression Library)

```bash
# Basic installation
pip install llmlingua

# For GPU acceleration
pip install torch
```

**Note**: LLMLingua uses small LMs (e.g., Phi-2) for prompt compression, achieving up to 20x compression ratio.

#### 3.2 Selective Context (Self-Information Compression)

```bash
# Install library
pip install selective-context

# Download required spacy model
python -m spacy download en_core_web_sm
```

**Note**: Information-theoretic prompt compression method, EMNLP'23.

#### 3.3 Mem0 (Optional, Requires API Key)

```bash
# Install Mem0 and vector database
pip install mem0ai chromadb
```

**Note**: Real Mem0 system (41K+ stars), requires OpenAI API Key.

### One-Command Install for All Open-Source Baselines

```bash
pip install -r requirements-baselines.txt
python -m spacy download en_core_web_sm
```

### Verify Baseline Installation

```bash
python baselines/test_adapters.py
```

Expected output:
```
Testing Native Baselines
[OK] sliding-window: OK (reduction: 0.0%)
[OK] keyword: OK (reduction: -41.2%)
...

Open-source baseline status:
  llmlingua: [OK] Available  # or [MISSING] Not installed
  selective-context: [OK] Available
  mem0-lib: [MISSING] Not installed
```

## 4. Environment Variable Configuration

### 4.1 Copy Example Config

```bash
cp .env.example .env
```

### 4.2 Basic Configuration (Required)

Edit `.env` file:

```env
# OpenClaw API Configuration
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_CHAT_COMPLETIONS_PATH=/v1/chat/completions
OPENCLAW_MODEL=anthropic/claude-sonnet-4-5
OPENCLAW_API_KEY=your-api-key-here

# Compression Configuration
OPENCLAW_CONTEXT_BUDGET_CHARS=12000
OPENCLAW_COMPRESSION_METHOD=lcm-proxy
```

### 4.3 Baseline-Specific Configuration (Optional)

```env
# LLMLingua Configuration
LLMLINGUA_MODEL=microsoft/phi-2  # or gpt2 (faster)

# Selective Context Configuration
SELECTIVE_CONTEXT_GRANULARITY=sentence  # sentence/phrase/token

# Mem0 Configuration
OPENAI_API_KEY=your-openai-key  # Required for Mem0
MEM0_VECTOR_STORE=chroma  # chroma or qdrant
```

## 5. Pre-Run Checklist

### 5.1 Basic Checks

```bash
# 1. Check task index
head tasks/TASK_INDEX.md

# 2. Check workspace structure
ls workspace/01_Recent_Constraint_Tracking/

# 3. Check configuration files
cat configs/budgets.yaml
cat configs/capabilities.yaml
```

### 5.2 Structural Validation (No Real Task Execution)

```bash
python eval/run_batch.py --dry-run
```

Note: This only validates task file structure without calling APIs.

### 5.3 Assets Check

**Important**: Some tasks require real multimodal asset files.

```bash
# Check current assets status
python scripts/check_assets.py  # If available
```

Assets requiring manual preparation are listed in `docs/ASSET_TODO.md`.

**Currently Provided Assets**:
- `assets/conflicts/` - Conflict evidence files (5 case groups)
- `assets/email_calendar/` - Email and calendar files (25 emails, 4 ICS)
- `assets/images/` - Image files (~20 images)
- `assets/pdfs/` - PDF files (24 files)
- `assets/videos/` - Video files (6 videos with JSON markers)
- `assets/logs/` - Log files (10 failure logs)
- `assets/screenshots/` - Screenshots (8 images)
- `assets/tables/` - Table data (CSV and SQLite)

**Assets Needing Supplement**: See Section 7 below.

## 6. Quick Start

### 6.1 Test Single Baseline

```bash
# Test native baseline
python eval/run_baselines.py \
    --baselines keyword \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 1
```

### 6.2 Baseline Comparison (Recommended)

```bash
# Compare all available baselines
python eval/run_baselines.py \
    --baselines sliding-window,keyword,recursive-summary,hierarchical \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 5 \
    --budget 12000
```

### 6.3 Full Comparison with Open-Source Baselines

```bash
python eval/run_all_baselines.py \
    --baselines sliding-window,keyword,hierarchical,llmlingua,selective-context \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 10 \
    --execute-tasks
```

### 6.4 API Real Execution

```bash
# Smoke test (1 task)
python eval/run_batch.py \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 1 \
    --output outputs/smoke_summary.json

# Single capability (5 tasks)
python eval/run_batch.py \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 5 \
    --output outputs/c1_summary.json

# Full run
python eval/run_batch.py \
    --output outputs/all_summary.json
```

## 7. Assets Manual Preparation Guide

### 7.1 Current Assets Status

| Asset Type | Current | Recommended | Status |
|-----------|---------|-------------|--------|
| Conflicts | 5 groups | 8-10 groups | Can supplement |
| Email/Calendar | 25 emails | 40+ emails | Can supplement |
| Images | ~20 | 40+ | Needs more |
| PDFs | 24 | 24 | Sufficient |
| Videos | 6 | 8-10 | Can supplement |
| Logs | 10 | 10 | Sufficient |
| Screenshots | 8 | 10+ | Can supplement |
| Tables | 5 | 8-10 | Can supplement |

### 7.2 Assets Requiring Manual Preparation

**Detailed list in `docs/ASSET_TODO.md`**, key items:

#### Images (assets/images/)
- Need more **food_package** category images (currently mostly in fashion folder)
- Need more **document_scan** category images
- Suggest adding various sizes and orientations

#### Email/Calendar (assets/email_calendar/)
- Add more cross-timezone meeting scenarios
- Add recurring schedule conflict cases

#### Videos (assets/videos/)
- Ensure each video has corresponding `.json` timestamp marker file
- Supplement videos from different domains (lectures, product launches, etc.)

### 7.3 Assets Naming Convention

```
assets/
├── images/
│   ├── fashion/fashion_{NNN}.png
│   ├── food_package/food_{NNN}.png
│   └── document_scan/scan_{NNN}.png
├── pdfs/
│   ├── clean_paper_{NN}.pdf
│   ├── noisy_scan_{NN}.pdf
│   └── table_doc_{NN}.pdf
└── videos/
    ├── {task}_{NN}.mp4
    └── {task}_{NN}.json  # Timestamp marker file
```

## 8. Docker Runtime (Optional)

### 8.1 Build Image

```bash
bash scripts/build_executor_image.sh
```

### 8.2 Configure Docker Runtime

In `.env`:

```env
OPENCLAW_RUNTIME=docker
DOCKER_IMAGE=openclaw-membench-executor:latest
DOCKER_NETWORK=host
```

### 8.3 Run

```bash
python eval/run_batch.py \
    --runtime docker \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 1 \
    --output outputs/docker_smoke.json
```

## 9. FAQ

### Q1: LLMLingua installation fails or is very slow

**A**: LLMLingua depends on PyTorch and Transformers, which are large. Suggestions:

```bash
# Use domestic mirror for acceleration (China)
pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install llmlingua -i https://pypi.tuna.tsinghua.edu.cn/simple

# Or use CPU version (smaller)
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Q2: Selective Context reports missing `en_core_web_sm`

**A**:
```bash
python -m spacy download en_core_web_sm
# If slow, use direct download
python -m spacy download en_core_web_sm --direct
```

### Q3: Can I skip Open-Source Baselines installation?

**A**: Absolutely! Native baselines require no extra dependencies:

```bash
# Only use native baselines
python eval/run_baselines.py \
    --baselines sliding-window,keyword,recursive-summary,hierarchical \
    --max-tasks 5
```

### Q4: Why does Mem0 need OpenAI API Key?

**A**: Mem0 uses LLM for memory extraction and vectorization. If you don't want to use it:
1. Skip Mem0 baseline
2. Use native `mem0` baseline (simplified version, no API needed)

### Q5: How to confirm all assets are ready?

**A**: Run structural validation:

```bash
# Check required files for each task
python eval/run_batch.py --dry-run --category 01_Recent_Constraint_Tracking

# Check assets completeness
ls -la assets/images/fashion/ | wc -l
ls -la assets/pdfs/ | wc -l
ls -la assets/videos/*.mp4 | wc -l
```

## 10. Next Steps

1. **Read Documentation**:
   - [BASELINES.md](BASELINES.md) - Baseline detailed introduction
   - [BASELINE_INTEGRATION_GUIDE.md](BASELINE_INTEGRATION_GUIDE.md) - Integration usage guide
   - [ASSET_TODO.md](ASSET_TODO.md) - Assets preparation checklist

2. **Run Tests**:
   ```bash
   python baselines/test_adapters.py
   ```

3. **Start Experiments**:
   ```bash
   python eval/run_all_baselines.py --max-tasks 5
   ```

## Reference Documentation

- [BASELINES.md](BASELINES.md) - Baseline detailed description
- [BASELINE_INTEGRATION_GUIDE.md](BASELINE_INTEGRATION_GUIDE.md) - Open-source baseline integration guide
- [BASELINE_QUICK_REFERENCE.md](BASELINE_QUICK_REFERENCE.md) - Quick reference
- [ASSET_TODO.md](ASSET_TODO.md) - Assets preparation checklist
- [CAPABILITY_BASED_DESIGN.md](CAPABILITY_BASED_DESIGN.md) - Capability design document
