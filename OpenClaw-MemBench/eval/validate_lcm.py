from __future__ import annotations

import argparse
import json
from pathlib import Path


def _validate_usage(path: Path) -> tuple[bool, list[str]]:
    msgs: list[str] = []
    if not path.exists():
        return False, [f"missing usage file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, [f"invalid json: {path} ({exc})"]

    required = [
        "compression_method",
        "raw_context_chars",
        "compressed_context_chars",
        "context_reduction_ratio",
        "scenario_turns",
        "compression_events",
    ]
    for k in required:
        if k not in data:
            msgs.append(f"missing key {k} in {path}")

    raw_chars = int(data.get("raw_context_chars", 0) or 0)
    compressed_chars = int(data.get("compressed_context_chars", 0) or 0)
    if raw_chars > 0 and compressed_chars > raw_chars:
        msgs.append(f"compressed_context_chars > raw_context_chars in {path}")

    rr = float(data.get("context_reduction_ratio", 0.0) or 0.0)
    if rr < -0.01 or rr > 1.01:
        msgs.append(f"invalid reduction ratio in {path}: {rr}")

    return len(msgs) == 0, msgs


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate LCM/compression logging correctness")
    parser.add_argument("--summary", type=str, required=True, help="Path to run summary json")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    rows = json.loads(summary_path.read_text(encoding="utf-8"))

    errors: list[str] = []
    checked = 0
    for r in rows:
        out_dir = r.get("output_dir")
        if not out_dir:
            continue
        usage_path = Path(out_dir) / "usage.json"
        ok, msgs = _validate_usage(usage_path)
        checked += 1
        if not ok:
            errors.extend(msgs)

    report = {
        "summary": str(summary_path),
        "checked_runs": checked,
        "valid": len(errors) == 0,
        "errors": errors,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
