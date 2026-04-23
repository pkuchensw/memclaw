#!/usr/bin/env python3
"""Run all baselines on all tasks and generate comprehensive comparison report.

This script:
1. Runs all available baselines on selected tasks
2. Collects compression metrics
3. Optionally runs full task execution with each baseline
4. Generates comprehensive visualizations and reports

Example:
    # Run all baselines on first 5 tasks of category 01
    python eval/run_all_baselines.py --category 01_Recent_Constraint_Tracking --max-tasks 5

    # Run specific baselines with full task execution
    python eval/run_all_baselines.py --baselines sliding-window,keyword,hierarchical --execute-tasks
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from baselines import list_baselines

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "outputs" / "baseline_comparison"


def run_baseline_comparison(
    baselines: list[str],
    category: str | None,
    max_tasks: int,
    budget: int,
) -> dict:
    """Run baseline comparison script."""
    cmd = [
        sys.executable,
        str(ROOT_DIR / "eval" / "run_baselines.py"),
        "--baselines", ",".join(baselines),
        "--budget", str(budget),
        "--output", str(OUTPUT_DIR / "comparison_summary.json"),
    ]

    if category:
        cmd.extend(["--category", category])
    if max_tasks > 0:
        cmd.extend(["--max-tasks", str(max_tasks)])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running baseline comparison:")
        print(result.stderr)
        return {}

    print(result.stdout)

    # Load results
    result_file = OUTPUT_DIR / "comparison_summary.json"
    if result_file.exists():
        return json.loads(result_file.read_text(encoding="utf-8"))
    return {}


def generate_visualizations(
    input_file: Path,
    output_dir: Path,
    format: str = "png",
) -> bool:
    """Generate visualization charts."""
    cmd = [
        sys.executable,
        str(ROOT_DIR / "eval" / "visualize_baselines.py"),
        "--input", str(input_file),
        "--output-dir", str(output_dir),
        "--format", format,
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error generating visualizations:")
        print(result.stderr)
        return False

    print(result.stdout)
    return True


def run_full_task_execution(
    baseline: str,
    category: str | None,
    max_tasks: int,
    budget: int,
) -> dict:
    """Run full task execution with a specific baseline compression method.

    This runs the actual OpenClaw agent with compressed context and evaluates
    task performance (not just compression metrics).
    """
    env = os.environ.copy()
    env["OPENCLAW_COMPRESSION_METHOD"] = baseline
    env["OPENCLAW_CONTEXT_BUDGET_CHARS"] = str(budget)

    cmd = [
        sys.executable,
        str(ROOT_DIR / "eval" / "run_batch.py"),
        "--runtime", "api",
        "--output", str(OUTPUT_DIR / f"task_results_{baseline}.json"),
    ]

    if category:
        cmd.extend(["--category", category])
    if max_tasks > 0:
        cmd.extend(["--max-tasks", str(max_tasks)])

    print(f"\nRunning full task execution with {baseline}...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        print(f"Error running tasks:")
        print(result.stderr)
        return {}

    print(result.stdout)

    # Load results
    result_file = OUTPUT_DIR / f"task_results_{baseline}.json"
    if result_file.exists():
        return json.loads(result_file.read_text(encoding="utf-8"))
    return {}


def aggregate_task_performance(results: dict[str, dict]) -> dict[str, dict]:
    """Aggregate task performance across baselines."""
    performance = {}

    for baseline, data in results.items():
        if not data:
            continue

        tasks = data if isinstance(data, list) else data.get("results", [])

        total_score = 0.0
        successful = 0
        failed = 0

        for task in tasks:
            status = task.get("status", "")
            if status in ("ok", "ok_fallback"):
                successful += 1
                total_score += task.get("overall_score", 0)
            elif status in ("error", "api_error", "grading_error"):
                failed += 1

        num_tasks = len(tasks)
        performance[baseline] = {
            "num_tasks": num_tasks,
            "successful": successful,
            "failed": failed,
            "avg_score": total_score / max(1, successful),
            "success_rate": successful / max(1, num_tasks),
        }

    return performance


def generate_comprehensive_report(
    compression_results: dict,
    task_results: dict[str, dict],
    output_path: Path,
) -> None:
    """Generate comprehensive markdown report."""
    lines = []
    lines.append("# OpenClaw-MemBench Baseline Comparison Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Compression Summary
    lines.append("## Compression Performance")
    lines.append("")
    lines.append("| Baseline | Avg Reduction | Avg Raw Size | Avg Compressed | Speed |")
    lines.append("|----------|---------------|--------------|----------------|-------|")

    summary = compression_results.get("summary", {})
    for baseline, stats in summary.items():
        comp = stats.get("compression", {})
        row = (
            f"| {baseline} | "
            f"{comp.get('avg_reduction_ratio', 0) * 100:.1f}% | "
            f"{comp.get('avg_raw_chars', 0):.0f} | "
            f"{comp.get('avg_compressed_chars', 0):.0f} | "
            f"N/A |"
        )
        lines.append(row)

    lines.append("")

    # Task Performance (if available)
    if task_results:
        lines.append("## Task Performance (with Full Execution)")
        lines.append("")
        lines.append("| Baseline | Tasks | Success Rate | Avg Score |")
        lines.append("|----------|-------|--------------|-----------|")

        perf = aggregate_task_performance(task_results)
        for baseline, stats in perf.items():
            row = (
                f"| {baseline} | "
                f"{stats['num_tasks']} | "
                f"{stats['success_rate'] * 100:.1f}% | "
                f"{stats['avg_score']:.3f} |"
            )
            lines.append(row)

        lines.append("")

    # Retention Analysis
    lines.append("## Retention Analysis")
    lines.append("")
    lines.append("Retention = Task Performance / Compression Ratio")
    lines.append("")

    if task_results and summary:
        lines.append("| Baseline | Compression | Task Score | Retention |")
        lines.append("|----------|-------------|------------|-----------|")

        perf = aggregate_task_performance(task_results)
        for baseline in summary.keys():
            comp_ratio = summary[baseline].get("compression", {}).get("avg_reduction_ratio", 0)
            task_score = perf.get(baseline, {}).get("avg_score", 0)
            retention = task_score / max(0.01, comp_ratio) if comp_ratio > 0 else 0

            row = (
                f"| {baseline} | "
                f"{comp_ratio * 100:.1f}% | "
                f"{task_score:.3f} | "
                f"{retention:.2f} |"
            )
            lines.append(row)

        lines.append("")

    # Method Descriptions
    lines.append("## Method Descriptions")
    lines.append("")

    descriptions = {
        "sliding-window": "Simple truncation keeping most recent content. Fast but loses historical constraints.",
        "keyword": "Extracts lines with important keywords. Good for constraint preservation.",
        "recursive-summary": "Hierarchical episode summarization. Preserves structure.",
        "hierarchical": "Multi-tier memory (working/short-term/long-term). Mimics human memory.",
        "mem0": "Fact extraction and categorization. Good for state tracking.",
        "vector-retrieval": "Semantic similarity retrieval. Query-adaptive.",
    }

    for baseline, desc in descriptions.items():
        if baseline in summary:
            lines.append(f"### {baseline}")
            lines.append("")
            lines.append(desc)
            lines.append("")

    # Visualizations
    lines.append("## Visualizations")
    lines.append("")
    lines.append("See the following generated charts:")
    lines.append("")
    lines.append("- `reduction_comparison.png`: Compression ratio comparison")
    lines.append("- `size_comparison.png`: Raw vs compressed size")
    lines.append("- `success_rate.png`: Compression success rates")
    lines.append("- `retention_curve.png`: Performance vs compression trade-off")
    lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    lines.append("Based on the comparison results:")
    lines.append("")

    if summary:
        # Find best compression
        best_compression = max(
            summary.items(),
            key=lambda x: x[1].get("compression", {}).get("avg_reduction_ratio", 0)
        )
        lines.append(f"- **Best Compression:** {best_compression[0]} "
                    f"({best_compression[1].get('compression', {}).get('avg_reduction_ratio', 0) * 100:.1f}% reduction)")

    if task_results:
        perf = aggregate_task_performance(task_results)
        best_task = max(perf.items(), key=lambda x: x[1].get("avg_score", 0))
        lines.append(f"- **Best Task Performance:** {best_task[0]} "
                    f"(score: {best_task[1].get('avg_score', 0):.3f})")

        # Best retention
        if summary:
            retentions = []
            for baseline in summary.keys():
                comp_ratio = summary[baseline].get("compression", {}).get("avg_reduction_ratio", 0)
                task_score = perf.get(baseline, {}).get("avg_score", 0)
                retention = task_score / max(0.01, comp_ratio) if comp_ratio > 0 else 0
                retentions.append((baseline, retention))

            if retentions:
                best_retention = max(retentions, key=lambda x: x[1])
                lines.append(f"- **Best Retention:** {best_retention[0]} "
                            f"(retention: {best_retention[1]:.2f})")

    lines.append("")

    # Write report
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nComprehensive report saved to: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run comprehensive baseline comparison"
    )
    parser.add_argument(
        "--baselines",
        type=str,
        default="all",
        help="Comma-separated list or 'all'",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Category to run (e.g., 01_Recent_Constraint_Tracking)",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=5,
        help="Maximum tasks per category (default: 5)",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=12000,
        help="Character budget for compression",
    )
    parser.add_argument(
        "--execute-tasks",
        action="store_true",
        help="Also run full task execution (slower, requires API)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Output directory",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        choices=["png", "pdf", "svg", "all"],
        help="Visualization format",
    )

    args = parser.parse_args()

    # Determine baselines to run
    available_baselines = list_baselines()
    if args.baselines == "all":
        baselines = available_baselines
    else:
        baselines = [b.strip() for b in args.baselines.split(",") if b.strip()]
        # Validate
        for b in baselines:
            if b not in available_baselines:
                print(f"Error: Unknown baseline '{b}'")
                print(f"Available: {', '.join(available_baselines)}")
                return 1

    print("=" * 80)
    print("OpenClaw-MemBench Baseline Comparison")
    print("=" * 80)
    print(f"Baselines: {', '.join(baselines)}")
    print(f"Category: {args.category or 'All'}")
    print(f"Max Tasks: {args.max_tasks}")
    print(f"Budget: {args.budget} chars")
    print(f"Full Execution: {args.execute_tasks}")
    print("=" * 80)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Run compression comparison
    print("\n[1/3] Running compression comparison...")
    compression_results = run_baseline_comparison(
        baselines=baselines,
        category=args.category,
        max_tasks=args.max_tasks,
        budget=args.budget,
    )

    if not compression_results:
        print("Error: No compression results generated")
        return 1

    # Step 2: Generate visualizations
    print("\n[2/3] Generating visualizations...")
    comparison_file = OUTPUT_DIR / "comparison_summary.json"
    if comparison_file.exists():
        generate_visualizations(
            input_file=comparison_file,
            output_dir=OUTPUT_DIR,
            format=args.format,
        )

    # Step 3: Optionally run full task execution
    task_results: dict[str, dict] = {}
    if args.execute_tasks:
        print("\n[3/3] Running full task execution...")
        for baseline in baselines:
            task_results[baseline] = run_full_task_execution(
                baseline=baseline,
                category=args.category,
                max_tasks=args.max_tasks,
                budget=args.budget,
            )
    else:
        print("\n[3/3] Skipping full task execution (use --execute-tasks to enable)")

    # Generate comprehensive report
    print("\nGenerating comprehensive report...")
    generate_comprehensive_report(
        compression_results=compression_results,
        task_results=task_results,
        output_path=OUTPUT_DIR / "COMPREHENSIVE_REPORT.md",
    )

    print("\n" + "=" * 80)
    print("Baseline Comparison Complete!")
    print("=" * 80)
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print(f"\nKey files:")
    print(f"  - comparison_summary.json: Raw comparison data")
    print(f"  - COMPREHENSIVE_REPORT.md: Full report")
    print(f"  - *.png: Visualization charts")

    return 0


if __name__ == "__main__":
    sys.exit(main())
