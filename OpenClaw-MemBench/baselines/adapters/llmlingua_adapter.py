"""LLMLingua adapter - Microsoft prompt compression library.

Repository: https://github.com/microsoft/LLMLingua
Paper: "LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models" (EMNLP'23, ACL'24)

Installation:
    pip install llmlingua

Requirements:
    - transformers
    - torch (GPU recommended for speed)

This adapter wraps the official Microsoft LLMLingua library to provide
a unified interface for OpenClaw-MemBench baseline comparison.
"""

from __future__ import annotations

from typing import Any

from baselines.base import BaseBaseline, BaselineResult


class LLMLinguaAdapter(BaseBaseline):
    """LLMLingua prompt compression baseline.

    LLMLingua uses a smaller language model (e.g., GPT-2, Phi-2, LLaMA-7B)
    to compress prompts by removing non-essential tokens while preserving
    semantic meaning and key information.

    Key features:
    - Up to 20x compression ratio
    - Task-agnostic compression (LLMLingua-2)
    - Budget controller for token allocation
    - Iterative token-level compression

    References:
        - Paper: https://arxiv.org/abs/2310.05736 (EMNLP'23)
        - Paper: https://arxiv.org/abs/2403.12968 (ACL'24 - LLMLingua-2)
        - Code: https://github.com/microsoft/LLMLingua
    """

    # Default model choices (from smallest to largest)
    MODEL_OPTIONS = {
        "gpt2": "gpt2",  # Smallest, fastest
        "phi-2": "microsoft/phi-2",  # Good balance
        "llama-7b": "meta-llama/Llama-2-7b-hf",  # Larger, better quality
        "phi-3": "microsoft/Phi-3-mini-4k-instruct",  # Latest small model
    }

    def __init__(
        self,
        budget_chars: int = 12000,
        model_name: str = "microsoft/phi-2",
        use_llmlingua2: bool = False,
        rate: float = 0.5,  # Target compression ratio (0-1)
        force_tokens: list[str] | None = None,
        drop_consecutive: bool = True,
    ):
        """Initialize LLMLingua adapter.

        Args:
            budget_chars: Target character budget (converted to tokens)
            model_name: Compressor model to use
            use_llmlingua2: Use LLMLingua-2 (faster, task-agnostic)
            rate: Target compression ratio (0.5 = 50% reduction)
            force_tokens: Tokens to always preserve
            drop_consecutive: Whether to drop consecutive tokens
        """
        super().__init__(budget_chars)
        self.model_name = model_name
        self.use_llmlingua2 = use_llmlingua2
        self.rate = rate
        self.force_tokens = force_tokens or ["?", "important", "key"]
        self.drop_consecutive = drop_consecutive

        # Import here to allow graceful fallback if not installed
        try:
            from llmlingua import PromptCompressor

            self._compressor = PromptCompressor(
                model_name=model_name,
                use_llmlingua2=use_llmlingua2,
            )
        except ImportError:
            raise ImportError(
                "LLMLingua not installed. Install with: pip install llmlingua\n"
                "For GPU support, also install: pip install torch"
            )

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation for character budget conversion."""
        # Approximate: 1 token ≈ 4 characters for English
        return len(text) // 4

    def _chars_to_tokens(self, chars: int) -> int:
        """Convert character budget to token budget."""
        return chars // 4

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Compress context using LLMLingua.

        Strategy:
        1. Merge all context into a single prompt
        2. Use LLMLingua to compress to target token budget
        3. Return compressed result with statistics

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

        # Combine all context (excluding task prompt)
        full_context = "\n\n".join(context_parts)
        raw_chars = len(full_context)
        raw_tokens = self._estimate_tokens(full_context)

        # Calculate target tokens
        # Reserve space for task prompt
        task_tokens = self._estimate_tokens(task_prompt)
        target_tokens = max(
            self._chars_to_tokens(self.budget_chars) - task_tokens,
            100  # Minimum tokens
        )

        # Use LLMLingua to compress
        try:
            compression_result = self._compressor.compress_prompt(
                prompt=full_context,
                instruction="",  # No additional instruction
                question=task_prompt,  # Question to preserve context for
                target_token=target_tokens,
                rate=self.rate,
                force_tokens=self.force_tokens,
                drop_consecutive=self.drop_consecutive,
            )

            compressed_context = compression_result["compressed_prompt"]
            compressed_tokens = compression_result.get("compressed_tokens", 0)
            original_tokens = compression_result.get("original_tokens", raw_tokens)

            # Add task prompt
            if task_prompt:
                final_context = f"{compressed_context}\n\n=== TASK ===\n{task_prompt}"
            else:
                final_context = compressed_context

            compressed_chars = len(final_context)

            # Calculate reduction
            reduction_ratio = (
                (raw_chars - compressed_chars) / raw_chars if raw_chars > 0 else 0.0
            )

            return BaselineResult(
                context=final_context,
                raw_chars=raw_chars,
                compressed_chars=compressed_chars,
                reduction_ratio=round(reduction_ratio, 4),
                method="llmlingua",
                metadata={
                    "model_name": self.model_name,
                    "use_llmlingua2": self.use_llmlingua2,
                    "target_rate": self.rate,
                    "original_tokens": original_tokens,
                    "compressed_tokens": compressed_tokens,
                    "token_reduction_ratio": (
                        (original_tokens - compressed_tokens) / original_tokens
                        if original_tokens > 0
                        else 0.0
                    ),
                    "num_workspace_files": len(workspace_files),
                    "num_scenario_turns": len(scenario_turns),
                },
                tokens_used={
                    "original_tokens": original_tokens,
                    "compressed_tokens": compressed_tokens,
                },
            )

        except Exception as e:
            # Fallback: return uncompressed with error
            return BaselineResult(
                context=full_context + (f"\n\n=== TASK ===\n{task_prompt}" if task_prompt else ""),
                raw_chars=raw_chars,
                compressed_chars=len(full_context),
                reduction_ratio=0.0,
                method="llmlingua",
                metadata={
                    "error": str(e),
                    "model_name": self.model_name,
                },
            )

    def __repr__(self) -> str:
        return (
            f"LLMLinguaAdapter("
            f"model='{self.model_name}', "
            f"budget={self.budget_chars}, "
            f"rate={self.rate}"
            f")"
        )
