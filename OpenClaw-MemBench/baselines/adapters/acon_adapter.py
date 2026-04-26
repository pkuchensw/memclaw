"""ACon adapter - Agent Context Optimization from Microsoft.

Repository: https://github.com/microsoft/acon
Paper: "ACon: Optimizing Context Compression for Long-horizon LLM Agents" (ICLR'26)

Installation:
    pip install acon  # If available on PyPI
    # Or from source:
    git clone https://github.com/microsoft/acon.git
    cd acon && pip install -e .

Requirements:
    - transformers
    - torch
    - openai (for LLM-as-optimizer)

ACon uses a gradient-free optimization approach (LLM-as-Optimizer) to refine
natural language compression guidelines, achieving 26-54% memory reduction
while preserving task performance.

This adapter provides a simplified implementation based on ACon's core concepts
when the official library is not available.
"""

from __future__ import annotations

from typing import Any

from baselines.base import BaseBaseline, BaselineResult


class AConAdapter(BaseBaseline):
    """ACon Agent Context Optimization baseline.

    ACon compresses both environment observations and interaction histories
    into concise yet informative condensations using:
    1. Utility Maximization (UT): Fix failures caused by compression
    2. Compression Optimization (CO): Minimize tokens for successful cases

    Key features:
    - Gradient-free optimization using LLM-as-Optimizer
    - Natural language compression guidelines
    - Contrastive task feedback
    - Distillable to smaller models (95%+ accuracy)

    References:
        - Paper: https://arxiv.org/abs/2510.00615
        - Code: https://github.com/microsoft/acon
    """

    # Default compression guidelines (can be optimized)
    DEFAULT_GUIDELINES = """
Compression Guidelines:
1. Preserve all constraints (must, should, required, exactly)
2. Keep the most recent user instructions intact
3. Summarize old tool outputs to key facts only
4. Maintain conflict markers between sources
5. Preserve checkpoint/final hint annotations
"""

    def __init__(
        self,
        budget_chars: int = 12000,
        model_name: str = "gpt-4o-mini",
        use_guideline_optimization: bool = False,
        preserve_recent_turns: int = 3,
    ):
        """Initialize ACon adapter.

        Args:
            budget_chars: Target character budget
            model_name: LLM for optimization (if guidelines enabled)
            use_guideline_optimization: Whether to optimize guidelines (requires API)
            preserve_recent_turns: Number of recent turns to preserve verbatim
        """
        super().__init__(budget_chars)
        self.model_name = model_name
        self.use_guideline_optimization = use_guideline_optimization
        self.preserve_recent_turns = preserve_recent_turns
        self.guidelines = self.DEFAULT_GUIDELINES

        # Try to import official ACon library
        self._acon_available = False
        try:
            import acon
            self._acon = acon
            self._acon_available = True
        except ImportError:
            pass  # Use fallback implementation

        # Import OpenAI if guideline optimization enabled
        if use_guideline_optimization:
            try:
                from openai import OpenAI
                self._client = OpenAI()
            except ImportError:
                raise ImportError(
                    "OpenAI required for guideline optimization. "
                    "Install with: pip install openai"
                )

    def _extract_key_facts(self, text: str) -> str:
        """Extract key facts from text using heuristics."""
        lines = text.split("\n")
        key_lines = []

        constraint_keywords = [
            "must", "should", "required", "constraint", "exactly",
            "only", "never", "always", "latest", "version",
            "exclude", "include", "output", "save to", "format"
        ]

        for line in lines:
            line_lower = line.lower().strip()
            # Keep lines with constraint keywords
            if any(kw in line_lower for kw in constraint_keywords):
                key_lines.append(line)
            # Keep lines with structural markers
            elif any(marker in line for marker in ["===", "---", "[FILE]", "[Episode]"]):
                key_lines.append(line)
            # Keep short factual statements
            elif len(line) < 100 and (":" in line or "=" in line):
                key_lines.append(line)

        return "\n".join(key_lines) if key_lines else text[:500]

    def _summarize_turn(self, turn: dict[str, Any]) -> str:
        """Summarize a single conversation turn."""
        role = turn.get("role", "user")
        content = turn.get("content", "")
        ep_id = turn.get("episode_id", "")
        hint = turn.get("compression_hint", "")

        # Check if this is a constraint-related turn
        is_constraint = any(kw in content.lower() for kw in
                          ["must", "should", "required", "constraint", "correction"])

        if is_constraint:
            # Preserve constraint turns with full content
            prefix = f"[{ep_id}] " if ep_id else ""
            hint_suffix = f" ({hint})" if hint else ""
            return f"{prefix}[{role}] {content}{hint_suffix}"

        # Summarize other turns
        summary = content
        if len(content) > 200:
            # Extract first sentence or first 150 chars
            first_sentence = content.split(".")[0] if "." in content else content[:150]
            summary = first_sentence + " [...]"

        prefix = f"[{ep_id}] " if ep_id else ""
        hint_suffix = f" ({hint})" if hint else ""
        return f"{prefix}[{role}] {summary}{hint_suffix}"

    def _compress_with_guidelines(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str,
    ) -> tuple[str, dict[str, Any]]:
        """Compress context using ACon-style guidelines."""
        parts: list[str] = []

        # 1. Process workspace files - extract key facts
        file_summaries = []
        for path, content in workspace_files:
            # Keep recent/important files more intact
            if any(keyword in path.lower() for keyword in ["constraint", "final", "checkpoint"]):
                file_summaries.append(f"=== {path} ===\n{content[:1000]}")
            else:
                key_facts = self._extract_key_facts(content)
                file_summaries.append(f"=== {path} ===\n{key_facts}")

        # 2. Process scenario turns - progressive summarization
        turn_summaries = []

        # Sort turns by turn_id to ensure chronological order
        sorted_turns = sorted(scenario_turns, key=lambda t: t.get("turn_id", 0))

        # Preserve recent turns verbatim
        recent_turns = sorted_turns[-self.preserve_recent_turns:]
        old_turns = sorted_turns[:-self.preserve_recent_turns] if len(sorted_turns) > self.preserve_recent_turns else []

        # Summarize old turns
        for turn in old_turns:
            summarized = self._summarize_turn(turn)
            turn_summaries.append(summarized)

        # Add recent turns in full
        for turn in recent_turns:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            ep_id = turn.get("episode_id", "")
            hint = turn.get("compression_hint", "")
            prefix = f"[{ep_id}] " if ep_id else ""
            hint_suffix = f" ({hint})" if hint else ""
            turn_summaries.append(f"{prefix}[{role}] {content}{hint_suffix}")

        # 3. Build compressed context
        if file_summaries:
            parts.append("=== WORKSPACE FILES ===\n" + "\n\n".join(file_summaries))

        if turn_summaries:
            parts.append("=== CONVERSATION HISTORY ===\n" + "\n".join(turn_summaries))

        if task_prompt:
            parts.append(f"=== TASK ===\n{task_prompt}")

        compressed = "\n\n".join(parts)

        # Apply budget constraint
        if len(compressed) > self.budget_chars:
            # Prioritize: task > recent turns > workspace > old turns
            if task_prompt:
                task_part = f"=== TASK ===\n{task_prompt}"
                available = self.budget_chars - len(task_part) - 200

                # Keep recent turns, truncate old content
                recent_content = "\n".join(turn_summaries[-self.preserve_recent_turns:])
                available_for_files = available - len(recent_content) - 100

                if available_for_files > 0 and file_summaries:
                    truncated_files = []
                    current_len = 0
                    for fs in file_summaries:
                        if current_len + len(fs) < available_for_files:
                            truncated_files.append(fs)
                            current_len += len(fs) + 2
                        else:
                            break
                    compressed = "\n\n".join([
                        "=== WORKSPACE FILES ===\n" + "\n\n".join(truncated_files),
                        "=== CONVERSATION HISTORY ===\n" + recent_content,
                        task_part
                    ])
                else:
                    compressed = recent_content + "\n\n" + task_part
            else:
                compressed = compressed[:self.budget_chars]

        metadata = {
            "guidelines_used": self.guidelines.strip(),
            "preserve_recent_turns": self.preserve_recent_turns,
            "num_files": len(workspace_files),
            "num_turns": len(scenario_turns),
            "recent_turns_preserved": len(recent_turns),
            "old_turns_summarized": len(old_turns),
        }

        return compressed, metadata

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Compress context using ACon methodology.

        Strategy:
        1. Categorize content by importance (constraints > recent > old)
        2. Preserve critical content verbatim
        3. Summarize less important content
        4. Apply budget constraints intelligently

        Args:
            workspace_files: List of (path, content) tuples
            scenario_turns: List of scenario conversation turns
            task_prompt: Final task instruction

        Returns:
            BaselineResult with compressed context
        """
        # Build raw context for statistics
        raw_parts = []
        for path, content in workspace_files:
            raw_parts.append(f"=== {path} ===\n{content}")
        for turn in scenario_turns:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            raw_parts.append(f"[{role}] {content}")
        if task_prompt:
            raw_parts.append(f"=== TASK ===\n{task_prompt}")

        full_context = "\n\n".join(raw_parts)
        raw_chars = len(full_context)

        # Use ACon compression
        compressed_context, metadata = self._compress_with_guidelines(
            workspace_files, scenario_turns, task_prompt
        )

        compressed_chars = len(compressed_context)
        reduction_ratio = (raw_chars - compressed_chars) / raw_chars if raw_chars > 0 else 0.0

        # Estimate tokens (rough approximation)
        tokens_used = {
            "original_tokens": raw_chars // 4,
            "compressed_tokens": compressed_chars // 4,
        }

        return BaselineResult(
            context=compressed_context,
            raw_chars=raw_chars,
            compressed_chars=compressed_chars,
            reduction_ratio=round(reduction_ratio, 4),
            method="acon",
            metadata={
                **metadata,
                "acon_library_available": self._acon_available,
                "model_name": self.model_name,
                "use_guideline_optimization": self.use_guideline_optimization,
            },
            tokens_used=tokens_used,
        )

    def __repr__(self) -> str:
        return (
            f"AConAdapter("
            f"budget={self.budget_chars}, "
            f"preserve_recent={self.preserve_recent_turns}, "
            f"lib_available={self._acon_available}"
            f")"
        )
