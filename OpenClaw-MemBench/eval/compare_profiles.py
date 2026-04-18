from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / os.environ.get("OUTPUT_SUBDIR", "outputs")


def _run_round(method: str, runtime: str, max_tasks: int, timeout: int, retries: int, output_path: Path) -> None:
    env = os.environ.copy()
    env["OPENCLAW_CONTEXT_PROFILE"] = "benchmark"
    env["OPENCLAW_COMPRESSION_METHOD"] = method
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
    total_raw_context = 0
    total_compressed_context = 0
    reduction = []

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
        total_raw_context += int(u.get("raw_context_chars", 0) or 0)
        total_compressed_context += int(u.get("compressed_context_chars", 0) or 0)
        rr = float(u.get("context_reduction_ratio", 0.0) or 0.0)
        reduction.append(rr)

    avg_reduction = round(sum(reduction) / len(reduction), 4) if reduction else 0.0

    return {
        "summary_path": str(summary_path),
        "total_tasks": total,
        "ok_tasks": len(ok_rows),
        "success_rate": round(success_rate, 4),
        "avg_overall_score": round(avg_score, 4),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_estimated_cost": round(total_cost, 8),
        "total_raw_context_chars": total_raw_context,
        "total_compressed_context_chars": total_compressed_context,
        "avg_context_reduction_ratio": avg_reduction,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare multiple compression methods")
    parser.add_argument("--runtime", choices=["api", "docker"], default="api")
    parser.add_argument("--max-tasks", type=int, default=40)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument(
        "--methods",
        type=str,
        default="full,lcm-proxy,sliding-window,keyword,episode",
        help="Comma-separated compression methods",
    )
    args = parser.parse_args()

    methods = [m.strip() for m in args.methods.split(",") if m.strip()]
    if not methods:
        raise SystemExit("No compression methods provided")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    per_method: dict[str, dict] = {}

    for method in methods:
        out_path = OUTPUT_DIR / f"compare_{method}_{args.runtime}_{stamp}.json"
        _run_round(method, args.runtime, args.max_tasks, args.timeout, args.retries, out_path)
        per_method[method] = _summarize(out_path)

    baseline = per_method.get("full") or per_method[methods[0]]
    retention = {}
    for method, info in per_method.items():
        base_success = float(baseline.get("success_rate", 0.0) or 0.0)
        cur_success = float(info.get("success_rate", 0.0) or 0.0)
        retention_score = 0.0 if base_success <= 0 else round(cur_success / base_success, 4)
        retention[method] = {
            "retention": retention_score,
            "success_rate_delta_vs_baseline": round(cur_success - base_success, 4),
            "avg_score_delta_vs_baseline": round(
                float(info.get("avg_overall_score", 0.0)) - float(baseline.get("avg_overall_score", 0.0)),
                4,
            ),
            "cost_delta_vs_baseline": round(
                float(info.get("total_estimated_cost", 0.0)) - float(baseline.get("total_estimated_cost", 0.0)),
                8,
            ),
        }

    report = {
        "runtime": args.runtime,
        "max_tasks": args.max_tasks,
        "timeout": args.timeout,
        "retries": args.retries,
        "methods": methods,
        "baseline_method": "full" if "full" in per_method else methods[0],
        "summary": per_method,
        "retention": retention,
    }

    out = OUTPUT_DIR / f"compare_report_{args.runtime}_{stamp}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport written to: {out}")


if __name__ == "__main__":
    main()
