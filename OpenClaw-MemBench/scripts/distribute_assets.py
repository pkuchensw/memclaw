#!/usr/bin/env python3
"""Distribute assets to task workspaces.

This script copies or symlinks assets from the assets/ directory
to the appropriate task workspaces based on capability requirements.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.task_parser import parse_task_md

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
WORKSPACE_DIR = ROOT_DIR / "workspace"
TASKS_DIR = ROOT_DIR / "tasks"

# Asset requirements per capability
CAPABILITY_ASSETS = {
    "01_Recent_Constraint_Tracking": {
        "images": ["document_scan", "fashion", "food_package"],
        "pdfs": ["clean_paper", "noisy_scan", "table_doc"],
        "videos": ["*"],
    },
    "02_Version_Update": {
        "email_calendar": ["*"],
        "logs": ["*"],
        "conflicts": ["*"],
    },
    "03_Procedure_Transfer": {
        "images": ["document_scan", "fashion"],
        "videos": ["*"],
    },
    "04_Repeated_Mistake_Prevention": {
        "logs": ["*"],
    },
    "05_Source_Conflict_Resolution": {
        "conflicts": ["*"],
        "screenshots": ["*"],
        "email_calendar": ["*"],
    },
    "06_Memory_Operation_Selection": {
        "pdfs": ["clean_paper"],
        "images": ["document_scan"],
        "tables": ["*"],
    },
    "07_Goal_Interruption_Resumption": {
        "videos": ["*"],
        "email_calendar": ["*"],
    },
    "08_Staleness_Applicability_Judgment": {
        "conflicts": ["*"],
    },
}


def get_task_category(task_file: Path) -> str:
    """Extract category from task file path."""
    return task_file.parent.name


def copy_assets_for_task(task_file: Path, use_symlink: bool = False, dry_run: bool = False) -> dict:
    """Copy/link required assets for a task.

    Returns:
        Dict with stats: {copied: int, linked: int, skipped: int, errors: list}
    """
    task = parse_task_md(task_file)
    category = task.get("category", "")
    workspace_path = Path(task.get("workspace_path", ""))

    stats = {"copied": 0, "linked": 0, "skipped": 0, "errors": []}

    if not category or not workspace_path.exists():
        stats["errors"].append(f"Invalid task: {task_file}")
        return stats

    asset_config = CAPABILITY_ASSETS.get(category, {})

    for asset_type, subdirs in asset_config.items():
        asset_dir = ASSETS_DIR / asset_type
        if not asset_dir.exists():
            continue

        # Determine target directory in workspace
        if asset_type in ["images", "pdfs", "videos", "tables", "screenshots"]:
            target_dir = workspace_path / "evidence" / asset_type
        elif asset_type in ["logs", "conflicts", "email_calendar"]:
            target_dir = workspace_path / "episodes" / asset_type
        else:
            target_dir = workspace_path / "evidence" / asset_type

        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

        # Process subdirectories or root
        if "*" in subdirs:
            # Copy everything from asset_type directory
            src_dirs = [d for d in asset_dir.iterdir() if d.is_dir()]
            if not src_dirs:
                src_dirs = [asset_dir]  # Use root if no subdirs
        else:
            src_dirs = [asset_dir / s for s in subdirs if (asset_dir / s).exists()]

        for src_dir in src_dirs:
            if not src_dir.exists():
                continue

            # Copy files
            for src_file in src_dir.rglob("*"):
                if not src_file.is_file():
                    continue

                rel_path = src_file.relative_to(src_dir)
                dst_file = target_dir / rel_path

                if dry_run:
                    print(f"[DRY-RUN] Would copy: {src_file} -> {dst_file}")
                    stats["copied"] += 1
                    continue

                try:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)

                    if use_symlink:
                        if dst_file.exists() or dst_file.is_symlink():
                            dst_file.unlink()
                        dst_file.symlink_to(src_file.resolve())
                        stats["linked"] += 1
                    else:
                        if dst_file.exists():
                            stats["skipped"] += 1
                            continue
                        shutil.copy2(src_file, dst_file)
                        stats["copied"] += 1
                except Exception as e:
                    stats["errors"].append(f"Failed to copy {src_file}: {e}")

    return stats


def distribute_all(category: str | None = None, use_symlink: bool = False, dry_run: bool = False) -> dict:
    """Distribute assets to all tasks."""
    total_stats = {"copied": 0, "linked": 0, "skipped": 0, "errors": [], "tasks": 0}

    if category:
        task_dirs = [TASKS_DIR / category]
    else:
        task_dirs = [d for d in TASKS_DIR.iterdir() if d.is_dir()]

    for task_dir in task_dirs:
        if not task_dir.exists():
            continue

        for task_file in task_dir.glob("*.md"):
            if task_file.name in ["README.md", "TASK_INDEX.md"]:
                continue

            stats = copy_assets_for_task(task_file, use_symlink, dry_run)
            total_stats["copied"] += stats["copied"]
            total_stats["linked"] += stats["linked"]
            total_stats["skipped"] += stats["skipped"]
            total_stats["errors"].extend(stats["errors"])
            total_stats["tasks"] += 1

            if not dry_run:
                print(f"Processed {task_file.name}: {stats['copied']} copied, {stats['linked']} linked")

    return total_stats


def main():
    parser = argparse.ArgumentParser(description="Distribute assets to task workspaces")
    parser.add_argument("--category", type=str, default=None, help="Process only one category")
    parser.add_argument("--symlink", action="store_true", help="Use symlinks instead of copying")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    print(f"Distributing assets (symlink={args.symlink}, dry_run={args.dry_run})...")
    stats = distribute_all(args.category, args.symlink, args.dry_run)

    print(f"\nSummary:")
    print(f"  Tasks processed: {stats['tasks']}")
    print(f"  Files copied: {stats['copied']}")
    print(f"  Files linked: {stats['linked']}")
    print(f"  Files skipped: {stats['skipped']}")
    print(f"  Errors: {len(stats['errors'])}")

    if stats["errors"]:
        print("\nErrors:")
        for err in stats["errors"][:10]:
            print(f"  - {err}")

    return 0 if not stats["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
