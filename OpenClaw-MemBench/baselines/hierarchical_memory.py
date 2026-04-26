"""Hierarchical Memory baseline - maintains multiple memory tiers.

This baseline simulates a hierarchical memory system with:
- Working memory: recent, high-fidelity content
- Short-term memory: summarized recent episodes
- Long-term memory: highly compressed old episodes
"""

from __future__ import annotations

from typing import Any

from baselines.base import BaseBaseline, BaselineResult, Episode


class HierarchicalMemoryBaseline(BaseBaseline):
    """Hierarchical memory with multiple tiers.

    This baseline organizes memory into tiers:
    - Working: Most recent episode (full fidelity)
    - Short-term: Previous 2-3 episodes (moderate compression)
    - Long-term: Older episodes (heavy compression to key facts)

    Pros:
        - Preserves recent information at high fidelity
        - Older information is not lost, just compressed
        - Mimics human memory organization

    Cons:
        - Requires tuning of tier boundaries
        - May lose procedural details in long-term tier
        - Fixed allocation may not match task needs
    """

    def __init__(
        self,
        budget_chars: int = 12000,
        working_memory_ratio: float = 0.4,
        short_term_ratio: float = 0.35,
        long_term_ratio: float = 0.25,
        short_term_episodes: int = 2,
    ):
        """Initialize hierarchical memory baseline.

        Args:
            budget_chars: Total character budget
            working_memory_ratio: Budget portion for working memory (latest episode)
            short_term_ratio: Budget portion for short-term memory
            long_term_ratio: Budget portion for long-term memory
            short_term_episodes: Number of episodes in short-term memory
        """
        super().__init__(budget_chars)
        self.working_memory_ratio = working_memory_ratio
        self.short_term_ratio = short_term_ratio
        self.long_term_ratio = long_term_ratio
        self.short_term_episodes = short_term_episodes

        # Calculate actual budgets
        self.working_budget = int(budget_chars * working_memory_ratio)
        self.short_term_budget = int(budget_chars * short_term_ratio)
        self.long_term_budget = int(budget_chars * long_term_ratio)

    def _compress_to_key_facts(self, text: str, max_chars: int) -> str:
        """Compress text to key facts only."""
        lines = text.splitlines()
        key_facts: list[str] = []

        # Keywords indicating important facts
        fact_keywords = {
            "version", "schema", "constraint", "must", "required",
            "output", "path", "format", "error", "success", "failed",
            "decision", "rule", "policy", "config",
        }

        for line in lines:
            line_lower = line.lower()
            # Keep lines with fact keywords
            if any(kw in line_lower for kw in fact_keywords):
                # Clean up the line
                clean = line.strip()
                if clean and len(clean) > 5:
                    key_facts.append(f"- {clean}")

        result = "\n".join(key_facts)
        if len(result) > max_chars:
            result = result[:max_chars].rsplit("\n", 1)[0]

        return result if result else text[:max_chars]

    def _summarize_for_short_term(self, text: str, max_chars: int) -> str:
        """Moderate compression for short-term memory."""
        lines = text.splitlines()

        # Keep first few lines (context)
        kept: list[str] = []
        current_len = 0

        # Always keep first line
        if lines:
            kept.append(lines[0])
            current_len = len(lines[0])

        # Keep lines with important content
        important_keywords = self._extract_constraint_keywords()
        for line in lines[1:]:
            if current_len + len(line) > max_chars:
                break
            line_lower = line.lower()
            if any(kw in line_lower for kw in important_keywords):
                kept.append(line)
                current_len += len(line) + 1

        # Add last line if there's room
        if len(lines) > 1 and lines[-1] not in kept:
            if current_len + len(lines[-1]) <= max_chars:
                kept.append(lines[-1])

        return "\n".join(kept)

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Apply hierarchical memory compression.

        Strategy:
        1. Group turns into episodes
        2. Assign episodes to memory tiers
        3. Apply tier-appropriate compression
        4. Combine with task prompt
        """
        # Group turns by episode
        episodes = self._group_turns_by_episode(scenario_turns)

        if not episodes:
            # No episodes, just include workspace files
            result_parts = [f"[FILE: {p}]\n{c[:self.budget_chars//len(workspace_files)]}"
                          for p, c in workspace_files]
            if task_prompt:
                result_parts.append(f"[TASK]\n{task_prompt}")
            compressed = "\n\n".join(result_parts)
            raw_chars = sum(len(c) for _, c in workspace_files)
            return BaselineResult(
                context=compressed,
                raw_chars=raw_chars,
                compressed_chars=len(compressed),
                reduction_ratio=round(1 - len(compressed)/max(1, raw_chars), 4),
                method="hierarchical-memory",
                metadata={"num_episodes": 0},
            )

        result_parts: list[str] = []
        remaining_budget = self.budget_chars - len(task_prompt) - 300

        # Working Memory: Latest episode (full or lightly compressed)
        latest_episode = episodes[-1]
        working_text = latest_episode.to_text()

        if len(working_text) > self.working_budget:
            working_text = working_text[-self.working_budget:]

        result_parts.append(f"=== WORKING MEMORY (Latest Episode: {latest_episode.episode_id}) ===\n{working_text}")
        remaining_budget -= len(result_parts[-1])

        # Short-term Memory: Previous N episodes (moderate compression)
        short_term_episodes = episodes[-(self.short_term_episodes + 1):-1]
        if short_term_episodes:
            short_term_parts: list[str] = []
            budget_per_episode = self.short_term_budget // max(1, len(short_term_episodes))

            for ep in short_term_episodes:
                ep_text = ep.to_text()
                compressed = self._summarize_for_short_term(ep_text, budget_per_episode)
                short_term_parts.append(f"[{ep.episode_id}] {compressed}")

            short_term_text = "\n\n".join(short_term_parts)
            if len(short_term_text) > self.short_term_budget:
                short_term_text = short_term_text[:self.short_term_budget]

            result_parts.append(f"=== SHORT-TERM MEMORY ===\n{short_term_text}")
            remaining_budget -= len(result_parts[-1])

        # Long-term Memory: Older episodes (heavy compression to key facts)
        long_term_episodes = episodes[:-(self.short_term_episodes + 1)]
        if long_term_episodes:
            # Combine all old episodes and extract key facts
            old_content = "\n".join(ep.to_text() for ep in long_term_episodes)
            key_facts = self._compress_to_key_facts(old_content, self.long_term_budget)

            if key_facts:
                result_parts.append(f"=== LONG-TERM MEMORY (Key Facts) ===\n{key_facts}")
                remaining_budget -= len(result_parts[-1])

        # Add workspace files if there's budget
        if workspace_files and remaining_budget > 500:
            file_budget = min(remaining_budget - 100, self.budget_chars * 0.15)
            budget_per_file = int(file_budget / len(workspace_files))

            file_parts: list[str] = []
            for path, content in workspace_files:
                if len(content) > budget_per_file:
                    content = content[:budget_per_file] + "..."
                file_parts.append(f"[FILE: {path}]\n{content}")

            result_parts.append("=== WORKSPACE FILES ===\n" + "\n\n".join(file_parts))

        # Add task prompt
        if task_prompt:
            result_parts.append(f"=== TASK ===\n{task_prompt}")

        compressed = "\n\n".join(result_parts)

        # Calculate statistics
        raw_chars = sum(len(ep.to_text()) for ep in episodes)
        raw_chars += sum(len(c) for _, c in workspace_files)
        compressed_chars = len(compressed)
        reduction_ratio = round(1 - compressed_chars / max(1, raw_chars), 4)

        return BaselineResult(
            context=compressed,
            raw_chars=raw_chars,
            compressed_chars=compressed_chars,
            reduction_ratio=reduction_ratio,
            method="hierarchical-memory",
            metadata={
                "num_episodes": len(episodes),
                "num_workspace_files": len(workspace_files),
                "working_memory_ratio": self.working_memory_ratio,
                "short_term_ratio": self.short_term_ratio,
                "long_term_ratio": self.long_term_ratio,
                "tiers_used": ["working"] +
                            (["short_term"] if short_term_episodes else []) +
                            (["long_term"] if long_term_episodes else []),
            },
            retrieval_stats={
                "episodes_in_working": 1,
                "episodes_in_short_term": len(short_term_episodes),
                "episodes_in_long_term": len(long_term_episodes),
            },
        )
