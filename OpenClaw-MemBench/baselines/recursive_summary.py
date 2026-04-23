"""Recursive Summarization baseline - hierarchical summarization of episodes.

This baseline uses an LLM to recursively summarize episodes, creating
a hierarchical summary structure similar to LCM but with simpler heuristics.
"""

from __future__ import annotations

from typing import Any

from baselines.base import BaseBaseline, BaselineResult, Episode


class RecursiveSummarizationBaseline(BaseBaseline):
    """Hierarchical recursive summarization baseline.

    This baseline organizes content into episodes, summarizes each episode,
    and then recursively summarizes groups of episode summaries.

    Pros:
        - Preserves hierarchical structure
        - Can capture episode-level semantics
        - Natural fit for multi-episode scenarios

    Cons:
        - Requires LLM calls for summarization (or uses simple heuristics)
        - May lose fine-grained details
        - Computationally more expensive
    """

    def __init__(
        self,
        budget_chars: int = 12000,
        episode_summary_length: int = 200,
        use_simple_heuristic: bool = True,
        preserve_latest_episode: bool = True,
    ):
        """Initialize recursive summarization baseline.

        Args:
            budget_chars: Target character budget
            episode_summary_length: Target length for individual episode summaries
            use_simple_heuristic: If True, use rule-based summarization instead of LLM
            preserve_latest_episode: If True, keep the latest episode in full
        """
        super().__init__(budget_chars)
        self.episode_summary_length = episode_summary_length
        self.use_simple_heuristic = use_simple_heuristic
        self.preserve_latest_episode = preserve_latest_episode

    def _simple_summarize(self, text: str, max_length: int) -> str:
        """Create a simple extractive summary.

        Strategy:
        1. Extract first sentence (often contains key info)
        2. Extract sentences with keywords
        3. Extract last sentence (often contains conclusions)
        """
        import re

        sentences = re.split(r'(?<=[.!?])\s+', text)
        if not sentences:
            return text[:max_length]

        # Keep first sentence
        summary_sentences = [sentences[0]]
        current_length = len(sentences[0])

        # Keep sentences with keywords
        keywords = self._extract_constraint_keywords()
        for sent in sentences[1:-1]:
            if current_length + len(sent) > max_length:
                break
            sent_lower = sent.lower()
            if any(kw in sent_lower for kw in keywords):
                summary_sentences.append(sent)
                current_length += len(sent) + 1

        # Add last sentence if there's room
        if sentences[-1] not in summary_sentences:
            if current_length + len(sentences[-1]) <= max_length:
                summary_sentences.append(sentences[-1])

        return " ".join(summary_sentences)[:max_length]

    def _summarize_episode(self, episode: Episode) -> str:
        """Summarize a single episode."""
        text = episode.to_text()

        if len(text) <= self.episode_summary_length:
            return text

        if self.use_simple_heuristic:
            return self._simple_summarize(text, self.episode_summary_length)

        # In a full implementation, this would call an LLM
        return self._simple_summarize(text, self.episode_summary_length)

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Apply recursive summarization.

        Strategy:
        1. Group turns into episodes
        2. Summarize older episodes
        3. Keep latest episode in full (if configured)
        4. Add workspace files as "file episodes"
        """
        # Group turns by episode
        episodes = self._group_turns_by_episode(scenario_turns)

        # Create summaries for each episode
        episode_summaries: list[tuple[str, str, bool]] = []  # (id, summary, is_full)

        for i, episode in enumerate(episodes):
            is_latest = (i == len(episodes) - 1)

            if is_latest and self.preserve_latest_episode:
                # Keep latest episode in full
                summary = episode.to_text()
                episode_summaries.append((episode.episode_id, summary, True))
            else:
                # Summarize older episodes
                summary = self._summarize_episode(episode)
                episode_summaries.append((episode.episode_id, summary, False))

        # Add workspace files as special episodes
        for path, content in workspace_files:
            if len(content) > self.episode_summary_length:
                summary = self._simple_summarize(content, self.episode_summary_length)
            else:
                summary = content
            episode_summaries.append((f"file:{path}", summary, len(content) <= self.episode_summary_length))

        # Build final context within budget
        budget_remaining = self.budget_chars - len(task_prompt) - 200
        result_parts: list[str] = []

        # Always include latest episode in full if it fits
        if episode_summaries:
            latest_id, latest_summary, is_full = episode_summaries[-1]
            if not latest_id.startswith("file:"):
                header = f"=== Episode: {latest_id} (FULL) ===" if is_full else f"=== Episode: {latest_id} (SUMMARY) ==="
                full_text = f"{header}\n{latest_summary}"
                if len(full_text) <= budget_remaining:
                    result_parts.append(full_text)
                    budget_remaining -= len(full_text) + 2
                    episode_summaries = episode_summaries[:-1]  # Remove from list

        # Add other episodes (newer first)
        for ep_id, summary, is_full in reversed(episode_summaries):
            header = f"=== Episode: {ep_id} (FULL) ===" if is_full else f"=== Episode: {ep_id} (SUMMARY) ==="
            part_text = f"{header}\n{summary}"

            if len(part_text) <= budget_remaining:
                result_parts.append(part_text)
                budget_remaining -= len(part_text) + 2
            else:
                # Try to add truncated version
                available = max(0, budget_remaining - len(header) - 1)
                if available > 50:
                    truncated = summary[:available]
                    result_parts.append(f"{header}\n{truncated}...")
                break

        # Add task prompt
        if task_prompt:
            result_parts.append(f"=== TASK ===\n{task_prompt}")

        compressed = "\n\n".join(result_parts)

        # Calculate statistics
        raw_parts: list[str] = []
        for ep in episodes:
            raw_parts.append(ep.to_text())
        for path, content in workspace_files:
            raw_parts.append(f"[FILE: {path}]\n{content}")
        raw_context = "\n\n".join(raw_parts)
        raw_chars = len(raw_context)
        compressed_chars = len(compressed)
        reduction_ratio = (
            round(1.0 - compressed_chars / raw_chars, 4) if raw_chars > 0 else 0.0
        )

        return BaselineResult(
            context=compressed,
            raw_chars=raw_chars,
            compressed_chars=compressed_chars,
            reduction_ratio=reduction_ratio,
            method="recursive-summary",
            metadata={
                "num_episodes": len(episodes),
                "num_workspace_files": len(workspace_files),
                "episode_summary_length": self.episode_summary_length,
                "latest_episode_preserved": self.preserve_latest_episode,
            },
            retrieval_stats={
                "summarized_episodes": sum(1 for _, _, is_full in episode_summaries if not is_full),
                "full_episodes": sum(1 for _, _, is_full in episode_summaries if is_full),
            },
        )
