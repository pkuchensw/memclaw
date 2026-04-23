# 开源 Baseline 集成指南

## 当前实现的性质

目前 `baselines/` 目录下的实现都是**基于论文思想自己开发的简化版本**：

| Baseline | 当前实现 | 是否使用开源代码 |
|---------|---------|----------------|
| Sliding Window | 自己实现 | ❌ |
| Keyword Extraction | 自己实现 | ❌ |
| Recursive Summary | 自己实现 | ❌ |
| Hierarchical Memory | 自己实现 | ❌ |
| Mem0 | 自己实现（模拟思想） | ❌ |
| Vector Retrieval | 自己实现（TF-IDF模拟） | ❌ |

**问题**：这些简化版本虽然能工作，但可能与原论文实现有差距，缺乏真实系统的复杂性和优化。

---

## 可用的开源实现

### 1. **LLMLingua**（微软）⭐ 强烈推荐

**GitHub**: [microsoft/LLMLingua](https://github.com/microsoft/LLMLingua)
**Paper**: EMNLP'23, ACL'24

**特点**:
- 使用小型 LM（GPT-2, LLaMA-7B, Phi-2）压缩提示
- 可达 **20x 压缩率**
- **LLMLingua-2**: 3-6x 速度提升
- 内置 LangChain/LlamaIndex 支持
- 减少 50-80% token 成本

**安装**:
```bash
pip install llmlingua
```

**使用示例**:
```python
from llmlingua import PromptCompressor

llm_lingua = PromptCompressor("microsoft/phi-2")
compressed = llm_lingua.compress_prompt(
    prompt=long_prompt,
    instruction="",
    question="",
    target_token=200
)
```

**集成难度**: ⭐⭐ 容易
**推荐度**: ⭐⭐⭐⭐⭐ 必须集成

---

### 2. **Selective Context**（liyucheng）

**GitHub**: [liyucheng09/Selective_Context](https://github.com/liyucheng09/Selective_Context)
**Paper**: EMNLP'23
**PyPI**: `selective-context`

**特点**:
- 基于**自信息**的内容过滤
- 支持句子/短语/token 三级压缩
- 2x 上下文扩展，GPU 成本减少 65%
- 被 Microsoft LLMLingua 和 LlamaIndex 采用

**安装**:
```bash
pip install selective-context
python -m spacy download en_core_web_sm
```

**使用示例**:
```python
from selective_context import SelectiveContext

sc = SelectiveContext(model_type='gpt2', lang='en')
compressed, reduced = sc(long_text, reduce_ratio=0.5)
```

**集成难度**: ⭐⭐ 容易
**推荐度**: ⭐⭐⭐⭐ 重要 baseline

---

### 3. **Mem0**（官方）⭐ 强烈推荐

**GitHub**: [mem0ai/mem0](https://github.com/mem0ai/mem0)
**Stars**: 41,000+
**Paper**: arXiv:2504.19413

**特点**:
- 混合存储架构（Vector + KV Store + Graph）
- 支持用户/会话/代理三级记忆
- 智能去重和一致性维护
- 多模态支持
- AWS Agent SDK 官方记忆提供商

**安装**:
```bash
pip install mem0ai
```

**使用示例**:
```python
from mem0 import Memory

m = Memory()

# 添加记忆
m.add("我在学习机器学习", user_id="alice")

# 搜索
results = m.search("Alice 在学什么？", user_id="alice")
```

**集成难度**: ⭐⭐⭐ 中等（需要配置存储后端）
**推荐度**: ⭐⭐⭐⭐⭐ 必须集成

---

### 4. **Letta (原 MemGPT)**

**GitHub**: [letta-ai/letta](https://github.com/letta-ai/letta)
**Paper**: "MemGPT: Towards LLMs as Operating Systems"
**License**: Apache 2.0

**特点**:
- 两级内存架构（Core/Archival）
- 自编辑内存能力
- 操作系统式内存分页
- 完整的 agent runtime

**安装**:
```bash
pip install letta
```

**集成难度**: ⭐⭐⭐⭐ 较难（完整 runtime，不是简单库）
**推荐度**: ⭐⭐⭐ 可选（可能过于复杂）

---

### 5. **LangChain Contextual Compression**

**文档**: [LangChain Contextual Compression](https://api.python.langchain.com/en/latest/_modules/langchain/retrievers/contextual_compression.html)

**特点**:
- 官方内置支持
- `LLMChainExtractor` - LLM 提取相关内容
- `LLMLinguaCompressor` - 集成 LLMLingua
- `EmbeddingsFilter` - 向量过滤

**使用示例**:
```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(llm)
retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)
```

**集成难度**: ⭐⭐ 容易
**推荐度**: ⭐⭐⭐ 可选

---

### 6. **ACON**（微软）⭐ 重要

**GitHub**: [microsoft/acon](https://github.com/microsoft/acon)
**Paper**: arXiv:2510.00615

**特点**:
- 针对长程 agent 优化的上下文压缩
- 对比任务反馈优化压缩提示
- Token 减少 26-54%，性能保持
- 支持蒸馏到小模型

**对比的 baselines**（paper 中使用的）:
- **No Compression**: 无压缩（上限）
- **FIFO**: 保留最近 k 个交互
- **Retrieval**: 基于相似度检索历史
- **LLMLingua**: 基于 encoder 的提取式压缩
- **Prompting**: 简单压缩指令

**集成难度**: ⭐⭐⭐ 中等
**推荐度**: ⭐⭐⭐⭐ 重要（这是直接相关工作）

---

## 推荐的集成优先级

### Phase 1: 必须集成（核心对比）

1. **LLMLingua**
   - 最主流的开源提示压缩工具
   - 性能优秀，文档完善
   - 直接对比价值高

2. **Mem0**
   - 41K+ stars，社区标准
   - 真实系统级别实现
   - 混合存储架构有代表性

3. **Selective Context**
   - 被 LLMLingua 采用
   - 自信息方法有理论依据
   - 轻量级易集成

### Phase 2: 重要补充

4. **ACON**
   - 直接相关工作（Agent 上下文压缩）
   - 学习到的压缩策略
   - 已有 baseline 实现可用

### Phase 3: 可选增强

5. **LangChain Contextual Compression**
   - 生态集成好
   - 但可能与其他方法重叠

6. **Letta/MemGPT**
   - 完整 runtime 过于复杂
   - 除非专门对比内存架构

---

## 集成架构设计

### Adapter 模式

为每个开源实现创建 Adapter，统一接口：

```python
# baselines/adapters/llmlingua_adapter.py
from llmlingua import PromptCompressor
from baselines.base import BaseBaseline, BaselineResult

class LLMLinguaAdapter(BaseBaseline):
    def __init__(self, model_name="microsoft/phi-2", **kwargs):
        super().__init__(**kwargs)
        self.compressor = PromptCompressor(model_name)
    
    def compress(self, workspace_files, scenario_turns, task_prompt=""):
        # 合并所有内容
        full_context = self._merge_context(workspace_files, scenario_turns)
        
        # 使用 LLMLingua 压缩
        result = self.compressor.compress_prompt(
            prompt=full_context,
            instruction="",
            question=task_prompt,
            target_token=self.budget_tokens,
        )
        
        return BaselineResult(
            context=result["compressed_prompt"],
            raw_chars=len(full_context),
            compressed_chars=len(result["compressed_prompt"]),
            reduction_ratio=result["compression_ratio"],
            method="llmlingua",
        )
```

### 依赖管理

在 `requirements-baselines.txt` 中分开管理：

```txt
# Core baselines (always installed)
# (current simple baselines have no extra deps)

# Open-source baselines (optional)
llmlingua>=0.2.0
selective-context>=0.1.0
mem0ai>=0.1.0

# Note: These require additional setup
# - llmlingua: needs GPU for best performance
# - mem0ai: needs vector DB (chroma/qdrant)
```

### 动态导入

```python
def get_baseline(name, **kwargs):
    """Get baseline with fallback to open-source adapters."""
    
    # Try open-source adapters first
    if name == "llmlingua":
        try:
            from baselines.adapters.llmlingua_adapter import LLMLinguaAdapter
            return LLMLinguaAdapter(**kwargs)
        except ImportError:
            raise ImportError(
                "LLMLingua not installed. Run: pip install llmlingua"
            )
    
    # Fall back to native implementations
    return BASELINE_REGISTRY[name](**kwargs)
```

---

## 具体集成步骤

### Step 1: 安装依赖

```bash
# 基础依赖
pip install llmlingua selective-context

# Mem0 需要额外依赖
pip install mem0ai qdrant-client  # 或 chromadb
```

### Step 2: 创建 Adapter 目录

```
baselines/
├── adapters/
│   ├── __init__.py
│   ├── llmlingua_adapter.py
│   ├── selective_context_adapter.py
│   ├── mem0_adapter.py
│   └── acon_adapter.py
├── native/  # 当前的简化实现
│   ├── sliding_window.py
│   ├── keyword_extract.py
│   └── ...
└── base.py
```

### Step 3: 实现适配器

每个 adapter 包装开源库，实现统一的 `compress()` 接口。

### Step 4: 更新注册表

```python
# baselines/__init__.py
BASELINE_REGISTRY = {
    # Native implementations
    "sliding-window": SlidingWindowBaseline,
    "keyword": KeywordExtractBaseline,
    ...
    # Open-source adapters
    "llmlingua": LLMLinguaAdapter,
    "selective-context": SelectiveContextAdapter,
    "mem0-lib": Mem0Adapter,
    "acon": ACONAdapter,
}
```

---

## 对比实验设计

### 实验 1: 压缩率 vs 任务性能

```bash
# 运行所有 baselines（包括开源）
python eval/run_all_baselines.py \
    --baselines sliding-window,keyword,llmlingua,selective-context,mem0-lib \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 10 \
    --execute-tasks
```

### 实验 2: 不同预算下的表现

```bash
for budget in 4000 8000 12000 16000; do
    python eval/run_baselines.py \
        --budget $budget \
        --baselines llmlingua,selective-context,mem0-lib \
        --output outputs/budget_sensitivity/$budget.json
done
```

### 实验 3: 能力特异性分析

```bash
for category in 01_Recent_Constraint_Tracking 02_Version_Update 03_Procedure_Transfer; do
    python eval/run_all_baselines.py \
        --category $category \
        --baselines all \
        --execute-tasks
done
```

---

## 预期结果

### LLMLingua 优势场景
- 长文档处理
- 需要保持语义连贯性
- 有 GPU 资源

### Selective Context 优势场景
- 快速压缩需求
- 自信息方法有效的场景
- 资源受限环境

### Mem0 优势场景
- 长期对话历史
- 需要跨会话记忆
- 多用户场景

### ACON 优势场景
- 长程 agent 任务
- 需要学习压缩策略
- 与我们的工作直接对比

---

## 风险和注意事项

1. **依赖复杂性**
   - 开源库可能引入大量依赖
   - 建议用可选依赖管理

2. **性能问题**
   - LLMLingua 需要 GPU 才能高效运行
   - Mem0 需要向量数据库

3. **API 变化**
   - 开源库 API 可能变化
   - Adapter 层需要维护

4. **公平性**
   - 开源实现可能有额外优化
   - 需要确保对比条件一致

---

## 总结

**现状**: 当前实现是简化的，基于论文思想自己开发的

**改进方向**:
1. 集成 **LLMLingua**（微软）- 最重要的 baseline
2. 集成 **Mem0**（官方）- 社区标准
3. 集成 **Selective Context** - 轻量级有效
4. 集成 **ACON**（微软）- 直接相关工作

**价值**:
- 与真正的开源实现对比更有说服力
- 减少"自己实现可能有 bias"的质疑
- 展示与 SOTA 的差距

**工作量**: 预计 2-3 天完成核心集成（LLMLingua + Selective Context）
