from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"

CAPABILITY_HINT = {
    "01_Recent_Constraint_Tracking": "Track latest constraints and slot-level output requirements.",
    "02_Version_Update": "Supersede outdated configuration with latest state chain.",
    "03_Procedure_Transfer": "Reuse successful abstract workflow while adapting source-specific steps.",
    "04_Repeated_Mistake_Prevention": "Apply prior failure checklist before taking risky actions.",
    "05_Source_Conflict_Resolution": "Arbitrate conflicting evidence by trust and recency.",
    "06_Memory_Operation_Selection": "Route each episode into proper memory form.",
    "07_Goal_Interruption_Resumption": "Checkpoint and resume exact unfinished subgoal.",
    "08_Staleness_Applicability_Judgment": "Reject stale procedure when environment changed.",
}


def _read_frontmatter(task_file: Path) -> dict:
    text = task_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    return yaml.safe_load(text[4:end]) or {}


def _workspace_path(meta: dict, task_file: Path) -> Path:
    text = task_file.read_text(encoding="utf-8")
    marker = "## Workspace Path"
    idx = text.find(marker)
    if idx >= 0:
        rest = text[idx + len(marker):]
        for line in rest.splitlines():
            ln = line.strip()
            if not ln or ln.startswith("```"):
                continue
            ws = ROOT / ln
            if ws.exists():
                return ws

    # Fallback for legacy templates.
    category = meta.get("category", task_file.parent.name)
    task_id = str(meta.get("id", task_file.stem))
    return ROOT / "workspace" / category / task_id.replace(f"{category}_", "")


def _long_noise(turn_seed: int) -> str:
    s = (
        f"Background note block {turn_seed}: "
        "A long context segment with procedural chatter, historical references, and noisy status logs. "
        "The operator discusses side threads about dependency trees, file naming consistency, prior retries, "
        "and potential evidence conflicts. This block should increase context length and force selective recall. "
        "Do not treat this as latest instruction unless explicitly marked as active constraint."
    )
    return s


def _build_turns(task_id: str, category: str) -> list[dict]:
    hint = CAPABILITY_HINT.get(category, "Apply capability-specific memory routing.")
    turns: list[dict] = []
    tid = 1

    turns.append(
        {
            "turn_id": tid,
            "episode_id": "E0_bootstrap",
            "role": "system",
            "content": f"Task bootstrap for {task_id}. Primary capability focus: {hint}",
            "compression_hint": "none",
        }
    )
    tid += 1

    # Episode 1: initial constraints.
    for i in range(1, 7):
        turns.append(
            {
                "turn_id": tid,
                "episode_id": "E1_constraints",
                "role": "user",
                "content": f"Constraint packet {i}: keep deterministic artifacts, strict schema, exact output paths.",
                "compression_hint": "checkpoint_soft" if i in {3, 6} else "",
            }
        )
        tid += 1

    # Episode 2: noisy long history.
    for i in range(7, 35):
        turns.append(
            {
                "turn_id": tid,
                "episode_id": "E2_noise_history",
                "role": "tool" if i % 4 == 0 else "user",
                "content": _long_noise(i),
                "compression_hint": "checkpoint_soft" if i in {12, 20, 30} else "",
            }
        )
        tid += 1

    # Episode 3: update/supersede state.
    for i in range(1, 7):
        turns.append(
            {
                "turn_id": tid,
                "episode_id": "E3_state_update",
                "role": "user",
                "content": (
                    f"Update {i}: newest rule supersedes older notes. "
                    "Use latest constraints only; outdated references must be ignored in final output."
                ),
                "compression_hint": "checkpoint_hard" if i in {3, 6} else "",
            }
        )
        tid += 1

    # Episode 4: interruption/resume style context.
    for i in range(1, 9):
        turns.append(
            {
                "turn_id": tid,
                "episode_id": "E4_interruption",
                "role": "assistant" if i % 2 == 0 else "user",
                "content": (
                    f"Interruption turn {i}: pause main objective, execute temporary side task, "
                    "then preserve progress snapshot for exact resumption."
                ),
                "compression_hint": "checkpoint_soft" if i in {4, 8} else "",
            }
        )
        tid += 1

    # Episode 5: conflict evidence.
    for i in range(1, 7):
        turns.append(
            {
                "turn_id": tid,
                "episode_id": "E5_conflict",
                "role": "tool",
                "content": (
                    f"Evidence source {i}: claims differ across docs/logs/messages. "
                    "Prioritize high-trust, recent, executable evidence in arbitration."
                ),
                "compression_hint": "checkpoint_hard" if i in {3, 6} else "",
            }
        )
        tid += 1

    # Final instruction turn before real prompt.
    turns.append(
        {
            "turn_id": tid,
            "episode_id": "E6_final_pre_task",
            "role": "user",
            "content": "Final pre-task reminder: produce machine-checkable outputs and cite decision evidence.",
            "compression_hint": "checkpoint_final",
        }
    )

    return turns


def _build_oracle(task_id: str, category: str) -> dict:
    return {
        "task_id": task_id,
        "primary_capability": category,
        "secondary_capability": [
            "06_Memory_Operation_Selection",
            "07_Goal_Interruption_Resumption",
        ],
        "gold_constraints": [
            "strict_schema",
            "exact_output_paths",
            "latest_rule_overrides_old",
        ],
        "gold_latest_state": {
            "state_version": "v3",
            "supersedes": ["v1", "v2"],
        },
        "gold_procedure": [
            "read_context",
            "resolve_conflict",
            "execute_tools",
            "validate_artifacts",
            "write_manifest",
        ],
        "gold_anti_rule": [
            "no_destructive_overwrite",
            "no_stale_rule_reuse",
            "no_first_page_only_fetch",
        ],
        "gold_evidence_priority": [
            "runtime_logs",
            "config_files",
            "recent_messages",
            "stale_docs",
        ],
        "gold_memory_operation": [
            "context_cache",
            "state_memory",
            "procedural_memory",
            "anti_memory",
            "evidence_graph",
        ],
        "compression_checkpoints": [
            {"episode_id": "E1_constraints", "turn_hint": "checkpoint_soft"},
            {"episode_id": "E2_noise_history", "turn_hint": "checkpoint_soft"},
            {"episode_id": "E3_state_update", "turn_hint": "checkpoint_hard"},
            {"episode_id": "E5_conflict", "turn_hint": "checkpoint_hard"},
            {"episode_id": "E6_final_pre_task", "turn_hint": "checkpoint_final"},
        ],
    }


def main() -> None:
    task_files = sorted(TASKS_DIR.glob("*/*.md"))
    count = 0

    for tf in task_files:
        meta = _read_frontmatter(tf)
        if not meta:
            continue
        task_id = str(meta.get("id", tf.stem))
        category = str(meta.get("category", tf.parent.name))
        ws = _workspace_path(meta, tf)
        ws.mkdir(parents=True, exist_ok=True)

        scenario_path = ws / "scenario.jsonl"
        oracle_path = ws / "oracle.yaml"

        turns = _build_turns(task_id, category)
        scenario_lines = [json.dumps(t, ensure_ascii=False) for t in turns]
        scenario_path.write_text("\n".join(scenario_lines) + "\n", encoding="utf-8")

        oracle = _build_oracle(task_id, category)
        oracle_path.write_text(yaml.safe_dump(oracle, sort_keys=False, allow_unicode=True), encoding="utf-8")

        count += 1

    print(f"Generated long-context scenario/oracle for {count} tasks.")


if __name__ == "__main__":
    main()
