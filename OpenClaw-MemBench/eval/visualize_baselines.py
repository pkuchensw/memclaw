#!/usr/bin/env python3
"""Visualization for baseline comparison results."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def load_comparison_results(path: Path) -> dict:
    """Load comparison results from JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def plot_reduction_comparison(summary: dict[str, dict], output_path: Path) -> None:
    """Plot compression reduction ratio comparison."""
    baselines = list(summary.keys())
    avg_reductions = [
        summary[b]["compression"]["avg_reduction_ratio"] * 100
        for b in baselines
    ]
    min_reductions = [
        summary[b]["compression"]["min_reduction_ratio"] * 100
        for b in baselines
    ]
    max_reductions = [
        summary[b]["compression"]["max_reduction_ratio"] * 100
        for b in baselines
    ]

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(baselines))
    width = 0.6

    bars = ax.bar(x, avg_reductions, width, label="Average", color="steelblue")

    # Add error bars for min/max
    ax.errorbar(
        x, avg_reductions,
        yerr=[
            [avg - min_r for avg, min_r in zip(avg_reductions, min_reductions)],
            [max_r - avg for avg, max_r in zip(avg_reductions, max_reductions)],
        ],
        fmt="none",
        color="black",
        capsize=5,
    )

    ax.set_ylabel("Reduction Ratio (%)")
    ax.set_title("Context Compression: Average Reduction by Baseline")
    ax.set_xticks(x)
    ax.set_xticklabels(baselines, rotation=45, ha="right")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.3)

    # Add value labels on bars
    for bar, val in zip(bars, avg_reductions):
        height = bar.get_height()
        ax.annotate(
            f"{val:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Saved: {output_path}")


def plot_size_comparison(summary: dict[str, dict], output_path: Path) -> None:
    """Plot raw vs compressed size comparison."""
    baselines = list(summary.keys())
    raw_sizes = [
        summary[b]["compression"]["avg_raw_chars"] / 1000
        for b in baselines
    ]
    compressed_sizes = [
        summary[b]["compression"]["avg_compressed_chars"] / 1000
        for b in baselines
    ]

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(baselines))
    width = 0.35

    bars1 = ax.bar(x - width/2, raw_sizes, width, label="Raw", color="lightcoral")
    bars2 = ax.bar(x + width/2, compressed_sizes, width, label="Compressed", color="lightgreen")

    ax.set_ylabel("Size (KB)")
    ax.set_title("Context Size: Raw vs Compressed")
    ax.set_xticks(x)
    ax.set_xticklabels(baselines, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Saved: {output_path}")


def plot_success_rate(summary: dict[str, dict], output_path: Path) -> None:
    """Plot success rate by baseline."""
    baselines = list(summary.keys())
    success_rates = [
        summary[b]["successful"] / max(summary[b]["num_tasks"], 1) * 100
        for b in baselines
    ]

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ["green" if r >= 90 else "orange" if r >= 70 else "red" for r in success_rates]
    bars = ax.bar(baselines, success_rates, color=colors, alpha=0.7)

    ax.set_ylabel("Success Rate (%)")
    ax.set_title("Compression Success Rate by Baseline")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, success_rates):
        height = bar.get_height()
        ax.annotate(
            f"{val:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
        )

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Saved: {output_path}")


def plot_retention_curve(results: list[dict], output_path: Path) -> None:
    """Plot retention curve across different budget levels.

    This simulates how performance changes with different budget levels.
    """
    # Group results by baseline
    by_baseline: dict[str, list[dict]] = {}
    for r in results:
        b = r["baseline"]
        if b not in by_baseline:
            by_baseline[b] = []
        by_baseline[b].append(r)

    fig, ax = plt.subplots(figsize=(10, 6))

    for baseline, baseline_results in by_baseline.items():
        # Sort by reduction ratio
        sorted_results = sorted(
            baseline_results,
            key=lambda x: x.get("compression", {}).get("reduction_ratio", 0)
        )

        # Use task success as proxy for retention (would need actual grading scores)
        x_vals = []
        y_vals = []

        for r in sorted_results:
            if r["status"] == "ok":
                reduction = r.get("compression", {}).get("reduction_ratio", 0)
                # Use reduction as proxy for budget (higher reduction = lower budget)
                x_vals.append(reduction * 100)
                # Assume success for now (1.0)
                y_vals.append(1.0)

        if x_vals and y_vals:
            ax.plot(x_vals, y_vals, marker="o", label=baseline, alpha=0.7)

    ax.set_xlabel("Compression Ratio (%)")
    ax.set_ylabel("Task Success Rate")
    ax.set_title("Retention Curve: Performance vs Compression")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Saved: {output_path}")


