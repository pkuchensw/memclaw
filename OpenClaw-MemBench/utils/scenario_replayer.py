from __future__ import annotations

import json
from pathlib import Path


def load_scenario_turns(scenario_path: str) -> list[dict]:
    """Load JSONL scenario turns.

    Supported keys per row:
    - turn_id: int
    - role: system|user|assistant|tool
    - content: str
    - episode_id: str (optional)
    - compression_hint: str (optional)
    """
    p = Path(scenario_path)
    if not p.exists():
        return []

    turns: list[dict] = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        raw = line.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        role = str(obj.get("role", "user")).strip().lower()
        if role not in {"system", "user", "assistant", "tool"}:
            role = "user"
        turns.append(
            {
                "turn_id": int(obj.get("turn_id", i)),
                "role": role,
                "content": str(obj.get("content", "") or "").strip(),
                "episode_id": str(obj.get("episode_id", "") or "").strip(),
                "compression_hint": str(obj.get("compression_hint", "") or "").strip(),
            }
        )

    turns.sort(key=lambda x: x["turn_id"])
    return turns


def scenario_to_messages(turns: list[dict], include_tool: bool = True) -> list[dict]:
    messages: list[dict] = []
    for t in turns:
        role = t["role"]
        if role == "tool" and not include_tool:
            continue
        content = t["content"]
        if not content:
            continue
        # Keep episode and compression metadata inside content for traceability.
        prefix_parts = []
        if t.get("episode_id"):
            prefix_parts.append(f"episode={t['episode_id']}")
        if t.get("compression_hint"):
            prefix_parts.append(f"compression_hint={t['compression_hint']}")
        if prefix_parts:
            content = f"[{'; '.join(prefix_parts)}]\n{content}"
        mapped_role = "assistant" if role == "tool" else role
        messages.append({"role": mapped_role, "content": content})
    return messages


def compression_events(turns: list[dict]) -> list[dict]:
    events: list[dict] = []
    for t in turns:
        hint = t.get("compression_hint", "")
        if hint:
            events.append(
                {
                    "turn_id": t.get("turn_id", 0),
                    "episode_id": t.get("episode_id", ""),
                    "hint": hint,
                }
            )
    return events
