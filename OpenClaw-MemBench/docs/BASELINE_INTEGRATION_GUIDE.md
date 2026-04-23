# Baseline Integration Guide

## Overview

This guide explains how to use **real open-source baseline implementations** alongside the native simplified baselines.

## Two Types of Baselines

### 1. Native Baselines (Simplified)

Implemented from scratch based on paper concepts:

| Baseline | Description | Good For |
|----------|-------------|----------|
| `sliding-window` | Simple recency truncation | Quick baseline |
| `keyword` | Keyword-based filtering | Constraint-heavy tasks |
| `recursive-summary` | Episode summarization | Multi-episode scenarios |
| `hierarchical` | Multi-tier memory | Mixed recency scenarios |
| `mem0` | Native Mem0 simulation | Quick testing without setup |
| `vector-retrieval` | TF-IDF retrieval | Semantic similarity |

**Pros**: No extra dependencies, fast, easy to understand  
**Cons**: May not match published paper performance

### 2. Open-Source Baselines (Recommended)

Wrappers around official open-source libraries:

| Baseline | Source | Paper | Why Use |
|----------|--------|-------|---------|
| `llmlingua` | [Microsoft](https://github.com/microsoft/LLMLingua) | EMNLP'23, ACL'24 | SOTA prompt compression |
| `selective-context` | [liyucheng](https://github.com/liyucheng09/Selective_Context) | EMNLP'23 | Information-theoretic |
| `mem0-lib` | [Mem0](https://github.com/mem0ai/mem0) | arXiv'25 | Real memory system |

**Pros**: Real implementation, reproducible, SOTA performance  
**Cons**: Additional dependencies, may need GPU/API keys

---

## Quick Start

### Step 1: Check Available Baselines

```bash
python -c "
from baselines import list_baselines, check_open_source_availability

print('Available baselines:')
for name in sorted(list_baselines()):
    print(f'  - {name}')

print('\nOpen-source availability:')
for name, available in check_open_source_availability().items():
    status = '✅' if available else '❌ Not installed'
    print(f'  {name}: {status}')
"
```

### Step 2: Install Open-Source Dependencies

```bash
# Install all open-source baselines
pip install llmlingua selective-context

# For Mem0, also install a vector database
pip install mem0ai chromadb

# Download required models
python -m spacy download en_core_web_sm
```

### Step 3: Verify Installation

```bash
python -c "
from baselines import check_open_source_availability
print(check_open_source_availability())
"
```

Expected output:
```python
{
    'llmlingua': True,
    'selective-context': True,
    'mem0-lib': True  # or False if not installed
}
```

---

## Usage Examples

### Using LLMLingua

```python
from baselines import get_baseline

# Initialize LLMLingua with Phi-2 compressor
baseline = get_baseline(
    "llmlingua",
    budget_chars=12000,
    model_name="microsoft/phi-2",  # or "gpt2" for faster
    rate=0.5,  # Target 50% compression
)

# Run compression
result = baseline.compress(
    workspace_files=[("notes.md", "Important: must use CSV format...")],
    scenario_turns=[{"role": "user", "content": "Set year to 2024"}],
    task_prompt="Generate output",
)

print(f"Reduction: {result.reduction_ratio:.2%}")
print(f"Original tokens: {result.tokens_used['original_tokens']}")
print(f"Compressed tokens: {result.tokens_used['compressed_tokens']}")
```

### Using Selective Context

```python
from baselines import get_baseline

baseline = get_baseline(
    "selective-context",
    budget_chars=12000,
    model_type="gpt2",
    granularity="sentence",  # or "phrase", "token"
)

result = baseline.compress(
    workspace_files=[...],
    scenario_turns=[...],
    task_prompt="...",
)
```

### Using Mem0 (Real Library)

```python
from baselines import get_baseline

# Note: Requires OPENAI_API_KEY environment variable
baseline = get_baseline(
    "mem0-lib",
    budget_chars=12000,
    vector_store="chroma",  # or "qdrant"
    user_id="test_user",
)

result = baseline.compress(...)
print(f"Memories extracted: {result.metadata['memories_extracted']}")
print(f"Memories retrieved: {result.metadata['memories_retrieved']}")
```

---

## Running Comparisons

### Compare Native vs Open-Source

```bash
python eval/run_baselines.py \
    --baselines keyword,llmlingua,selective-context \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 5
```

### Full Comparison with Task Execution

```bash
python eval/run_all_baselines.py \
    --baselines all \
    --category 01_Recent_Constraint_Tracking \
    --max-tasks 10 \
    --execute-tasks
```

### Budget Sensitivity Analysis

```bash
for budget in 4000 8000 12000 16000; do
    python eval/run_baselines.py \
        --budget $budget \
        --baselines llmlingua,selective-context \
        --output outputs/budget_${budget}.json
done
```

---

## Troubleshooting

### LLMLingua Issues

**Problem**: `ImportError: LLMLingua not installed`

**Solution**:
```bash
pip install llmlingua torch transformers
```

**Problem**: Slow compression

**Solution**: Use smaller model or GPU
```python
baseline = get_baseline("llmlingua", model_name="gpt2")  # Faster
```

### Selective Context Issues

**Problem**: `OSError: Can't find model 'en_core_web_sm'`

**Solution**:
```bash
python -m spacy download en_core_web_sm
```

### Mem0 Issues

**Problem**: `No API key found`

**Solution**:
```bash
export OPENAI_API_KEY="your-key"
# or
export OPENAI_API_KEY=$(cat ~/.openai_key)
```

**Problem**: `Connection refused` for Qdrant

**Solution**: Use ChromaDB instead (embedded)
```python
baseline = get_baseline("mem0-lib", vector_store="chroma")
```

---

## Performance Comparison

Expected performance characteristics:

| Baseline | Speed | Compression | Quality | Setup |
|----------|-------|-------------|---------|-------|
| `keyword` | ⚡⚡⚡ Fast | ⭐⭐ Medium | ⭐⭐ Good | None |
| `llmlingua` | ⭐ Medium | ⭐⭐⭐⭐⭐ High | ⭐⭐⭐⭐ Very Good | pip install |
| `selective-context` | ⭐⭐ Fast | ⭐⭐⭐⭐ High | ⭐⭐⭐ Good | pip install |
| `mem0-lib` | ⭐ Slow | ⭐⭐⭐ Medium | ⭐⭐⭐⭐⭐ Excellent | API key + DB |

---

## Best Practices

### 1. For Research Papers

**Always use open-source baselines**:
- More credible (real implementations)
- Reproducible by reviewers
- Comparable to other papers

### 2. For Quick Experiments

**Use native baselines**:
- No setup required
- Fast iteration
- Good for prototyping

### 3. For Production

**Use appropriate tool for the job**:
- High compression + quality: `llmlingua`
- Speed: `selective-context`
- Long-term memory: `mem0-lib`

### 4. For Fair Comparison

- Use same budget across all baselines
- Test on same task set
- Report both compression and task performance
- Include error bars / variance

---

## Migration from Native to Open-Source

If you were using native baselines and want to switch:

| Native | Open-Source Equivalent | Notes |
|--------|------------------------|-------|
| `keyword` | `selective-context` | Both use information filtering |
| `mem0` (native) | `mem0-lib` | Real implementation |
| `vector-retrieval` | - | No direct equivalent |

---

## Adding New Open-Source Baselines

To add a new open-source adapter:

1. **Create adapter file**:

```python
# baselines/adapters/my_lib_adapter.py
from baselines.base import BaseBaseline, BaselineResult

class MyLibAdapter(BaseBaseline):
    def __init__(self, budget_chars=12000, **kwargs):
        super().__init__(budget_chars)
        # Import and initialize the library
        from my_lib import Compressor
        self._compressor = Compressor(**kwargs)
    
    def compress(self, workspace_files, scenario_turns, task_prompt=""):
        # Implement compression using the library
        compressed = self._compressor.compress(...)
        return BaselineResult(
            context=compressed,
            raw_chars=original_size,
            compressed_chars=len(compressed),
            reduction_ratio=reduction,
            method="my-lib",
        )
```

2. **Register in `adapters/__init__.py`**

3. **Update `baselines/__init__.py`** to import the adapter

4. **Add to `requirements-baselines.txt`**

---

## References

### LLMLingua
- Paper: [LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models](https://arxiv.org/abs/2310.05736) (EMNLP'23)
- Paper: [LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression](https://arxiv.org/abs/2403.12968) (ACL'24)
- Code: https://github.com/microsoft/LLMLingua

### Selective Context
- Paper: [Compressing Context to Enhance Inference Efficiency of Large Language Models](https://arxiv.org/abs/2309.07338) (EMNLP'23)
- Code: https://github.com/liyucheng09/Selective_Context

### Mem0
- Paper: [Mem0: Building production-ready AI agents with scalable long-term memory](https://arxiv.org/abs/2504.19413)
- Code: https://github.com/mem0ai/mem0

---

## Summary

✅ **Native baselines**: Good for quick testing and prototyping  
✅ **Open-source baselines**: Essential for research and production  
✅ **Recommended setup**: Install `llmlingua` and `selective-context` for core comparisons  
✅ **Migration**: Easy switch from native to open-source using same interface

For credible research, **always include at least one real open-source baseline** (preferably LLMLingua) in your comparisons.
