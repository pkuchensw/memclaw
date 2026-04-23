# OpenClaw-MemBench 安装与配置指南

本文档详细介绍 OpenClaw-MemBench 的环境安装、baseline 配置以及运行前检查。

## 1. 系统要求

### 基础要求
- **操作系统**: Linux (推荐) / Windows 10+ / macOS
- **Python**: 3.10 及以上
- **内存**: 至少 8GB RAM（推荐 16GB）
- **磁盘**: 至少 5GB 可用空间

### 可选要求（用于 Open-Source Baselines）
- **NVIDIA GPU**: 用于加速 LLMLingua 等需要 GPU 的 baseline（推荐但不必须）
- **Docker**: 用于隔离运行环境
- **OpenAI API Key**: 用于 Mem0 baseline 和真实任务执行

## 2. 创建 Python 环境

### 方案 A：venv（推荐）

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

### 方案 B：conda

```bash
conda create -n openclaw-membench python=3.10 -y
conda activate openclaw-membench
pip install -U pip
pip install -r requirements.txt
```

## 3. 安装 Baseline 依赖

### 基础 Baselines（已包含在 requirements.txt）

基础 native baselines 无需额外安装：
- `sliding-window` - 滑动窗口
- `keyword` - 关键词提取
- `recursive-summary` - 递归摘要
- `hierarchical` - 分层记忆
- `mem0` (native) - Mem0 简化版
- `vector-retrieval` - 向量检索

### Open-Source Baselines（推荐安装）

为了与真实开源实现对比，**强烈建议**安装以下依赖：

#### 3.1 LLMLingua（微软提示压缩库）

```bash
# 基础安装
pip install llmlingua

# 如果需要 GPU 加速
pip install torch
```

**说明**: LLMLingua 使用小型 LM（如 Phi-2）压缩提示，可达 20x 压缩率。

#### 3.2 Selective Context（自信息压缩）

```bash
# 安装库
pip install selective-context

# 下载必需的 spacy 模型
python -m spacy download en_core_web_sm
```

**说明**: 基于信息论的提示压缩方法，EMNLP'23。

#### 3.3 Mem0（可选，需要 API Key）

```bash
# 安装 Mem0 和向量数据库
pip install mem0ai chromadb
```

**说明**: 真实 Mem0 系统（41K+ stars），需要 OpenAI API Key。

### 一键安装所有 Open-Source Baselines

```bash
pip install -r requirements-baselines.txt
python -m spacy download en_core_web_sm
```

### 验证 Baseline 安装

```bash
python baselines/test_adapters.py
```

预期输出：
```
Testing Native Baselines
[OK] sliding-window: OK (reduction: 0.0%)
[OK] keyword: OK (reduction: -41.2%)
...

Open-source baseline status:
  llmlingua: [OK] Available  # 或 [MISSING] Not installed
  selective-context: [OK] Available
  mem0-lib: [MISSING] Not installed
```

## 4. 环境变量配置

### 4.1 复制示例配置

```bash
cp .env.example .env
```

### 4.2 基础配置（必须）

编辑 `.env` 文件：

```env
# OpenClaw API 配置
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_CHAT_COMPLETIONS_PATH=/v1/chat/completions
OPENCLAW_MODEL=anthropic/claude-sonnet-4-5
OPENCLAW_API_KEY=your-api-key-here

# 压缩配置
OPENCLAW_CONTEXT_BUDGET_CHARS=12000
OPENCLAW_COMPRESSION_METHOD=lcm-proxy
```

### 4.3 Baseline 专用配置（可选）

```env
# LLMLingua 配置
LLMLINGUA_MODEL=microsoft/phi-2  # 或 gpt2（更快）

# Selective Context 配置
SELECTIVE_CONTEXT_GRANULARITY=sentence  # sentence/phrase/token

# Mem0 配置
OPENAI_API_KEY=your-openai-key  # Mem0 需要
MEM0_VECTOR_STORE=chroma  # chroma 或 qdrant
```

## 5. 运行前检查清单

### 5.1 基础检查

```bash
# 1. 检查任务索引
head tasks/TASK_INDEX.md

# 2. 检查 workspace 结构
ls workspace/01_Recent_Constraint_Tracking/

# 3. 检查配置文件
cat configs/budgets.yaml
cat configs/capabilities.yaml
```

### 5.2 结构校验（不跑真实任务）

```bash
python eval/run_batch.py --dry-run
```

说明：该命令只校验任务文件结构，不会调用 API。

### 5.3 Assets 检查

**重要**: 部分任务需要真实的多模态资源文件。

```bash
# 检查当前 assets 状态
python scripts/check_assets.py  # 如果存在
```

需要手动准备的 assets 清单见 `docs/ASSET_TODO.md`。

**当前已提供的 Assets**:
- ✅ `assets/conflicts/` - 冲突证据文件（5 组案例）
- ✅ `assets/email_calendar/` - 邮件和日历文件（25 封邮件，4 个 ICS）
- ✅ `assets/images/` - 图片文件（约 20 张）
- ✅ `assets/pdfs/` - PDF 文件（24 个）
- ✅ `assets/videos/` - 视频文件（6 个，带 JSON 标记）
- ✅ `assets/logs/` - 日志文件（10 个失败日志）
- ✅ `assets/screenshots/` - 截图（8 张）
- ✅ `assets/tables/` - 表格数据（CSV 和 SQLite）

**需要补充的 Assets**: 见本文档第 7 节。

## 6. 快速开始

### 6.1 测试单个 Baseline

```bash
# 测试 native baseline
python eval/run_baselines.py \
    --baselines keyword \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 1
```

