#!/usr/bin/env python3
"""Unified baseline comparison script with automatic result aggregation.

Usage:
    python run_all_baselines.py --task 01 --category 01_Recent_Constraint_Tracking
    python run_all_baselines.py --task-file tasks/01_Recent_Constraint_Tracking/01_Recent_Constraint_Tracking_task_01_arxiv_csv_digest.md
    python run_all_baselines.py --category 01_Recent_Constraint_Tracking --all-tasks
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv()

from eval.run_batch import run_single, collect_tasks
from utils.task_parser import parse_task_md


# Default baseline configurations to test
DEFAULT_BASELINES = [
    ("full-context", 200000, "No compression baseline"),
    ("sliding-window", 12000, "Simple recency truncation"),
    ("keyword", 12000, "Keyword-based filtering"),
    ("lcm-proxy", 12000, "LCM proxy compression"),
    ("recursive-summary", 12000, "Episode summarization"),
    ("hierarchical", 12000, "Multi-tier memory"),
]


def print_header(text: str, width: int = 70) -> None:
    """Print a formatted header."""
    print("\n" + "=" * width)
    print(f" {text}")
    print("=" * width)


def print_progress(current: int, total: int, method: str, status: str = "running") -> None:
    """Print progress indicator."""
    pct = (current / total) * 100
    bar_width = 30
    filled = int(bar_width * current / total)
    # Use ASCII-only characters for Windows compatibility
    bar = "#" * filled + "-" * (bar_width - filled)
    print(f"\r[{bar}] {pct:5.1f}% | {current}/{total} | {method}: {status}", end="", flush=True)


def run_baseline_comparison(
    task_file: Path,
    baselines: list[tuple[str, int, str]] | None = None,
    max_retries: int = 2,
    skip_errors: bool = True,
    dry_run: bool = False,
) -> list[dict]:
    """Run all baseline methods on a single task and return aggregated results.

    Args:
        task_file: Path to the task markdown file
        baselines: List of (method_name, budget, description) tuples
        max_retries: Maximum retries per method
        skip_errors: Whether to continue on errors

    Returns:
        List of result dictionaries for each baseline
    """
    baselines = baselines or DEFAULT_BASELINES
    results = []

    # Parse task once
    task = parse_task_md(task_file)
    print(f"\nTask: {task['task_id']}")
    print(f"Capability: {task.get('capability', 'N/A')}")
    print(f"Testing {len(baselines)} baseline methods...")

    total = len(baselines)

    for i, (method, budget, description) in enumerate(baselines, 1):
        print_progress(i - 1, total, method, "starting")

        # Set environment variables for this baseline
        os.environ["OPENCLAW_COMPRESSION_METHOD"] = method
        os.environ["OPENCLAW_CONTEXT_BUDGET_CHARS"] = str(budget)

        start_time = time.time()
        error_count = 0
        result = None

        while error_count <= max_retries:
            try:
                result = run_single(task_file, dry_run=dry_run)
                break
            except Exception as e:
                error_count += 1
                if error_count > max_retries:
                    result = {
                        "task_id": task["task_id"],
                        "category": task["category"],
                        "status": "error",
                        "overall_score": 0.0,
                        "error": str(e),
                        "task_file": str(task_file),
                        "output_dir": "",
                    }
                else:
                    time.sleep(2 ** error_count)  # Exponential backoff

        elapsed = time.time() - start_time

        # Enrich result with baseline info
        result["baseline_method"] = method
        result["budget"] = budget
        result["description"] = description
        result["elapsed_seconds"] = round(elapsed, 2)
        result["timestamp"] = datetime.now().isoformat()

        results.append(result)

        status = result.get("status", "unknown")
        score = result.get("overall_score", 0.0)
        print_progress(i, total, method, f"{status} (score={score:.4f})")

    print()  # New line after progress bar
    return results


def extract_token_usage(result: dict) -> dict:
    """Extract token usage from result output directory."""
    output_dir = result.get("output_dir", "")
    usage_file = Path(output_dir) / "usage.json"

    default = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "raw_context_chars": 0,
        "compressed_context_chars": 0,
        "context_reduction_ratio": 0.0,
    }

    if not usage_file.exists():
        return default

    try:
        usage = json.loads(usage_file.read_text(encoding="utf-8"))
        return {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "raw_context_chars": usage.get("raw_context_chars", 0),
            "compressed_context_chars": usage.get("compressed_context_chars", 0),
            "context_reduction_ratio": usage.get("context_reduction_ratio", 0.0),
        }
    except Exception:
        return default


def format_results_table(results: list[dict], task_id: str = "") -> str:
    """Format results as a markdown table."""
    lines = []
    lines.append(f"# Baseline Comparison Results{f' - {task_id}' if task_id else ''}\n")
    lines.append(f"**Test Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**Model:** {os.environ.get('OPENCLAW_MODEL', 'unknown')}\n")
    lines.append("")

    # Main summary table
    lines.append("## Summary Table\n")
    lines.append("| Rank | Method | Score | Status | Total Tokens | Reduction | Time (s) | Description |")
    lines.append("|------|--------|-------|--------|--------------|-----------|----------|-------------|")

    # Sort by score descending
    sorted_results = sorted(results, key=lambda x: x.get("overall_score", 0), reverse=True)

    for rank, r in enumerate(sorted_results, 1):
        method = r.get("baseline_method", "unknown")
        score = r.get("overall_score", 0.0)
        status = r.get("status", "unknown")
        elapsed = r.get("elapsed_seconds", 0)
        desc = r.get("description", "")

        usage = extract_token_usage(r)
        total_tok = usage.get("total_tokens", 0)
        reduction = usage.get("context_reduction_ratio", 0.0)

        status_icon = "[OK]" if status == "ok" else "[!]" if "fallback" in status else "[X]"

        lines.append(
            f"| {rank} | **{method}** | {score:.4f} | {status_icon} {status} | {total_tok:,} | {reduction:.1%} | {elapsed:.1f}s | {desc} |"
        )

    lines.append("")

    # Detailed metrics table
    lines.append("## Detailed Metrics\n")
    lines.append("| Method | Input | Output | Total | Raw Chars | Compressed | Reduction | Compression |")
    lines.append("|--------|-------|--------|-------|-----------|------------|-----------|-------------|")

    for r in sorted_results:
        method = r.get("baseline_method", "unknown")
        usage = extract_token_usage(r)

        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        tot = usage.get("total_tokens", 0)
        raw = usage.get("raw_context_chars", 0)
        comp = usage.get("compressed_context_chars", 0)
        red = usage.get("context_reduction_ratio", 0.0)

        # Calculate compression ratio
        if comp > 0 and raw > 0:
            ratio = raw / comp
            ratio_str = f"{ratio:.2f}×"
        else:
            ratio_str = "-"

        lines.append(
            f"| {method} | {inp:,} | {out:,} | {tot:,} | {raw:,} | {comp:,} | {red:.1%} | {ratio_str} |"
        )

    lines.append("")

    # Score breakdown
    lines.append("## Score Breakdown\n")
    lines.append("| Method | Overall | Execution | Memory Form | Compression | Capability | Constraint |")
    lines.append("|--------|---------|-----------|-------------|-------------|------------|------------|")

    for r in sorted_results:
        method = r.get("baseline_method", "unknown")
        scores = r.get("scores", {})

        ov = r.get("overall_score", 0.0)
        ex = scores.get("execution_quality_score", 0.0)
        mf = scores.get("memory_form_accuracy_score", 0.0)
        cp = scores.get("compression_fidelity_score", 0.0)
        cd = scores.get("capability_depth_score", 0.0)
        ct = scores.get("constraint_precision_score", 0.0)

        lines.append(
            f"| {method} | {ov:.4f} | {ex:.4f} | {mf:.4f} | {cp:.4f} | {cd:.4f} | {ct:.4f} |"
        )

    lines.append("")

    # Analysis
    lines.append("## Analysis\n")

    # Best accuracy
    ok_results = [r for r in results if r.get("status") == "ok"]
    if ok_results:
        best = max(ok_results, key=lambda x: x.get("overall_score", 0))
        lines.append(f"### Best Accuracy\n")
        lines.append(f"- **Method:** {best.get('baseline_method')}")
        lines.append(f"- **Score:** {best.get('overall_score', 0):.4f}")
        lines.append(f"- **Time:** {best.get('elapsed_seconds', 0):.2f}s")
        lines.append("")

    # Best efficiency
    results_with_usage = [(r, extract_token_usage(r)) for r in results if extract_token_usage(r)["total_tokens"] > 0]
    if results_with_usage:
        best_eff = min(results_with_usage, key=lambda x: x[1]["total_tokens"])
        lines.append(f"### Best Token Efficiency\n")
        lines.append(f"- **Method:** {best_eff[0].get('baseline_method')}")
        lines.append(f"- **Total Tokens:** {best_eff[1]['total_tokens']:,}")
        lines.append(f"- **Reduction:** {best_eff[1]['context_reduction_ratio']:.1%}")
        lines.append("")

    # Best balance (score per token)
    if results_with_usage:
        balanced = max(results_with_usage, key=lambda x: x[0].get("overall_score", 0) / max(1, x[1]["total_tokens"]) * 10000)
        lines.append(f"### Best Score/Efficiency Balance\n")
        lines.append(f"- **Method:** {balanced[0].get('baseline_method')}")
        lines.append(f"- **Score:** {balanced[0].get('overall_score', 0):.4f}")
        lines.append(f"- **Tokens:** {balanced[1]['total_tokens']:,}")
        lines.append("")

    # Errors
    errors = [r for r in results if "error" in r and r.get("error")]
    if errors:
        lines.append(f"### Errors/Warnings\n")
        for r in errors:
            method = r.get("baseline_method", "unknown")
            status = r.get("status", "unknown")
            err = str(r.get("error", ""))[:100]
            lines.append(f"- **{method}** ({status}): {err}...")
        lines.append("")

    return "\n".join(lines)


def save_results(results: list[dict], output_dir: Path, task_id: str) -> tuple[Path, Path]:
    """Save results in both markdown and JSON formats."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"baseline_comparison_{task_id}_{timestamp}"

    # Save markdown report
    md_file = output_dir / f"{base_name}.md"
    md_content = format_results_table(results, task_id)
    md_file.write_text(md_content, encoding="utf-8")

    # Save raw JSON
    json_file = output_dir / f"{base_name}.json"
    json_file.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

    return md_file, json_file


