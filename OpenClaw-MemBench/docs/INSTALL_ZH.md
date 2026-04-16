# 环境安装与运行前检查（中文）

本文档用于 OpenClaw-MemBench 的环境安装与“运行前人工检查”。

## 1. 基础要求

- 操作系统：Linux（推荐）
- Python：3.10 及以上
- 可选：Docker/OpenClaw（用于真实端到端运行）

## 2. 创建 Python 环境

### 方案 A：venv

```bash
python3 -m venv .venv
source .venv/bin/activate
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

## 3. 环境变量配置

```bash
cp .env.example .env
```

按你的 OpenClaw 实际部署修改 .env。

如果你希望“只改 API 就能跑”，至少配置以下字段：

- OPENCLAW_BASE_URL
- OPENCLAW_CHAT_COMPLETIONS_PATH
- OPENCLAW_MODEL
- OPENCLAW_API_KEY（如需要鉴权）

示例：

```env
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_CHAT_COMPLETIONS_PATH=/v1/chat/completions
OPENCLAW_MODEL=anthropic/claude-sonnet-4-5
OPENCLAW_API_KEY=
```

## 4. 运行前必查清单（建议你先看）

1. 任务总览是否符合预期：tasks/TASK_INDEX.md
2. 是否需要补素材：docs/ASSET_TODO.md
3. 每个 task 是否有独立 workspace：workspace/*/task_*
4. 压缩预算配置是否合理：configs/budgets.yaml
5. 能力-记忆对象映射是否一致：configs/capabilities.yaml

## 5. 可选“仅结构”校验（不跑真实 agent）

```bash
python eval/run_batch.py --dry-run
```

说明：该命令只校验任务文件结构，不会进行真实 OpenClaw 执行。

## 6. API 真实执行（最小改动）

现在 eval/run_batch.py 已接入 API 执行器。

先做 1 个任务冒烟：

```bash
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --output outputs/smoke_summary.json
```

跑完整个能力类：

```bash
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --output outputs/c1_summary.json
```

跑全量：

```bash
python eval/run_batch.py --output outputs/all_summary.json
```

每次运行会在 outputs/<category>/<task_id>/<timestamp>/ 下写入：

- request.json
- response.json
- transcript.json
- assistant.txt

## 7. Docker 是否必须

- 只做 API 测试：不是必须。
- 追求可复现和隔离的 benchmark：建议必须使用 Docker/OpenClaw 隔离环境。

### 构建隔离执行镜像

```bash
bash scripts/build_executor_image.sh
```

### 启用 docker runtime

在 .env 中设置：

```env
OPENCLAW_RUNTIME=docker
DOCKER_IMAGE=openclaw-membench-executor:latest
DOCKER_NETWORK=host
```

然后执行（示例）：

```bash
python eval/run_batch.py --runtime docker --category 01_Recent_Constraint_Tracking --max-tasks 1 --output outputs/docker_smoke_summary.json
```

每个任务的输出目录会额外产生日志：

- docker_stdout.log
- docker_stderr.log

## 8. 额外图片/视频等素材

已统一登记在 docs/ASSET_TODO.md，后续可由你手工补充。
