"""Adapters for open-source baseline implementations.

This module provides adapters that wrap real open-source libraries
to provide a unified interface for baseline comparison.
"""

from __future__ import annotations

# Try to import adapters - they may fail if dependencies not installed
adapters_available = {}

try:
    from baselines.adapters.llmlingua_adapter import LLMLinguaAdapter
    adapters_available["llmlingua"] = LLMLinguaAdapter
except ImportError as e:
    adapters_available["llmlingua"] = None

try:
    from baselines.adapters.selective_context_adapter import SelectiveContextAdapter
    adapters_available["selective-context"] = SelectiveContextAdapter
except ImportError:
    adapters_available["selective-context"] = None

try:
    from baselines.adapters.mem0_adapter import Mem0Adapter
    adapters_available["mem0-lib"] = Mem0Adapter
except ImportError:
    adapters_available["mem0-lib"] = None


def get_available_adapters() -> dict[str, type | None]:
    """Get dictionary of available adapters."""
    return adapters_available.copy()


def check_adapter_available(name: str) -> bool:
    """Check if an adapter is available."""
    return adapters_available.get(name) is not None


__all__ = [
    "LLMLinguaAdapter",
    "SelectiveContextAdapter",
    "Mem0Adapter",
    "get_available_adapters",
    "check_adapter_available",
]
