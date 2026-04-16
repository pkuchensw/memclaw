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
- docs/: 中英文说明与安装文档
- assets/: 外部素材占位目录

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
```

## 当前进度

- 任务场景：40 个（英文）
- workspace 骨架：40 套
- 双语文档：已完成
- 额外图片/视频素材：未导入，已记录在 docs/ASSET_TODO.md
