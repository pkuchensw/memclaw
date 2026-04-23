"""Keyword Extraction baseline - keeps lines containing important keywords."""

from __future__ import annotations

from typing import Any

from baselines.base import BaseBaseline, BaselineResult


class KeywordExtractBaseline(BaseBaseline):
    """Keyword-based extraction that keeps lines with important signals.

    This baseline extracts lines containing keywords that are likely
    to indicate constraints, requirements, or important information.

    Pros:
        - Fast, rule-based
        - Preserves constraint-related content
        - Good signal-to-noise ratio

    Cons:
        - Keyword list is manually curated
        - No semantic understanding
        - May miss implicit constraints
    """

    DEFAULT_KEYWORDS = {
        # Constraints and requirements
        "constraint", "must", "should", "required", "requirement",
        "exactly", "only", "never", "always", "strict",
        # Version and state
        "version", "latest", "update", "deprecated", "superseded",
        "state", "schema", "format",
        # Actions and outputs
        "output", "path", "save", "export", "write",
        "csv", "json", "file", "directory",
        # Task structure
        "episode", "step", "procedure", "workflow",
        # Error and conflict
        "error", "conflict", "evidence", "resolution",
        # Memory signals
        "resume", "interrupt", "checkpoint", "stale",
        # Time and versioning
        "year", "date", "time", "version", "v1", "v2", "v3",
    }

    def __init__(
        self,
        budget_chars: int = 12000,
        keywords: set[str] | None = None,
        min_line_length: int = 10,
        keep_context_lines: int = 1,
    ):
        """Initialize keyword extraction baseline.

        Args:
            budget_chars: Target character budget
            keywords: Custom keyword set (uses DEFAULT_KEYWORDS if None)
            min_line_length: Minimum line length to consider
            keep_context_lines: Number of context lines around matches to keep
        """
        super().__init__(budget_chars)
        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self.min_line_length = min_line_length
        self.keep_context_lines = keep_context_lines

    def _extract_keyword_lines(self, text: str) -> list[str]:
        """Extract lines containing keywords plus surrounding context."""
        lines = text.splitlines()
        kept_indices: set[int] = set()

        for i, line in enumerate(lines):
            if len(line.strip()) < self.min_line_length:
                continue
            line_lower = line.lower()
            if any(kw in line_lower for kw in self.keywords):
                # Keep this line and surrounding context
                for j in range(
                    max(0, i - self.keep_context_lines),
                    min(len(lines), i + self.keep_context_lines + 1)
                ):
                    kept_indices.add(j)

        return [lines[i] for i in sorted(kept_indices)]

    def _score_line_importance(self, line: str) -> float:
        """Score a line by how many keywords it contains."""
        line_lower = line.lower()
        matches = sum(1 for kw in self.keywords if kw in line_lower)
        # Normalize by line length to avoid bias toward long lines
        length_factor = min(1.0, len(line) / 200)
        return matches * (0.5 + 0.5 * length_factor)

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Apply keyword extraction compression.

        Strategy:
        1. Extract lines containing keywords from all content
        2. Score lines by keyword density
        3. If still over budget, keep highest-scoring lines
        4. Add task prompt at the end (always preserved)
        """
        # Process workspace files
        extracted_parts: list[tuple[str, list[str], float]] = []

        for path, content in workspace_files:
            lines = self._extract_keyword_lines(content)
            if lines:
                score = sum(self._score_line_importance(line) for line in lines)
                extracted_parts.append((f"[FILE: {path}]", lines, score))

        # Process scenario turns
        scenario_lines: list[str] = []
        for turn in scenario_turns:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            ep_id = turn.get("episode_id", "")

            # Check if this turn has keywords
            content_lower = content.lower()
            if any(kw in content_lower for kw in self.keywords):
                prefix = f"[{role}]"
                if ep_id:
                    prefix = f"[episode={ep_id}]{prefix}"
                scenario_lines.append(f"{prefix} {content}")

        if scenario_lines:
            extracted_parts.append(
                ("[SCENARIO]", scenario_lines, float(len(scenario_lines)))
            )

        # Sort parts by score (importance)
        extracted_parts.sort(key=lambda x: x[2], reverse=True)

        # Build output within budget
        budget_remaining = self.budget_chars - len(task_prompt) - 100  # buffer
        result_parts: list[str] = []

        for header, lines, _ in extracted_parts:
            part_text = f"{header}\n" + "\n".join(lines)
            if len(part_text) < budget_remaining:
                result_parts.append(part_text)
                budget_remaining -= len(part_text) + 2
            else:
                # Take what fits
                available = max(0, budget_remaining - len(header) - 1)
                if available > 100:
                    truncated = "\n".join(lines)[:available]
                    result_parts.append(f"{header}\n{truncated}")
                break

        # Add task prompt at the end
        if task_prompt:
            result_parts.append(f"[TASK]\n{task_prompt}")

        compressed = "\n\n".join(result_parts)

        # Calculate statistics
        raw_context = "\n\n".join(
            [f"[FILE: {p}]\n{c}" for p, c in workspace_files] +
            [f"[TURN] {t.get('content', '')}" for t in scenario_turns]
        )
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
            method="keyword-extract",
            metadata={
                "num_keywords": len(self.keywords),
                "extracted_parts": len(extracted_parts),
                "num_scenario_turns": len(scenario_turns),
                "num_workspace_files": len(workspace_files),
            },
            retrieval_stats={
                "lines_extracted": sum(len(lines) for _, lines, _ in extracted_parts),
            },
        )