def generate_markdown_report(results: dict, output_path: Path) -> None:
    """Generate a markdown report of comparison results."""
    meta = results.get("metadata", {})
    summary = results.get("summary", {})

    lines = []
    lines.append("# Baseline Comparison Report")
    lines.append("")
    lines.append(f"**Date:** {meta.get('timestamp', 'N/A')}")
    lines.append(f"**Budget:** {meta.get('budget_chars', 'N/A')} characters")
    lines.append(f"**Tasks:** {meta.get('num_tasks', 'N/A')}")
    lines.append("")

    lines.append("## Summary Table")
    lines.append("")
    lines.append("| Baseline | Tasks | Success | Avg Reduction | Avg Raw | Avg Compressed |")
    lines.append("|----------|-------|---------|---------------|---------|----------------|")

    for baseline, stats in summary.items():
        comp = stats.get("compression", {})
        row = (
            f"| {baseline} | "
            f"{stats['num_tasks']} | "
            f"{stats['successful']} | "
            f"{comp.get('avg_reduction_ratio', 0) * 100:.1f}% | "
            f"{comp.get('avg_raw_chars', 0):.0f} | "
            f"{comp.get('avg_compressed_chars', 0):.0f} |"
        )
        lines.append(row)

    lines.append("")
    lines.append("## Detailed Analysis")
    lines.append("")

    for baseline, stats in summary.items():
        lines.append(f"### {baseline}")
        lines.append("")
        lines.append(f"- **Tasks:** {stats['num_tasks']}")
        lines.append(f"- **Successful:** {stats['successful']}")
        lines.append(f"- **Failed:** {stats['failed']}")
        lines.append(f"- **Avg Reduction:** {stats['compression']['avg_reduction_ratio'] * 100:.1f}%")
        lines.append(f"- **Min Reduction:** {stats['compression']['min_reduction_ratio'] * 100:.1f}%")
        lines.append(f"- **Max Reduction:** {stats['compression']['max_reduction_ratio'] * 100:.1f}%")
        lines.append("")

    lines.append("## Visualizations")
    lines.append("")
    lines.append("- `reduction_comparison.png`: Average compression reduction by baseline")
    lines.append("- `size_comparison.png`: Raw vs compressed size comparison")
    lines.append("- `success_rate.png`: Compression success rate by baseline")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Visualize baseline comparison results"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to comparison_results.json",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/baseline_comparison",
        help="Output directory for visualizations",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        choices=["png", "pdf", "svg", "all"],
        help="Output format",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load results
    results = load_comparison_results(input_path)
    summary = results.get("summary", {})

    print(f"Loaded results for {len(summary)} baselines")

    # Generate plots
    try:
        plot_reduction_comparison(
            summary,
            output_dir / f"reduction_comparison.{args.format}"
        )
        plot_size_comparison(
            summary,
            output_dir / f"size_comparison.{args.format}"
        )
        plot_success_rate(
            summary,
            output_dir / f"success_rate.{args.format}"
        )
        plot_retention_curve(
            results.get("results", []),
            output_dir / f"retention_curve.{args.format}"
        )

        # Generate markdown report
        generate_markdown_report(results, output_dir / "report.md")

        print(f"\nAll visualizations saved to: {output_dir}")
        return 0

    except Exception as e:
        print(f"Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
