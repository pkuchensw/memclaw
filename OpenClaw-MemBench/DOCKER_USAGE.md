# OpenClaw-MemBench Docker 使用指南

## 概述

本指南介绍如何在 Docker 环境中运行 OpenClaw-MemBench 测评，解决挂载覆盖等关键问题。

## 目录结构

```
OpenClaw-MemBench/
├── docker/
│   ├── Dockerfile              # 主 Dockerfile（推荐使用）
│   ├── Dockerfile.standalone   # 独立构建版本
│   ├── Dockerfile.windows      # Windows 环境版本
│   └── README.md               # Docker 目录说明
├── docs/
│   └── DOCKER_SETUP.md         # 详细配置文档
└── eval/
    └── run_batch.py            # 主运行脚本
```

## 快速开始（3步运行）

### 第1步：配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置以下变量：
OPENCLAW_BASE_URL=https://api.openai.com/v1
OPENCLAW_API_KEY=your-api-key
OPENCLAW_MODEL=gpt-4
```

### 第2步：构建 Docker 镜像

```bash
# 进入项目目录
cd OpenClaw-MemBench

# 构建镜像
docker build -f docker/Dockerfile -t openclaw-membench:latest .

# 验证构建
 docker run --rm openclaw-membench:latest openclaw --version
```

### 第3步：运行测评

```bash
# Windows (Git Bash)
export MSYS_NO_PATHCONV=1
export OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --runtime openclaw-docker

# Linux/Mac
export OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --runtime openclaw-docker
```

## 核心问题与解决方案

### 问题：挂载覆盖

**现象**：`openclaw: command not found`

**原因**：官方镜像中 `/usr/local/bin/openclaw` 是 `/app/openclaw.mjs` 的符号链接。运行时 workspace 被挂载到 `/app`，导致 openclaw 命令失效。

**解决方案**：将 openclaw 复制到 `/opt/openclaw/`，该位置不会被挂载覆盖。

```dockerfile
RUN mkdir -p /opt/openclaw && \
    cp -r /app/* /opt/openclaw/ && \
    rm -f /usr/local/bin/openclaw && \
    ln -s /opt/openclaw/openclaw.mjs /usr/local/bin/openclaw
```

## 运行参数

### 命令行选项

```bash
python eval/run_batch.py \
  --runtime openclaw-docker \           # 使用 Docker 运行环境
  --category 01_Recent_Constraint_Tracking \  # 任务类别
  --max-tasks 1 \                       # 最大任务数
  --output outputs/summary.json         # 输出文件
```

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `OPENCLAW_DOCKER_IMAGE` | Docker 镜像名 | 是 |
| `OPENCLAW_BASE_URL` | API 基础 URL | 是 |
| `OPENCLAW_API_KEY` | API 密钥 | 是 |
| `OPENCLAW_MODEL` | 模型名称 | 是 |
| `MSYS_NO_PATHCONV` | Windows 禁用路径转换 | Windows必需 |

## 可用任务类别

| 类别 ID | 名称 | 描述 |
|---------|------|------|
| 01_Recent_Constraint_Tracking | Recent Constraint Tracking | 近期约束追踪 |
| 02_Version_Update | Version Update | 版本更新处理 |
| 03_Procedure_Transfer | Procedure Transfer | 程序迁移 |
| 04_Repeated_Mistake_Prevention | Repeated Mistake Prevention | 重复错误预防 |
| 05_Source_Conflict_Resolution | Source Conflict Resolution | 来源冲突解决 |
| 06_Memory_Operation_Selection | Memory Operation Selection | 记忆操作选择 |
| 07_Goal_Interruption_Resumption | Goal Interruption and Task Resumption | 目标中断恢复 |
| 08_Staleness_Applicability_Judgment | Staleness and Applicability Judgment | 时效性判断 |

## 输出结果

运行成功后，结果保存在 `outputs/` 目录：

```
outputs/
├── summary.json                    # 测评结果汇总
└── 01_Recent_Constraint_Tracking/
    └── 01_Recent_Constraint_Tracking_task_01_arxiv_csv_digest/
        └── 20260424_231021/
            └── attempt_1/
                ├── agent.log       # Agent 运行日志
                ├── chat.jsonl      # 完整对话记录（125KB+）
                ├── usage.json      # Token 使用情况
                └── results/        # 任务输出结果
                    ├── arxiv_memory_rl.csv
                    ├── constraint_trace.json
                    ├── result.json
                    └── summary.md
```

## 常见问题

### Q1: Windows 路径转换错误

**症状**：`docker: Error response from daemon: ...`

**解决**：设置 `export MSYS_NO_PATHCONV=1`

### Q2: openclaw 命令未找到

**症状**：`/bin/bash: line 1: openclaw: command not found`

**解决**：确保使用修复后的 Dockerfile 构建镜像：
```bash
docker build -f docker/Dockerfile -t openclaw-membench:latest .
```

### Q3: API 连接超时

**症状**：Timeout 或 Connection Error

**解决**：检查 `.env` 中的 API 配置，确保网络可访问

## 测试验证

```bash
# 1. 验证镜像
docker images openclaw-membench:latest

# 2. 验证 openclaw 可用
docker run --rm openclaw-membench:latest openclaw --version

# 3. 运行 Task1 测试
export OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --runtime openclaw-docker
```

## 完整流程示例

```bash
# 1. 进入目录
cd OpenClaw-MemBench

# 2. 配置环境
cp .env.example .env
# 编辑 .env 设置 API 密钥

# 3. 构建镜像
docker build -f docker/Dockerfile -t openclaw-membench:latest .

# 4. Windows 设置路径转换
export MSYS_NO_PATHCONV=1

# 5. 设置镜像环境变量
export OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest

# 6. 运行 Task1 测试
python eval/run_batch.py \
  --category 01_Recent_Constraint_Tracking \
  --max-tasks 1 \
  --runtime openclaw-docker

# 7. 查看结果
cat outputs/summary.json
```

## 参考文档

- 详细配置文档：[docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md)
- Docker 说明：[docker/README.md](docker/README.md)
