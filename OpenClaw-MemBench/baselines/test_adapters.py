#!/usr/bin/env python3
"""Test script for open-source baseline adapters.

Run this to verify that open-source baselines are correctly installed and working.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from baselines import (
    list_baselines,
    check_open_source_availability,
    get_baseline,
)


def test_native_baselines():
    """Test that native baselines work without extra dependencies."""
    print("=" * 60)
    print("Testing Native Baselines")
    print("=" * 60)

    native_baselines = ["sliding-window", "keyword", "recursive-summary", "hierarchical"]

    for name in native_baselines:
        try:
            baseline = get_baseline(name, budget_chars=1000)
            result = baseline.compress(
                workspace_files=[("test.md", "This is a test with constraint: must use CSV.")],
                scenario_turns=[{"role": "user", "content": "Year: 2024-2025"}],
                task_prompt="Generate output",
            )
            print(f"[OK] {name}: OK (reduction: {result.reduction_ratio:.1%})")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")


def test_open_source_baselines():
    """Test open-source baseline adapters."""
    print("\n" + "=" * 60)
    print("Testing Open-Source Baselines")
    print("=" * 60)

    availability = check_open_source_availability()

    for name, available in availability.items():
        if not available:
            print(f"[SKIP] {name}: Not installed (skip)")
            print(f"   Install: pip install {name.replace('-', '')}")
            continue

        try:
            baseline = get_baseline(name, budget_chars=1000)
            result = baseline.compress(
                workspace_files=[("test.md", "This is a test with constraint: must use CSV format for output.")],
                scenario_turns=[
                    {"role": "user", "content": "Set year range to 2024-2025"},
                    {"role": "assistant", "content": "OK, year range set"},
                ],
                task_prompt="Generate CSV output with year filter",
            )
            print(f"[OK] {name}: OK")
            print(f"   Raw chars: {result.raw_chars}")
            print(f"   Compressed chars: {result.compressed_chars}")
            print(f"   Reduction: {result.reduction_ratio:.1%}")
            if hasattr(result, 'tokens_used') and result.tokens_used:
                print(f"   Tokens: {result.tokens_used}")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Run all tests."""
    print("OpenClaw-MemBench Baseline Adapter Test")
    print()

    # List available baselines
    print("Available baselines:")
    for name in sorted(list_baselines()):
        print(f"  - {name}")
    print()

    # Test native baselines
    test_native_baselines()

    # Test open-source baselines
    test_open_source_baselines()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

    # Summary
    availability = check_open_source_availability()
    print("\nOpen-source baseline status:")
    for name, available in availability.items():
        status = "[OK] Available" if available else "[MISSING] Not installed"
        print(f"  {name}: {status}")

    if not any(availability.values()):
        print("\n[TIP] Install open-source baselines for more credible comparisons:")
        print("   pip install llmlingua selective-context")


if __name__ == "__main__":
    main()
