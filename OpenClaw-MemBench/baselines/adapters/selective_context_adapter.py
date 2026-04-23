"""Selective Context adapter - Self-information based prompt compression.

Repository: https://github.com/liyucheng09/Selective_Context
Paper: "Compressing Context to Enhance Inference Efficiency of Large Language Models" (EMNLP'23)
PyPI: selective-context

Installation:
    pip install selective-context
    python -m spacy download en_core_web_sm

Requirements:
    - spacy
    - transformers
    - torch

This adapter wraps the official Selective Context library to provide
a unified interface for OpenClaw-MemBench baseline comparison.
"""

from __future__ import annotations

from typing import Any

from baselines.base import BaseBaseline, BaselineResult


class SelectiveContextAdapter(BaseBaseline):
    """Selective Context prompt compression baseline.

    Selective Context uses self-information (from a small LM like GPT-2)
    to evaluate the informativeness of each lexical unit (sentence,
    phrase, or token), then filters out less informative content based
    on a specified compression ratio.

    Key features:
    - Self-information based filtering (information theory grounded)
    - Three granularity levels: sentence, phrase, token
    - 2x context window expansion capability
    - Language-agnostic (supports EN and ZH)

    References:
        - Paper: https://arxiv.org/abs/2309.07338 (EMNLP'23)
        - Code: https://github.com/liyucheng09/Selective_Context
    """

    def __init__(
        self,
        budget_chars: int = 12000,
        model_type: str = "gpt2",
        lang: str = "en",
        granularity: str = "sentence",  # "sentence", "phrase", or "token"
    ):
        """Initialize Selective Context adapter.

        Args:
            budget_chars: Target character budget
            model_type: Base model for computing self-information ("gpt2", "gpt-neo", etc.)
            lang: Language code ("en" for English, "zh" for Chinese)
            granularity: Compression granularity ("sentence", "phrase", or "token")
        """
        super().__init__(budget_chars)
        self.model_type = model_type
        self.lang = lang
        self.granularity = granularity

        # Import here to allow graceful fallback
        try:
            from selective_context import SelectiveContext

            self._compressor = SelectiveContext(
                model_type=model_type,
                lang=lang,
            )
        except ImportError:
            raise ImportError(
                "Selective Context not installed.\n"
                "Install with: pip install selective-context\n"
                "Then download spacy model: python -m spacy download en_core_web_sm"
            )

    def _calculate_reduce_ratio(self, text: str) -> float:
        """Calculate reduction ratio to hit target budget."""
        if len(text) <= self.budget_chars:
            return 0.0
        # Calculate ratio needed to reach budget
        return min(0.95, 1.0 - (self.budget_chars / len(text)))

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Compress context using Selective Context.

        Strategy:
        1. Merge all context into a single text
        2. Calculate required reduction ratio to hit budget
        3. Use Selective Context to filter by self-information
        4. Return compressed result with statistics

        Args:
            workspace_files: List of (path, content) tuples
            scenario_turns: List of scenario conversation turns
            task_prompt: Final task instruction

        Returns:
            BaselineResult with compressed context
        """
        # Build full context
        context_parts: list[str] = []

        # Add workspace files
        for path, content in workspace_files:
            context_parts.append(f"=== {path} ===\n{content}")

        # Add scenario turns
        if scenario_turns:
            turn_texts = []
            for turn in scenario_turns:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                ep_id = turn.get("episode_id", "")
                prefix = f"[{ep_id}] " if ep_id else ""
                turn_texts.append(f"{prefix}[{role}] {content}")
            context_parts.append("=== Conversation ===\n" + "\n".join(turn_texts))

        # Combine all context (excluding task prompt for now)
        full_context = "\n\n".join(context_parts)
        raw_chars = len(full_context)

        # Add task prompt to know what to preserve context for
        if task_prompt:
            # Append task prompt to guide compression
            input_text = f"{full_context}\n\nQuestion: {task_prompt}"
        else:
            input_text = full_context

        # Calculate target reduction ratio
        # Reserve space for task prompt in final output
        task_chars = len(task_prompt) if task_prompt else 0
        available_budget = self.budget_chars - task_chars - 100  # buffer

        reduce_ratio = self._calculate_reduce_ratio(input_text)

        if reduce_ratio <= 0:
            # No compression needed
            final_context = input_text
            compressed_chars = len(final_context)
            reduction_ratio = 0.0
            kept_sentences = []
            reduced_sentences = []
        else:
            try:
                # Use Selective Context to compress
                compressed_context, reduced_content = self._compressor(
                    input_text,
                    reduce_ratio=reduce_ratio,
                )

                # Parse reduced content to get statistics
                if isinstance(reduced_content, list):
                    reduced_sentences = reduced_content
                elif isinstance(reduced_content, str):
                    reduced_sentences = reduced_content.split("\n")
                else:
                    reduced_sentences = []

                # Add task prompt back
                if task_prompt:
                    final_context = f"{compressed_context}\n\n=== TASK ===\n{task_prompt}"
                else:
                    final_context = compressed_context

                compressed_chars = len(final_context)
                reduction_ratio = (
                    (raw_chars - compressed_chars) / raw_chars if raw_chars > 0 else 0.0
                )

            except Exception as e:
                # Fallback: return uncompressed with error
                final_context = input_text
                compressed_chars = len(final_context)
                reduction_ratio = 0.0
                reduced_sentences = []
                return BaselineResult(
                    context=final_context,
                    raw_chars=raw_chars,
                    compressed_chars=compressed_chars,
                    reduction_ratio=reduction_ratio,
                    method="selective-context",
                    metadata={
                        "error": str(e),
                        "model_type": self.model_type,
                        "reduce_ratio_requested": reduce_ratio,
                    },
                )

        return BaselineResult(
            context=final_context,
            raw_chars=raw_chars,
            compressed_chars=compressed_chars,
            reduction_ratio=round(reduction_ratio, 4),
            method="selective-context",
            metadata={
                "model_type": self.model_type,
                "lang": self.lang,
                "granularity": self.granularity,
                "reduce_ratio": reduce_ratio,
                "num_workspace_files": len(workspace_files),
                "num_scenario_turns": len(scenario_turns),
                "num_reduced_sentences": len(reduced_sentences),
            },
            retrieval_stats={
                "reduced_sentences": reduced_sentences[:20],  # Limit for size
            },
        )

    def __repr__(self) -> str:
        return (
            f"SelectiveContextAdapter("
            f"model='{self.model_type}', "
            f"budget={self.budget_chars}, "
            f"granularity='{self.granularity}'"
            f")"
        )
