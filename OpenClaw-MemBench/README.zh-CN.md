# OpenClaw-MemBench（中文说明）

OpenClaw-MemBench 是一个 capability-first 的 Agent 基准，用于评估 OpenClaw 在长上下文和压缩场景下的记忆能力与鲁棒性。

## 项目目标

项目重点不是"工具会不会用"，而是"记忆是否正确"。

围绕 8 类能力设计 40 个多 episode 场景（每类 5 个）：

1. 近期约束追踪（Recent Constraint Tracking）
2. 版本更新吸收（Version Update）
3. 流程迁移复用（Procedure Transfer）
4. 重复错误避免（Repeated Mistake Prevention）
5. 冲突证据仲裁（Source Conflict Resolution）
6. 记忆操作选择（Memory Operation Selection）
7. 打断后任务恢复（Goal Interruption and Task Resumption）
8. 过时性与适用性判断（Staleness and Applicability Judgment）

## 目录说明

- `tasks/`: 英文任务定义（统一模板）
- `workspace/`: 每个任务的隔离工作区骨架
- `configs/`: 预算配置与能力映射
- `eval/`: 批量入口与结构校验
- `utils/`: 任务解析与评分汇总
- `skills/`: 可注入技能卡（更贴近真实 agent 使用场景）
- `docker/`: Docker 配置文件
- `scripts/`: 构建和运行脚本
- `docs/`: 中英文说明与安装文档
- `assets/`: 外部素材占位目录

## 快速开始

### 1. 环境安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 可选：安装开源基线对比库
pip install -r requirements-baselines.txt
python -m spacy download en_core_web_sm
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

### 3. 快速 Baseline 对比测试（推荐）

```bash
# 快速测试3个主要 baseline（最快）
python scripts/run_all_baselines.py --quick --category 01_Recent_Constraint_Tracking --task-num 1

# 完整对比所有6个 baseline
python scripts/run_all_baselines.py --category 01_Recent_Constraint_Tracking --task-num 1

# 测试某个类别下的所有任务
python scripts/run_all_baselines.py --category 01_Recent_Constraint_Tracking --all-tasks

# 结构校验（不调用 API）
python scripts/run_all_baselines.py --quick --dry-run --category 01_Recent_Constraint_Tracking --task-num 1
```

`run_all_baselines.py` 脚本会自动：
- 运行多种压缩方法（full-context, sliding-window, keyword, lcm-proxy, recursive-summary, hierarchical）
- 收集指标（准确率、token 使用量、压缩率）
- 生成 Markdown 和 JSON 格式的对比表格
- 保存结果到 `outputs/<task_id>/baseline_comparison_*.md`

### 3. 运行基准测试

```bash
# 结构校验（不调用 API）
python eval/run_batch.py --dry-run

# 真实执行（单任务冒烟测试）
python eval/run_batch.py \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 1 \
    --output outputs/smoke_summary.json
```

---

## Docker 部署（推荐）

使用 Docker 容器运行基准测试，确保环境隔离和可复现性。

### 前置要求

- Docker 20.10+ 已安装并运行
- Docker Compose 2.0+（可选，用于 docker-compose 部署）
- 至少 4GB 空闲内存用于容器操作

### Docker 部署选项

#### 方案一：使用脚本构建和运行（推荐）

```bash
# 第一步：构建 Docker 镜像
bash scripts/build_openclaw_image.sh

# 第二步：测试 Docker 环境
bash scripts/test_docker_setup.sh

# 第三步：使用 Docker 运行基准测试
bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 1
```

#### 方案二：手动构建 Docker 镜像

```bash
# 构建独立镜像
docker build -f docker/Dockerfile.standalone -t openclaw-membench:latest .

# 验证安装
docker run --rm openclaw-membench:latest openclaw --version
```

#### 方案三：使用 Docker Compose

```bash
# 启动基准测试环境
docker-compose up -d openclaw-membench

# 在容器内执行命令
docker-compose exec openclaw-membench bash

# 在容器内运行基准测试
openclaw --version
```

### Docker 环境变量配置

