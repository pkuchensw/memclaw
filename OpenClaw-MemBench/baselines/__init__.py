"""Baselines for OpenClaw-MemBench.

This module provides various memory management and context compression baselines
for comparison against the capability-based memory compiler.

Two types of baselines are available:
1. Native implementations - Simplified versions based on paper concepts
2. Open-source adapters - Wrappers around real open-source libraries

For research comparisons, prefer open-source adapters when available.
"""

from __future__ import annotations

from baselines.base import BaseBaseline, BaselineResult
from baselines.sliding_window import SlidingWindowBaseline
from baselines.keyword_extract import KeywordExtractBaseline
from baselines.recursive_summary import RecursiveSummarizationBaseline
from baselines.hierarchical_memory import HierarchicalMemoryBaseline

# Optional native baselines (require external dependencies)
try:
    from baselines.mem0_baseline import Mem0Baseline
    MEM0_NATIVE_AVAILABLE = True
except ImportError:
    MEM0_NATIVE_AVAILABLE = False

try:
    from baselines.vector_retrieval import VectorRetrievalBaseline
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

# Open-source library adapters (preferred for research)
# These wrap real implementations like LLMLingua, Selective Context, Mem0, ACon, MemGPT
LLMLINGUA_AVAILABLE = False
SELECTIVE_CONTEXT_AVAILABLE = False
MEM0_LIB_AVAILABLE = False
ACON_AVAILABLE = False
MEMGPT_AVAILABLE = False

try:
    from baselines.adapters.llmlingua_adapter import LLMLinguaAdapter
    LLMLINGUA_AVAILABLE = True
except ImportError:
    pass

try:
    from baselines.adapters.selective_context_adapter import SelectiveContextAdapter
    SELECTIVE_CONTEXT_AVAILABLE = True
except ImportError:
    pass

try:
    from baselines.adapters.mem0_adapter import Mem0Adapter
    MEM0_LIB_AVAILABLE = True
except ImportError:
    pass

try:
    from baselines.adapters.acon_adapter import AConAdapter
    ACON_AVAILABLE = True
except ImportError:
    pass

try:
    from baselines.adapters.memgpt_adapter import MemGPTAdapter
    MEMGPT_AVAILABLE = True
except ImportError:
    pass


BASELINE_REGISTRY: dict[str, type[BaseBaseline]] = {
    # Native implementations
    "sliding-window": SlidingWindowBaseline,
    "keyword": KeywordExtractBaseline,
    "recursive-summary": RecursiveSummarizationBaseline,
    "hierarchical": HierarchicalMemoryBaseline,
}

# Native optional baselines
if MEM0_NATIVE_AVAILABLE:
    BASELINE_REGISTRY["mem0"] = Mem0Baseline

if VECTOR_AVAILABLE:
    BASELINE_REGISTRY["vector-retrieval"] = VectorRetrievalBaseline

# Open-source library adapters (preferred)
if LLMLINGUA_AVAILABLE:
    BASELINE_REGISTRY["llmlingua"] = LLMLinguaAdapter

if SELECTIVE_CONTEXT_AVAILABLE:
    BASELINE_REGISTRY["selective-context"] = SelectiveContextAdapter

if MEM0_LIB_AVAILABLE:
    BASELINE_REGISTRY["mem0-lib"] = Mem0Adapter

if ACON_AVAILABLE:
    BASELINE_REGISTRY["acon"] = AConAdapter

if MEMGPT_AVAILABLE:
    BASELINE_REGISTRY["memgpt"] = MemGPTAdapter


def get_baseline(name: str, **kwargs) -> BaseBaseline:
    """Get a baseline instance by name.

    Args:
        name: Baseline name (e.g., "sliding-window", "llmlingua")
        **kwargs: Additional arguments passed to baseline constructor

    Returns:
        Baseline instance

    Raises:
        ValueError: If baseline name is not recognized
    """
    name = name.lower().replace("_", "-")
    if name not in BASELINE_REGISTRY:
        available = ", ".join(BASELINE_REGISTRY.keys())
        raise ValueError(f"Unknown baseline: {name}. Available: {available}")

    return BASELINE_REGISTRY[name](**kwargs)


def list_baselines() -> list[str]:
    """List all available baseline names."""
    return list(BASELINE_REGISTRY.keys())


def list_open_source_baselines() -> list[str]:
    """List baselines that use real open-source libraries."""
    oss_baselines = []
    if LLMLINGUA_AVAILABLE:
        oss_baselines.append("llmlingua")
    if SELECTIVE_CONTEXT_AVAILABLE:
        oss_baselines.append("selective-context")
    if MEM0_LIB_AVAILABLE:
        oss_baselines.append("mem0-lib")
    if ACON_AVAILABLE:
        oss_baselines.append("acon")
    if MEMGPT_AVAILABLE:
        oss_baselines.append("memgpt")
    return oss_baselines


def check_open_source_availability() -> dict[str, bool]:
    """Check which open-source baselines are available."""
    return {
        "llmlingua": LLMLINGUA_AVAILABLE,
        "selective-context": SELECTIVE_CONTEXT_AVAILABLE,
        "mem0-lib": MEM0_LIB_AVAILABLE,
        "acon": ACON_AVAILABLE,
        "memgpt": MEMGPT_AVAILABLE,
    }


__all__ = [
    "BaseBaseline",
    "BaselineResult",
    "SlidingWindowBaseline",
    "KeywordExtractBaseline",
    "RecursiveSummarizationBaseline",
    "HierarchicalMemoryBaseline",
    "get_baseline",
    "list_baselines",
    "list_open_source_baselines",
    "check_open_source_availability",
    "BASELINE_REGISTRY",
    "MEM0_NATIVE_AVAILABLE",
    "VECTOR_AVAILABLE",
    "LLMLINGUA_AVAILABLE",
    "SELECTIVE_CONTEXT_AVAILABLE",
    "MEM0_LIB_AVAILABLE",
    "ACON_AVAILABLE",
    "MEMGPT_AVAILABLE",
]
