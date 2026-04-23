#!/usr/bin/env python3
"""Baseline comparison runner for OpenClaw-MemBench.

This script runs all configured baselines on the benchmark tasks
and produces comparison metrics.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from baselines import get_baseline, list_baselines, BaselineResult
from utils.task_parser import parse_task_md
from utils.grading import run_grading_from_task_md
from utils.scenario_replayer import load_scenario_turns

ROOT_DIR = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT_DIR / "tasks"
OUTPUT_DIR = ROOT_DIR / "outputs" / "baseline_comparison"


def collect_tasks(category: str | None = None) -> list[Path]:
    """Collect all task files."""
    if category:
        cat_path = TASKS_DIR / category
        if cat_path.exists():
            return sorted(cat_path.glob("*.md"))
        return []

    files: list[Path] = []
    for d in sorted(TASKS_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("_"):
            files.extend(sorted(d.glob("*.md")))
    return files


def run_baseline_on_task(
    baseline_name: str,
    task: dict,
    budget_chars: int = 12000,
) -> dict[str, Any]:
    """Run a single baseline on a task.

    Returns results including:
    - Compression statistics
    - Grading scores (if available)
    - Timing information
    """
    result = {
        "baseline": baseline_name,
        "task_id": task["task_id"],
        "category": task["category"],
        "timestamp": datetime.now().isoformat(),
        "status": "ok",
        "error": None,
    }

    try:
        # Initialize baseline
        baseline = get_baseline(baseline_name, budget_chars=budget_chars)

        # Load workspace files and scenario
        workspace_path = task.get("workspace_path", "")
        scenario_path = task.get("scenario_path", "")
        scenario_turns = load_scenario_turns(scenario_path)

        # Load workspace files
        workspace_files = _load_workspace_files(workspace_path)

        # Get task prompt
        task_prompt = task.get("prompt", "")

        # Run compression
        start_time = datetime.now()
        compression_result = baseline.compress(
            workspace_files=workspace_files,
            scenario_turns=scenario_turns,
            task_prompt=task_prompt,
        )
        end_time = datetime.now()

        result["compression"] = compression_result.to_dict()
        result["timing"] = {
            "compression_seconds": (end_time - start_time).total_seconds(),
        }

        # Save compressed context for inspection
        output_subdir = OUTPUT_DIR / task["task_id"] / baseline_name
        output_subdir.mkdir(parents=True, exist_ok=True)

        context_file = output_subdir / "compressed_context.txt"
        context_file.write_text(compression_result.context, encoding="utf-8")

        result_file = output_subdir / "result.json"
        result_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        result["output_dir"] = str(output_subdir)

    except Exception as e:
        result["status"] = "error"
        result["error"] = f"{e}\n{traceback.format_exc()}"

    return result


def _load_workspace_files(workspace_path: str) -> list[tuple[str, str]]:
    """Load text files from workspace."""
    ws = Path(workspace_path)
    files: list[tuple[str, str]] = []

    if not ws.exists():
        return files

    text_extensions = {
        ".txt", ".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".log",
        ".py", ".js", ".ts", ".html", ".css", ".sh", ".xml", ".toml",
    }

    for subdir in ["episodes", "evidence"]:
        folder = ws / subdir
        if not folder.exists():
            continue
        for filepath in sorted(folder.rglob("*")):
            if not filepath.is_file():
                continue
            if filepath.suffix.lower() not in text_extensions:
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                rel_path = str(filepath.relative_to(ws))
                files.append((rel_path, content))
            except Exception:
                continue

    return files


def run_comparison(
    baselines: list[str],
    category: str | None = None,
    max_tasks: int = 0,
    budget_chars: int = 12000,
) -> dict[str, Any]:
    """Run comparison of multiple baselines.

    Args:
        baselines: List of baseline names to compare
        category: Optional category to filter tasks
        max_tasks: Maximum tasks to run (0 = all)
        budget_chars: Character budget for compression

    Returns:
        Comparison results with statistics
    """
    print(f"Running baseline comparison: {', '.join(baselines)}")
    print(f"Budget: {budget_chars} chars")
    print("-" * 60)

    # Collect tasks
    task_files = collect_tasks(category)
    if max_tasks > 0:
        task_files = task_files[:max_tasks]

    print(f"Tasks: {len(task_files)}")

    # Run all baselines on all tasks
    all_results: list[dict] = []

    for task_file in task_files:
        print(f"\nProcessing: {task_file.name}")

        try:
            task = parse_task_md(task_file)
        except Exception as e:
            print(f"  Error parsing task: {e}")
            continue

        for baseline_name in baselines:
            print(f"  Running {baseline_name}...", end=" ")

            result = run_baseline_on_task(
                baseline_name=baseline_name,
                task=task,
                budget_chars=budget_chars,
            )

            all_results.append(result)

            if result["status"] == "ok":
                comp = result.get("compression", {})
                reduction = comp.get("reduction_ratio", 0) * 100
                print(f"OK (reduction: {reduction:.1f}%)")
            else:
                print(f"ERROR: {result['error'][:50]}...")

    # Aggregate statistics
    summary = _aggregate_results(all_results, baselines)

    return {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "budget_chars": budget_chars,
            "baselines": baselines,
            "num_tasks": len(task_files),
            "category": category,
        },
        "summary": summary,
        "results": all_results,
    }


def _aggregate_results(
    results: list[dict],
    baselines: list[str],
) -> dict[str, dict]:
    """Aggregate results by baseline."""
    summary: dict[str, dict] = {}

    for baseline in baselines:
        baseline_results = [r for r in results if r["baseline"] == baseline]

        if not baseline_results:
            continue

        # Compression stats
        reductions = []
        raw_sizes = []
        compressed_sizes = []

        for r in baseline_results:
            if r["status"] == "ok":
                comp = r.get("compression", {})
                reductions.append(comp.get("reduction_ratio", 0))
                raw_sizes.append(comp.get("raw_chars", 0))
                compressed_sizes.append(comp.get("compressed_chars", 0))

        summary[baseline] = {
            "num_tasks": len(baseline_results),
            "successful": len([r for r in baseline_results if r["status"] == "ok"]),
            "failed": len([r for r in baseline_results if r["status"] != "ok"]),
            "compression": {
                "avg_reduction_ratio": sum(reductions) / len(reductions) if reductions else 0,
                "min_reduction_ratio": min(reductions) if reductions else 0,
                "max_reduction_ratio": max(reductions) if reductions else 0,
                "avg_raw_chars": sum(raw_sizes) / len(raw_sizes) if raw_sizes else 0,
                "avg_compressed_chars": sum(compressed_sizes) / len(compressed_sizes) if compressed_sizes else 0,
            },
        }

        # Add method-specific stats if available
        retrieval_stats = []
        for r in baseline_results:
            if r["status"] == "ok":
                comp = r.get("compression", {})
                if "retrieval_stats" in comp:
                    retrieval_stats.append(comp["retrieval_stats"])

        if retrieval_stats:
            summary[baseline]["retrieval_stats"] = {
                "num_with_stats": len(retrieval_stats),
            }

    return summary


def format_comparison_table(summary: dict[str, dict]) -> str:
    """Format comparison summary as a table."""
    lines = []
    lines.append("\n" + "=" * 80)
    lines.append("BASELINE COMPARISON RESULTS")
    lines.append("=" * 80)

    # Header
    header = f"{'Baseline':<25} {'Tasks':>8} {'Success':>8} {'Avg Reduction':>15} {'Avg Raw':>12} {'Avg Compressed':>16}"
    lines.append(header)
    lines.append("-" * 80)

    # Rows
    for baseline, stats in summary.items():
        comp = stats.get("compression", {})
        row = (
            f"{baseline:<25} "
            f"{stats['num_tasks']:>8} "
            f"{stats['successful']:>8} "
            f"{comp.get('avg_reduction_ratio', 0) * 100:>14.1f}% "
            f"{comp.get('avg_raw_chars', 0):>11.0f} "
            f"{comp.get('avg_compressed_chars', 0):>15.0f}"
        )
        lines.append(row)

    lines.append("=" * 80)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run baseline comparison for OpenClaw-MemBench"
    )
    parser.add_argument(
        "--baselines",
        type=str,
        default="sliding-window,keyword,recursive-summary,hierarchical",
        help="Comma-separated list of baselines to compare",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter to specific category (e.g., 01_Recent_Constraint_Tracking)",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=0,
        help="Maximum number of tasks to run (0 = all)",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=12000,
        help="Character budget for compression",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_DIR / "comparison_summary.json"),
        help="Output file for comparison results",
    )
    parser.add_argument(
        "--list-baselines",
        action="store_true",
        help="List available baselines and exit",
    )

    args = parser.parse_args()

    if args.list_baselines:
        print("Available baselines:")
        for name in sorted(list_baselines()):
            print(f"  - {name}")
        return 0

    # Parse baseline list
    baselines = [b.strip() for b in args.baselines.split(",") if b.strip()]

    # Validate baselines
    available = set(list_baselines())
    for b in baselines:
        if b not in available:
            print(f"Error: Unknown baseline '{b}'")
            print(f"Available: {', '.join(sorted(available))}")
            return 1

    # Run comparison
    results = run_comparison(
        baselines=baselines,
        category=args.category,
        max_tasks=args.max_tasks,
        budget_chars=args.budget,
    )

    # Print summary table
    print(format_comparison_table(results["summary"]))

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nResults saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