在 `.env` 文件中配置以下变量：

```bash
# 运行时配置
OPENCLAW_RUNTIME=openclaw-docker
OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest

# API 配置（必需）
OPENCLAW_BASE_URL=https://api.openai.com/v1
OPENCLAW_API_KEY=your-api-key-here
OPENCLAW_MODEL=gpt-4

# Docker 特定设置
OPENCLAW_DOCKER_NETWORK=host
OPENCLAW_DOCKER_PRESERVE_CONTAINER=false
OPENCLAW_DOCKER_HIDE_PATTERNS=oracle.yaml,grader.py,gt,answers,solution,expected
```

### 使用 Docker 运行基准测试

```bash
# 运行单个类别
bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 5

# 运行类别中所有任务
bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 100

# 运行特定类别并自定义输出
bash scripts/run_openclaw_docker.sh 02_Version_Update 10 outputs/version_results.json
```

### Docker 故障排除

**问题：Docker 守护进程未运行**
```bash
# Linux：启动 Docker 服务
sudo systemctl start docker

# Windows/Mac：打开 Docker Desktop 应用程序
```

**问题：镜像构建失败**
```bash
# 检查 Docker 是否运行
docker info

# 尝试无缓存构建
docker build --no-cache -f docker/Dockerfile.standalone -t openclaw-membench:latest .
```

**问题：容器无法连接 API**
```bash
# 使用主机网络模式（默认）
# 或在 docker-compose.yml 中配置适当的网络
export OPENCLAW_DOCKER_NETWORK=host
```

**问题：运行脚本时权限被拒绝**
```bash
# 使脚本可执行
chmod +x scripts/*.sh
```

---

## 真实场景增强（本次升级）

1. **多轮 scenario 回放**
   - 每个任务 workspace 下支持 scenario.jsonl
   - runner 会在最终执行前回放历史回合，支持 interruption / update / conflict 结构

2. **技能系统注入**
   - 支持从 skills/registry.yaml 读取 skill cards
   - 能力可映射默认 skills，任务也可手工覆写

3. **超长上下文构建**
   - 提供 scripts/build_long_context.py，自动为 40 个任务生成长历史与压缩检查点
   - 生成 oracle.yaml（white-box capability targets）

4. **多压缩方法对比**
   - `OPENCLAW_COMPRESSION_METHOD` 支持 full、lcm-proxy、sliding-window、keyword、episode
   - `eval/compare_profiles.py` 可一次比较多方法并输出 retention / cost / token 差异

5. **压缩可追踪日志**
   - usage.json 新增 raw_context_chars、compressed_context_chars、context_reduction_ratio
   - 记录 scenario_turns 与 compression_events

## 可用基线方法

### 原生基线（无需额外依赖）

| 基线 | 描述 | 适用场景 |
|------|------|----------|
| `sliding-window` | 简单最近截断 | 快速基线 |
| `keyword` | 基于关键词的过滤 | 约束密集型任务 |
| `recursive-summary` | 片段摘要 | 多片段场景 |
| `hierarchical` | 多级记忆 | 混合最近性场景 |
| `mem0` | 原生 Mem0 模拟 | 无需配置的快速测试 |
| `vector-retrieval` | TF-IDF 检索 | 语义相似性 |

### 开源基线（真实实现）

