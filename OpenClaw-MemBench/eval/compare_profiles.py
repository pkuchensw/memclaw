from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / os.environ.get("OUTPUT_SUBDIR", "outputs")


def _run_round(profile: str, runtime: str, max_tasks: int, timeout: int, retries: int, output_path: Path) -> None:
    env = os.environ.copy()
    env["OPENCLAW_CONTEXT_PROFILE"] = profile
    env["OPENCLAW_REQUEST_TIMEOUT"] = str(timeout)
    env["OPENCLAW_MAX_RETRIES"] = str(retries)

    cmd = [
        "python",
        "eval/run_batch.py",
        "--runtime",
        runtime,
        "--max-tasks",
        str(max_tasks),
        "--output",
        str(output_path),
    ]
    subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, check=True)


def _summarize(summary_path: Path) -> dict:
    rows = json.loads(summary_path.read_text(encoding="utf-8"))
    total = len(rows)
    ok_rows = [r for r in rows if r.get("status") == "ok"]
    success_rate = (len(ok_rows) / total) if total else 0.0
    avg_score = (sum(float(r.get("overall_score", 0.0)) for r in rows) / total) if total else 0.0

    total_cost = 0.0
    total_input = 0
    total_output = 0
    usage_count = 0
    for r in rows:
        out_dir = r.get("output_dir")
        if not out_dir:
            continue
        u_path = Path(out_dir) / "usage.json"
        if not u_path.exists():
            continue
        try:
            u = json.loads(u_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        total_cost += float(u.get("estimated_cost", 0.0) or 0.0)
        total_input += int(u.get("input_tokens", 0) or 0)
        total_output += int(u.get("output_tokens", 0) or 0)
        usage_count += 1

    return {
        "summary_path": str(summary_path),
        "total_tasks": total,
        "ok_tasks": len(ok_rows),
        "success_rate": round(success_rate, 4),
        "avg_overall_score": round(avg_score, 4),
        "usage_count": usage_count,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_estimated_cost": round(total_cost, 8),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare full vs compressed context profile")
    parser.add_argument("--runtime", choices=["api", "docker"], default="api")
    parser.add_argument("--max-tasks", type=int, default=40)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--retries", type=int, default=1)
    args = parser.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = OUTPUT_DIR / f"compare_full_{args.runtime}_{stamp}.json"
    compressed_path = OUTPUT_DIR / f"compare_compressed_{args.runtime}_{stamp}.json"

    _run_round("full", args.runtime, args.max_tasks, args.timeout, args.retries, full_path)
    _run_round("compressed", args.runtime, args.max_tasks, args.timeout, args.retries, compressed_path)

    full = _summarize(full_path)
    compressed = _summarize(compressed_path)
    delta = {
        "success_rate_delta": round(compressed["success_rate"] - full["success_rate"], 4),
        "avg_overall_score_delta": round(compressed["avg_overall_score"] - full["avg_overall_score"], 4),
        "estimated_cost_delta": round(compressed["total_estimated_cost"] - full["total_estimated_cost"], 8),
        "input_tokens_delta": compressed["total_input_tokens"] - full["total_input_tokens"],
        "output_tokens_delta": compressed["total_output_tokens"] - full["total_output_tokens"],
    }

    report = {
        "runtime": args.runtime,
        "max_tasks": args.max_tasks,
        "timeout": args.timeout,
        "retries": args.retries,
        "full": full,
        "compressed": compressed,
        "delta_compressed_minus_full": delta,
    }

    out = OUTPUT_DIR / f"compare_report_{args.runtime}_{stamp}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport written to: {out}")


if __name__ == "__main__":
    main()
