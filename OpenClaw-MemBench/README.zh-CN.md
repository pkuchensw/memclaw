# OpenClaw-MemBench（中文说明）

OpenClaw-MemBench 是一个 capability-first 的 Agent 基准，用于评估 OpenClaw 在长上下文和压缩场景下的记忆能力与鲁棒性。

## 项目目标

项目重点不是“工具会不会用”，而是“记忆是否正确”。

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

- tasks/: 英文任务定义（统一模板）
- workspace/: 每个任务的隔离工作区骨架
- configs/: 预算配置与能力映射
- eval/: 批量入口与结构校验
- utils/: 任务解析与评分汇总
- skills/: 可注入技能卡（更贴近真实 agent 使用场景）
- docs/: 中英文说明与安装文档
- assets/: 外部素材占位目录

## 真实场景增强（本次升级）

1. 多轮 scenario 回放
- 每个任务 workspace 下支持 scenario.jsonl
- runner 会在最终执行前回放历史回合，支持 interruption / update / conflict 结构

2. 技能系统注入
- 支持从 skills/registry.yaml 读取 skill cards
- 能力可映射默认 skills，任务也可手工覆写

3. 超长上下文构建
- 提供 scripts/build_long_context.py，自动为 40 个任务生成长历史与压缩检查点
- 生成 oracle.yaml（white-box capability targets）

4. 多压缩方法对比
- `OPENCLAW_COMPRESSION_METHOD` 支持 full、lcm-proxy、sliding-window、keyword、episode
- `eval/compare_profiles.py` 可一次比较多方法并输出 retention / cost / token 差异

5. 压缩可追踪日志
- usage.json 新增 raw_context_chars、compressed_context_chars、context_reduction_ratio
- 记录 scenario_turns 与 compression_events

## 你当前可以先检查什么（不运行）

1. 检查任务总览：tasks/TASK_INDEX.md
2. 抽查具体任务：tasks/*/*.md
3. 检查环境安装文档：docs/INSTALL_ZH.md
4. 检查素材缺口清单：docs/ASSET_TODO.md
5. 检查项目状态：docs/PROJECT_STATUS.md

## 运行前约定

按照你的要求：运行 benchmark 之前先由你检查。

目前我仅完成了文件构建与文档生成，没有执行 benchmark 正式运行。

## 可选结构校验命令（仅在你确认后执行）

```bash
python eval/run_batch.py --dry-run
python eval/run_batch.py --dry-run --category 01_Recent_Constraint_Tracking
python scripts/build_long_context.py
python eval/compare_profiles.py --runtime api --max-tasks 40 --methods full,lcm-proxy,sliding-window,keyword,episode
python eval/validate_lcm.py --summary outputs/summary.json
```

## 真实 OpenClaw 隔离执行（对齐 WildClawBench 风格）

新增 `openclaw-docker` runtime：在容器内真实启动 OpenClaw gateway + agent 执行任务。

1. 构建镜像（基于 OpenClaw 可运行基础镜像）：

```bash
bash scripts/build_openclaw_image.sh
```

2. `.env` 中启用：

- `OPENCLAW_RUNTIME=openclaw-docker`
- `OPENCLAW_DOCKER_IMAGE=openclaw-membench-openclaw:latest`

3. 运行能力级 smoke test：

```bash
bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 1 outputs/openclaw_smoke.json
```

### 防泄露设计

- 执行前先复制 workspace 到沙箱目录。
- 按 `OPENCLAW_DOCKER_HIDE_PATTERNS` 删除 oracle / gt / solution 等敏感文件。
- 评分在执行后进行，且与 agent 执行过程隔离。

### 能力单测约束

运行器会校验 `category -> capability` 一一对应。
不匹配任务会被标记为 `task_schema_error`，确保每个任务突出一种主能力。

## 当前进度

- 任务场景：40 个（英文）
- workspace 骨架：40 套
- 双语文档：已完成
- 额外图片/视频素材：未导入，已记录在 docs/ASSET_TODO.md
