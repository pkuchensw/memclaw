"""Sliding Window baseline - keeps most recent context up to budget."""

from __future__ import annotations

from typing import Any

from baselines.base import BaseBaseline, BaselineResult


class SlidingWindowBaseline(BaseBaseline):
    """Simple sliding window that keeps the most recent content.

    This is the simplest baseline that truncates context from the beginning,
    keeping only the most recent content up to the character budget.

    Pros:
        - Very fast, no computation overhead
        - Preserves recency naturally

    Cons:
        - Loses important historical constraints
        - No understanding of semantic importance
        - Performs poorly on constraint-tracking tasks
    """

    def __init__(
        self,
        budget_chars: int = 12000,
        preserve_constraints: bool = False,
        window_from_end: bool = True,
    ):
        """Initialize sliding window baseline.

        Args:
            budget_chars: Target character budget
            preserve_constraints: If True, tries to keep constraint-related content
            window_from_end: If True, keeps end of context (most recent), else start
        """
        super().__init__(budget_chars, preserve_constraints=preserve_constraints)
        self.window_from_end = window_from_end

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Apply sliding window compression.

        Strategy:
        1. Concatenate all context
        2. If within budget, return all
        3. If over budget, truncate from the opposite end of the window
        """
        # Build full context
        context_parts: list[str] = []

        # Add workspace files
        for path, content in workspace_files:
            context_parts.append(f"[FILE: {path}]\n{content}")

        # Add scenario turns
        if scenario_turns:
            context_parts.append("\n=== SCENARIO ===")
            for turn in scenario_turns:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                ep_id = turn.get("episode_id", "")
                prefix = f"[{role}]"
                if ep_id:
                    prefix = f"[episode={ep_id}]{prefix}"
                context_parts.append(f"{prefix} {content}")

        # Add task prompt
        if task_prompt:
            context_parts.append(f"\n=== TASK ===\n{task_prompt}")

        full_context = "\n\n".join(context_parts)
        raw_chars = len(full_context)

        # Apply sliding window
        if raw_chars <= self.budget_chars:
            compressed = full_context
        else:
            if self.window_from_end:
                # Keep most recent (end)
                compressed = full_context[-self.budget_chars:]
                # Try to start at a newline for cleaner cut
                if "\n" in compressed[:100]:
                    first_newline = compressed.find("\n")
                    compressed = compressed[first_newline + 1:]
            else:
                # Keep oldest (start)
                compressed = full_context[:self.budget_chars]

        compressed_chars = len(compressed)
        reduction_ratio = (
            round(1.0 - compressed_chars / raw_chars, 4) if raw_chars > 0 else 0.0
        )

        return BaselineResult(
            context=compressed,
            raw_chars=raw_chars,
            compressed_chars=compressed_chars,
            reduction_ratio=reduction_ratio,
            method="sliding-window",
            metadata={
                "window_from_end": self.window_from_end,
                "num_workspace_files": len(workspace_files),
                "num_scenario_turns": len(scenario_turns),
            },
        )