### 6.2 Baseline 对比（推荐）

```bash
# 对比所有可用 baselines
python eval/run_baselines.py \
    --baselines sliding-window,keyword,recursive-summary,hierarchical \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 5 \
    --budget 12000
```

### 6.3 包含 Open-Source Baselines 的完整对比

```bash
python eval/run_all_baselines.py \
    --baselines sliding-window,keyword,hierarchical,llmlingua,selective-context \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 10 \
    --execute-tasks
```

### 6.4 API 真实执行

```bash
# 冒烟测试（1 个任务）
python eval/run_batch.py \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 1 \
    --output outputs/smoke_summary.json

# 单个能力类（5 个任务）
python eval/run_batch.py \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 5 \
    --output outputs/c1_summary.json

# 全量运行
python eval/run_batch.py \
    --output outputs/all_summary.json
```

## 7. Assets 手动准备指南

### 7.1 当前 Assets 状态

| Asset 类型 | 当前数量 | 推荐数量 | 状态 |
|-----------|---------|---------|------|
| 冲突证据 (conflicts) | 5 组 | 8-10 组 | ⚠️ 可补充 |
| 邮件/日历 (email_calendar) | 25 封邮件 | 40+ 封 | ⚠️ 可补充 |
| 图片 (images) | ~20 张 | 40+ 张 | ⚠️ 需补充 |
| PDFs | 24 个 | 24 个 | ✅ 充足 |
| 视频 (videos) | 6 个 | 8-10 个 | ⚠️ 可补充 |
| 日志 (logs) | 10 个 | 10 个 | ✅ 充足 |
| 截图 (screenshots) | 8 张 | 10+ 张 | ⚠️ 可补充 |
| 表格 (tables) | 5 个 | 8-10 个 | ⚠️ 可补充 |

### 7.2 需要手动准备的 Assets

**详细清单见 `docs/ASSET_TODO.md`**，关键补充项：

#### 图片 (assets/images/)
- 需要更多 **food_package** 类别图片（当前大部分在 fashion 目录）
- 需要更多 **document_scan** 类别图片
- 建议添加不同尺寸和方向的图片

#### 邮件/日历 (assets/email_calendar/)
- 补充更多跨时区会议场景
- 添加重复日程冲突案例

#### 视频 (assets/videos/)
- 确保每个视频都有对应的 `.json` 时间标记文件
- 补充不同领域的视频（讲座、产品发布等）

### 7.3 Assets 命名规范

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
    └── {task}_{NN}.json  # 时间标记文件
```

## 8. Docker 运行（可选）

### 8.1 构建镜像

```bash
bash scripts/build_executor_image.sh
```

### 8.2 配置 Docker 运行

在 `.env` 中设置：

```env
OPENCLAW_RUNTIME=docker
DOCKER_IMAGE=openclaw-membench-executor:latest
DOCKER_NETWORK=host
```

### 8.3 运行

```bash
python eval/run_batch.py \
    --runtime docker \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 1 \
    --output outputs/docker_smoke.json
```

## 9. 常见问题

### Q1: LLMLingua 安装失败或很慢

**A**: LLMLingua 依赖 PyTorch 和 Transformers，较大。建议：

```bash
# 使用国内镜像加速
pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install llmlingua -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用 CPU 版本（更小）
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Q2: Selective Context 提示缺少 `en_core_web_sm`

**A**:
```bash
python -m spacy download en_core_web_sm
# 如果慢，使用镜像
python -m spacy download en_core_web_sm --direct
```

### Q3: 我不想安装 Open-Source Baselines，可以吗？

**A**: 完全可以！Native baselines 无需额外依赖：

```bash
# 只使用 native baselines
python eval/run_baselines.py \
    --baselines sliding-window,keyword,recursive-summary,hierarchical \
    --max-tasks 5
```

### Q4: Mem0 为什么需要 OpenAI API Key？

**A**: Mem0 使用 LLM 进行记忆提取和向量化。如果不想使用，可以：
1. 跳过 Mem0 baseline
2. 使用 native `mem0` baseline（简化版，无需 API）

### Q5: 如何确认所有 assets 都已准备好？

**A**: 运行结构校验：

```bash
# 检查每个任务的必要文件
python eval/run_batch.py --dry-run --category 01_Recent_Constraint_Tracking

# 检查 assets 完整性
ls -la assets/images/fashion/ | wc -l
ls -la assets/pdfs/ | wc -l
ls -la assets/videos/*.mp4 | wc -l
```

## 10. 下一步

1. **阅读文档**:
   - [BASELINES.md](BASELINES.md) - Baseline 详细介绍
   - [BASELINE_INTEGRATION_GUIDE.md](BASELINE_INTEGRATION_GUIDE.md) - 集成使用指南
   - [ASSET_TODO.md](ASSET_TODO.md) - Assets 准备清单

2. **运行测试**:
   ```bash
   python baselines/test_adapters.py
   ```

3. **开始实验**:
   ```bash
   python eval/run_all_baselines.py --max-tasks 5
   ```

## 参考文档

- [BASELINES.md](BASELINES.md) - Baseline 详细说明
- [BASELINE_INTEGRATION_GUIDE.md](BASELINE_INTEGRATION_GUIDE.md) - 开源 Baseline 集成指南
- [BASELINE_QUICK_REFERENCE.md](BASELINE_QUICK_REFERENCE.md) - 快速参考
- [ASSET_TODO.md](ASSET_TODO.md) - Assets 准备清单
- [CAPABILITY_BASED_DESIGN.md](CAPABILITY_BASED_DESIGN.md) - 能力设计文档
