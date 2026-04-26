# Docker 运行缓慢和内存优化指南

## 问题分析

### 1. Docker 运行缓慢的原因

- **镜像体积大**：`openclaw-membench:latest` 镜像约 3.5GB
- **冷启动时间**：每次运行需要启动新容器
- **模型下载**：某些 baseline（如 llmlingua）首次运行需要下载 HuggingFace 模型
- **技能加载**：每次运行都重新加载 skills 和配置文件
- **API 超时**：Moonshot API 90秒超时可能导致重试

### 2. Python 内存占用高的原因

- **Vector Retrieval**：TF-IDF 向量计算缓存
- **Hierarchical Memory**：多层内存结构保留完整内容
- **Docker 进程残留**：容器未正确清理
- **重复加载**：多次运行之间没有共享缓存

## 优化方案

### 方案 1：使用轻量级 Baseline（推荐用于测试）

修改 `test_new_baselines.py`，只使用轻量级方法：

```python
# 只使用轻量级 baseline，避免 vector-retrieval 和 hierarchical
LIGHTWEIGHT_BASELINES = [
    "sliding-window",      # 最简单，无额外计算
    "keyword",             # 仅关键词匹配
    "recursive-summary",   # 纯文本摘要
    "acon",               # 新添加的轻量级方法
    "memgpt",             # 新添加的轻量级方法
]
```

### 方案 2：限制并发和内存

在 `.env` 文件中添加：

```bash
# 限制并发任务数
DEFAULT_PARALLEL=1

# Docker 内存限制
DOCKER_EXTRA_ARGS=--memory=2g --memory-swap=2g

# 禁用重试
OPENCLAW_MAX_RETRIES=0

# 缩短超时
OPENCLAW_REQUEST_TIMEOUT=30
```

### 方案 3：使用 API 模式而非 Docker

API 模式运行更快，内存占用更低：

```bash
# 使用 API 模式
export OPENCLAW_RUNTIME=api
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1
```

### 方案 4：预加载模型（如果使用 LLMLingua）

如果必须使用 llmlingua，预先下载模型：

```python
# 在测试前预加载模型
from transformers import AutoModel, AutoTokenizer
model_name = "microsoft/phi-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
```

### 方案 5：优化向量检索

修改 `baselines/vector_retrieval.py`，添加内存限制：

```python
def __init__(self, budget_chars=12000, chunk_size=500, ...):
    # 限制最大块数，防止内存爆炸
    self.max_chunks = 100  # 新增限制

def _chunk_text(self, text: str, source: str) -> list[dict[str, Any]]:
    chunks = []
    # ... 原有代码 ...
    
    # 限制最大块数
    if len(chunks) > self.max_chunks:
        chunks = chunks[:self.max_chunks]
    
    return chunks
```

### 方案 6：使用单任务脚本

使用简化版测试脚本 `test_task1_docker.py`，避免 run_batch 的开销：

```bash
python test_task1_docker.py --model kimi-k2.5 --timeout 60
```

## 推荐的测试流程

### 快速验证（开发测试）

```bash
# 1. 使用 dry-run 验证配置
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --dry-run --max-tasks 1

# 2. 使用 API 模式快速测试
export OPENCLAW_RUNTIME=api
python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1

# 3. 使用单任务脚本
python test_task1_docker.py --timeout 60
```

### 生产测试（完整评估）

```bash
# 清理旧容器和缓存
docker system prune -f

# 使用 Docker 模式，限制资源
docker run -d --memory=2g --memory-swap=2g openclaw-membench:latest

# 运行测试
export OPENCLAW_RUNTIME=openclaw-docker
export DOCKER_EXTRA_ARGS="--memory=2g"
python eval/run_batch.py --category 01_Recent_Constraint_Tracking
```

## 监控命令

```bash
# 监控 Docker 容器内存使用
docker stats --no-stream

# 监控 Python 进程内存
ps aux | grep python | awk '{print $2, $4, $6, $11}'

# 清理 Docker 缓存
docker system prune -af --volumes
```

## 快速修复清单

- [ ] 删除不需要的 baseline 方法（如 llmlingua）
- [ ] 限制 `vector-retrieval` 的最大块数
- [ ] 使用 API 模式代替 Docker 模式
- [ ] 设置 `OPENCLAW_MAX_RETRIES=0`
- [ ] 设置 `DOCKER_EXTRA_ARGS=--memory=2g`
- [ ] 定期运行 `docker system prune -f`