| 基线 | 来源 | 论文 | 优势 |
|------|------|------|------|
| `llmlingua` | [Microsoft](https://github.com/microsoft/LLMLingua) | EMNLP'23, ACL'24 | SOTA 提示压缩（最高 20x） |
| `selective-context` | [liyucheng](https://github.com/liyucheng09/Selective_Context) | EMNLP'23 | 信息论过滤 |
| `mem0-lib` | [Mem0](https://github.com/mem0ai/mem0) | arXiv'25 | 真实记忆系统（41K+ stars） |

安装开源基线：
```bash
pip install llmlingua selective-context
# 可选：安装 Mem0
pip install mem0ai chromadb
export OPENAI_API_KEY="your-key"
```

## 任务格式

每个任务 Markdown 包含：

- Prompt（提示词）
- Expected Behavior（期望行为）
- Grading Criteria（评分标准）
- Automated Checks（Python 自动化检查）
- Workspace Path（工作区路径）
- Skills / Env / Warmup（技能/环境/预热）

参考模板：[tasks/task_template.md](tasks/task_template.md)

## 真实 OpenClaw 隔离执行（对齐 WildClawBench 风格）

新增 `openclaw-docker` runtime：在容器内真实启动 OpenClaw gateway + agent 执行任务。

1. 构建镜像（基于 OpenClaw 可运行基础镜像）：

```bash
bash scripts/build_openclaw_image.sh
```

2. `.env` 中启用：

```bash
OPENCLAW_RUNTIME=openclaw-docker
OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest
```

3. 运行能力级 smoke test：

```bash
bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 1 outputs/openclaw_smoke.json
```

### 防泄露设计

- 执行前先复制 workspace 到沙箱目录
- 按 `OPENCLAW_DOCKER_HIDE_PATTERNS` 删除 oracle / gt / solution 等敏感文件
- 评分在执行后进行，且与 agent 执行过程隔离

### 能力单测约束

运行器会校验 `category -> capability` 一一对应。
不匹配任务会被标记为 `task_schema_error`，确保每个任务突出一种主能力。

## 上下文压缩配置

压缩配置文件位于 [configs/budgets.yaml](configs/budgets.yaml)：

- `full-context` - 无压缩
- `lcm-medium-budget` - 中度压缩
- `lcm-low-budget` - 高度压缩
- `lcm-stress-budget` - 极限压缩

这些可以连接到你的 OpenClaw 部署中的 lossless-claw/LCM 运行时策略。

## 素材状态

基准测试包含多模态素材以进行真实评估：

| 素材类型 | 数量 | 状态 |
|---------|------|------|
| 冲突数据 | 5 组 | 可用 |
| 邮件/日历 | 25 封邮件，4 个 ICS | 可用 |
| 图片 | ~20 张 | 可用 |
| PDF | 24 个文件 | 可用 |
| 视频 | 6 个 | 可用 |
| 日志 | 10 个 | 可用 |
| 截图 | 8 张 | 可用 |
| 表格 | 5 个文件 | 可用 |

## 文档

- [INSTALL_EN.md](docs/INSTALL_EN.md) / [INSTALL_ZH.md](docs/INSTALL_ZH.md) - 安装指南
- [BASELINES.md](docs/BASELINES.md) - 基线详细文档
- [CAPABILITY_BASED_DESIGN.md](docs/CAPABILITY_BASED_DESIGN.md) - 能力设计

## 当前进度

- 任务场景：40 个（英文）
- workspace 骨架：40 套
- 原生基线：6 个
- 开源基线适配器：3 个（LLMLingua、Selective Context、Mem0）
- 双语文档：已完成
- 额外图片/视频素材：未导入，已记录在 docs/ASSET_TODO.md
- Docker 支持：完整的容器化执行

## Docker 架构

基准测试支持多种 Docker 部署模式：

### 1. 独立模式（`docker/Dockerfile.standalone`）

自包含镜像，包括：
- Ubuntu 22.04 基础镜像
- Node.js 20.x 和 OpenClaw CLI
- Python 3 及所需依赖
- 无外部基础镜像依赖

### 2. 执行器模式（`docker/Dockerfile.executor`）

完整项目镜像用于开发：
- 扩展独立镜像
- 包含完整项目代码
- 可直接运行基准测试

### 3. Docker Compose（`docker-compose.yml`）

编排部署，包括：
- 开发用的卷挂载
- API 调用的主机网络访问
- 健康检查和资源限制

## 基准测试执行流程

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   任务解析器    │────▶│   OpenClaw Agent │────▶│     评分系统    │
│  (加载 .md)     │     │   (容器内运行)   │     │   (自动化)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  加载场景       │     │  在沙箱中运行    │     │  对输出评分     │
│  工作区         │     │  使用技能        │     │  对比 oracle    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## 致谢

设计参考：

- OpenClaw
- WildClawBench
- lossless-claw / LCM
