from __future__ import annotations

import json
from pathlib import Path


def aggregate_scores(scores: dict[str, float]) -> float:
    numeric = [v for v in scores.values() if isinstance(v, (int, float))]
    if not numeric:
        return 0.0
    return round(sum(numeric) / len(numeric), 4)


def format_table(rows: list[dict]) -> str:
    header = ["task_id", "overall_score", "status"]
    lines = ["\t".join(header)]
    for r in rows:
        lines.append("\t".join([
            str(r.get("task_id", "")),
            f"{r.get('overall_score', 0.0):.4f}",
            str(r.get("status", "ok")),
        ]))
    return "\n".join(lines)


def write_summary(output_path: Path, rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