def main():
    parser = argparse.ArgumentParser(
        description="Run all baseline methods and generate comparison report"
    )
    parser.add_argument(
        "--task-file",
        type=Path,
        help="Path to specific task markdown file",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Category to test (e.g., 01_Recent_Constraint_Tracking)",
    )
    parser.add_argument(
        "--task-num",
        type=int,
        default=1,
        help="Task number within category (default: 1)",
    )
    parser.add_argument(
        "--all-tasks",
        action="store_true",
        help="Test all tasks in the specified category",
    )
    parser.add_argument(
        "--baselines",
        type=str,
        help="Comma-separated list of baselines to test (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT_DIR / "outputs",
        help="Output directory for results",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="Maximum retries per method (default: 1)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: test only 3 fastest baselines",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate task structure without calling API",
    )

    args = parser.parse_args()

    # Determine which baselines to test
    if args.quick:
        baselines = [
            ("full-context", 200000, "No compression baseline"),
            ("sliding-window", 12000, "Simple recency truncation"),
            ("lcm-proxy", 12000, "LCM proxy compression"),
        ]
    elif args.baselines:
        # Parse custom baseline list
        custom = [b.strip() for b in args.baselines.split(",")]
        baselines = [(b, 12000, "Custom") for b in custom]
    else:
        baselines = DEFAULT_BASELINES

    # Determine tasks to test
    if args.task_file:
        task_files = [args.task_file]
    elif args.category:
        if args.all_tasks:
            task_files = collect_tasks(args.category)
        else:
            # Find specific task by number
            task_files = collect_tasks(args.category)
            task_files = [f for f in task_files if f"_task_{args.task_num:02d}" in f.name]
            if not task_files:
                print(f"Error: Task {args.task_num} not found in category {args.category}")
                sys.exit(1)
    else:
        # Default to task 1 of category 1
        task_files = collect_tasks("01_Recent_Constraint_Tracking")[:1]

    print_header(f"Baseline Comparison Test - {len(task_files)} task(s), {len(baselines)} method(s)")

    all_results = {}
    total_start = time.time()

    for task_file in task_files:
        task_id = task_file.stem
        print_header(f"Testing: {task_id}", width=50)

        results = run_baseline_comparison(
            task_file=task_file,
            baselines=baselines,
            max_retries=args.max_retries,
            dry_run=args.dry_run,
        )

        all_results[task_id] = results

        # Save individual task results
        task_output_dir = args.output_dir / task_id
        task_output_dir.mkdir(parents=True, exist_ok=True)
        md_file, json_file = save_results(results, task_output_dir, task_id)

        print(f"\n[OK] Results saved to:")
        print(f"  - {md_file}")
        print(f"  - {json_file}")

    # If multiple tasks, create combined report
    if len(task_files) > 1:
        combined_output = args.output_dir / "combined_baseline_comparison.md"
        lines = ["# Combined Baseline Comparison Report\n"]
        lines.append(f"**Tasks Tested:** {len(task_files)}\n")
        lines.append(f"**Baselines:** {', '.join(b[0] for b in baselines)}\n")
        lines.append(f"**Total Time:** {time.time() - total_start:.1f}s\n\n")

        for task_id, results in all_results.items():
            lines.append(f"## {task_id}\n")
            lines.append(format_results_table(results, task_id))
            lines.append("\n---\n")

        combined_output.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n[OK] Combined report saved to: {combined_output}")

    print_header("Test Complete", width=50)
    print(f"Total time: {time.time() - total_start:.1f}s")


if __name__ == "__main__":
    main()
