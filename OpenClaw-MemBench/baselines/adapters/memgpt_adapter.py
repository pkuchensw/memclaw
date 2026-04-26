"""MemGPT adapter - Memory-GPT for unbounded context.

Repository: https://github.com/cpacker/MemGPT
Paper: "MemGPT: Towards LLMs as Operating Systems" (arXiv:2310.08560)
PyPI: pip install memgpt (or pip install letta for newer versions)

Installation:
    pip install memgpt
    # Or for newer versions:
    pip install letta

Requirements:
    - memgpt or letta
    - transformers, torch (for embeddings)
    - Vector database (ChromaDB, Qdrant, or SQLite fallback)

MemGPT treats LLM context like virtual memory in an OS:
- Main context (working memory): Limited size, fast access
- External context: Larger storage, slower retrieval
- Memory management functions: search, recall, archive

This adapter simulates MemGPT's tiered memory architecture for context compression.

References:
    - Paper: https://arxiv.org/abs/2310.08560
    - Code: https://github.com/cpacker/MemGPT
    - Docs: https://memgpt.readme.io
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field

from baselines.base import BaseBaseline, BaselineResult


@dataclass
class MemoryTier:
    """Represents a memory tier in MemGPT architecture."""
    name: str
    max_size: int
    content: list[str] = field(default_factory=list)
    priority: int = 0

    def add(self, content: str, priority: int = 0) -> bool:
        """Add content if within budget."""
        if self.current_size + len(content) <= self.max_size:
            self.content.append((content, priority))
            return True
        return False

    def get_content(self) -> str:
        """Get all content sorted by priority."""
        sorted_content = sorted(self.content, key=lambda x: x[1], reverse=True)
        return "\n".join([c[0] for c in sorted_content])

    @property
    def current_size(self) -> int:
        return sum(len(c[0]) for c in self.content)


class MemGPTAdapter(BaseBaseline):
    """MemGPT memory-tier baseline.

    MemGPT treats LLM context as virtual memory with multiple tiers:
    1. Working Memory (Main Context): ~8K chars, always available
    2. Recall Memory: Recent important information
    3. Archival Memory: Long-term storage, retrieved on demand

    Key features:
    - FIFO eviction with importance weighting
    - Self-editing memory pages
    - OS-inspired memory management functions
    - Multi-level retrieval strategy

    This adapter implements a simplified tiered memory system inspired by MemGPT.

    References:
        - Paper: https://arxiv.org/abs/2310.08560
        - Code: https://github.com/cpacker/MemGPT
    """

    # Memory tier sizes (in characters)
    DEFAULT_WORKING_MEMORY_SIZE = 4000  # Core context
    DEFAULT_RECALL_MEMORY_SIZE = 5000   # Recent important info
    DEFAULT_ARCHIVAL_MEMORY_SIZE = 3000 # Long-term (searchable)

    # Importance scoring keywords
    HIGH_PRIORITY_KEYWORDS = [
        "must", "required", "constraint", "exactly", "only",
        "never", "always", "final", "checkpoint_hard", "checkpoint_final"
    ]
    MEDIUM_PRIORITY_KEYWORDS = [
        "should", "correction", "update", "version",
        "checkpoint_soft", "exclude", "include"
    ]

    def __init__(
        self,
        budget_chars: int = 12000,
        working_memory_ratio: float = 0.35,
        recall_memory_ratio: float = 0.40,
        use_vector_search: bool = False,
        embedding_model: str | None = None,
    ):
        """Initialize MemGPT adapter.

        Args:
            budget_chars: Total character budget across all tiers
            working_memory_ratio: % of budget for working memory
            recall_memory_ratio: % of budget for recall memory
            use_vector_search: Whether to use semantic search for archival
            embedding_model: Model for embeddings (if vector search enabled)
        """
        super().__init__(budget_chars)
        self.working_memory_ratio = working_memory_ratio
        self.recall_memory_ratio = recall_memory_ratio
        self.use_vector_search = use_vector_search
        self.embedding_model = embedding_model

        # Calculate tier sizes
        self.working_size = int(budget_chars * working_memory_ratio)
        self.recall_size = int(budget_chars * recall_memory_ratio)
        self.archival_size = budget_chars - self.working_size - self.recall_size - 500  # Buffer

        # Try to import MemGPT/Letta library
        self._memgpt_available = False
        self._letta_available = False
        try:
            import memgpt
            self._memgpt = memgpt
            self._memgpt_available = True
        except ImportError:
            pass

        try:
            import letta
            self._letta = letta
            self._letta_available = True
        except ImportError:
            pass

        # Initialize simple embedding if vector search requested
        if use_vector_search:
            self._init_embedding_model()

    def _init_embedding_model(self):
        """Initialize embedding model for semantic search."""
        self._embedding_model = None
        try:
            from sentence_transformers import SentenceTransformer
            model_name = self.embedding_model or "all-MiniLM-L6-v2"
            self._embedding_model = SentenceTransformer(model_name)
        except ImportError:
            pass  # Fall back to keyword search

    def _calculate_importance(self, text: str, hint: str = "") -> int:
        """Calculate importance score for content."""
        score = 0
        text_lower = text.lower()
        hint_lower = hint.lower()

        # Check high priority keywords
        for kw in self.HIGH_PRIORITY_KEYWORDS:
            if kw in text_lower or kw in hint_lower:
                score += 10

        # Check medium priority keywords
        for kw in self.MEDIUM_PRIORITY_KEYWORDS:
            if kw in text_lower or kw in hint_lower:
                score += 5

        # Recency boost (will be applied by ordering)
        # Task instructions get high priority
        if "task" in hint_lower or "final" in hint_lower:
            score += 15

        # Conflict markers are important
        if "source" in text_lower and ("conflict" in text_lower or "vs" in text_lower):
            score += 8

        return score

    def _semantic_search(self, query: str, documents: list[str], top_k: int = 5) -> list[int]:
        """Search for relevant documents using embeddings."""
        if self._embedding_model is None or not documents:
            # Fall back to keyword search
            return self._keyword_search(query, documents, top_k)

        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity

            # Encode query and documents
            query_embedding = self._embedding_model.encode([query])
            doc_embeddings = self._embedding_model.encode(documents)

            # Calculate similarities
            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]

            # Get top-k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            return top_indices.tolist()
        except Exception:
            return self._keyword_search(query, documents, top_k)

    def _keyword_search(self, query: str, documents: list[str], top_k: int = 5) -> list[int]:
        """Fallback keyword-based search."""
        query_words = set(query.lower().split())
        scores = []

        for i, doc in enumerate(documents):
            doc_words = set(doc.lower().split())
            overlap = len(query_words & doc_words)
            scores.append((i, overlap))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in scores[:top_k]]

    def _compress_with_tiers(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str,
    ) -> tuple[str, dict[str, Any]]:
        """Compress using MemGPT-style tiered memory."""
        # Initialize memory tiers
        working_memory = MemoryTier("working", self.working_size)
        recall_memory = MemoryTier("recall", self.recall_size)
        archival_memory = MemoryTier("archival", self.archival_size)

        # Sort turns by turn_id for chronological processing
        sorted_turns = sorted(scenario_turns, key=lambda t: t.get("turn_id", 0))

        # 1. Identify high-priority content for working memory
        high_priority_content = []

        # Task prompt always goes to working memory
        if task_prompt:
            high_priority_content.append((f"=== TASK ===\n{task_prompt}", 100))

        # Recent turns with high importance
        recent_turns = sorted_turns[-3:] if len(sorted_turns) >= 3 else sorted_turns
        for turn in recent_turns:
            content = turn.get("content", "")
            hint = turn.get("compression_hint", "")
            ep_id = turn.get("episode_id", "")
            role = turn.get("role", "user")
            importance = self._calculate_importance(content, hint)

            if importance >= 10 or hint in ["checkpoint_hard", "checkpoint_final"]:
                prefix = f"[{ep_id}] " if ep_id else ""
                formatted = f"{prefix}[{role}] {content}"
                high_priority_content.append((formatted, importance))

        # Constraint-related files to working memory
        for path, content in workspace_files:
            if any(kw in path.lower() for kw in ["constraint", "final", "oracle", "checkpoint"]):
                importance = 20
                high_priority_content.append(
                    (f"=== {path} ===\n{content[:1500]}", importance)
                )

        # Fill working memory (sorted by importance)
        high_priority_content.sort(key=lambda x: x[1], reverse=True)
        for content, priority in high_priority_content:
            if not working_memory.add(content, priority):
                break

        # 2. Fill recall memory with remaining recent content
        recall_candidates = []
        for turn in sorted_turns:
            if turn not in recent_turns:  # Skip already processed
                content = turn.get("content", "")
                hint = turn.get("compression_hint", "")
                ep_id = turn.get("episode_id", "")
                role = turn.get("role", "user")
                importance = self._calculate_importance(content, hint)

                if importance >= 5:
                    prefix = f"[{ep_id}] " if ep_id else ""
                    formatted = f"{prefix}[{role}] {content[:500]}"
                    recall_candidates.append((formatted, importance))

        # Add important workspace files to recall
        for path, content in workspace_files:
            if not any(kw in path.lower() for kw in ["constraint", "final", "oracle"]):
                key_facts = self._extract_key_facts(content)
                if key_facts:
                    recall_candidates.append(
                        (f"=== {path} ===\n{key_facts}", 5)
                    )

        recall_candidates.sort(key=lambda x: x[1], reverse=True)
        for content, priority in recall_candidates:
            if not recall_memory.add(content, priority):
                break

        # 3. Fill archival memory with summarized older content
        archival_docs = []
        old_turns = sorted_turns[:-5] if len(sorted_turns) > 5 else []
        for turn in old_turns:
            content = turn.get("content", "")
            ep_id = turn.get("episode_id", "")
            role = turn.get("role", "user")

            # Create summary
            if len(content) > 100:
                summary = content[:100] + " [...]"
            else:
                summary = content

            archival_docs.append(f"[{ep_id}] [{role}] {summary}")

        archival_text = "\n".join(archival_docs)
        if archival_text:
            archival_memory.add(archival_text, 1)

        # 4. Search archival memory if task prompt provided
        if task_prompt and self.use_vector_search and archival_docs:
            relevant_indices = self._semantic_search(task_prompt, archival_docs, top_k=3)
            retrieved = [archival_docs[i] for i in relevant_indices if i < len(archival_docs)]
            if retrieved:
                archival_memory.content = [("\n".join(retrieved), 10)]

        # 5. Build final context
        parts = []

        working_content = working_memory.get_content()
        if working_content:
            parts.append(working_content)

        recall_content = recall_memory.get_content()
        if recall_content:
            parts.append(f"=== RECALL MEMORY ===\n{recall_content}")

        archival_content = archival_memory.get_content()
        if archival_content:
            parts.append(f"=== ARCHIVAL MEMORY ===\n{archival_content}")

        compressed = "\n\n".join(parts)

        # Ensure we don't exceed budget
        if len(compressed) > self.budget_chars:
            compressed = compressed[:self.budget_chars]

        metadata = {
            "working_memory_used": working_memory.current_size,
            "recall_memory_used": recall_memory.current_size,
            "archival_memory_used": archival_memory.current_size,
            "working_memory_limit": self.working_size,
            "recall_memory_limit": self.recall_size,
            "archival_memory_limit": self.archival_size,
            "num_files": len(workspace_files),
            "num_turns": len(scenario_turns),
        }

        return compressed, metadata

    def _extract_key_facts(self, text: str) -> str:
        """Extract key facts from text."""
        lines = text.split("\n")
        key_lines = []

        constraint_keywords = [
            "constraint", "must", "should", "required", "schema",
            "output", "path", "format", "version", "year"
        ]

        for line in lines[:50]:  # First 50 lines
            line_lower = line.lower().strip()
            if any(kw in line_lower for kw in constraint_keywords):
                key_lines.append(line)
            elif ":" in line and len(line) < 150:
                key_lines.append(line)

        return "\n".join(key_lines[:20])  # Limit to 20 lines

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Compress context using MemGPT tiered memory.

        Strategy:
        1. Working Memory: Task + high-priority recent content
        2. Recall Memory: Important historical content
        3. Archival Memory: Summarized old content, searchable

        Args:
            workspace_files: List of (path, content) tuples
            scenario_turns: List of scenario conversation turns
            task_prompt: Final task instruction

        Returns:
            BaselineResult with tiered compressed context
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

        # Use MemGPT tiered compression
        compressed_context, metadata = self._compress_with_tiers(
            workspace_files, scenario_turns, task_prompt
        )

        compressed_chars = len(compressed_context)
        reduction_ratio = (raw_chars - compressed_chars) / raw_chars if raw_chars > 0 else 0.0

        tokens_used = {
            "original_tokens": raw_chars // 4,
            "compressed_tokens": compressed_chars // 4,
        }

        return BaselineResult(
            context=compressed_context,
            raw_chars=raw_chars,
            compressed_chars=compressed_chars,
            reduction_ratio=round(reduction_ratio, 4),
            method="memgpt",
            metadata={
                **metadata,
                "memgpt_lib_available": self._memgpt_available,
                "letta_lib_available": self._letta_available,
                "use_vector_search": self.use_vector_search,
            },
            tokens_used=tokens_used,
        )

    def __repr__(self) -> str:
        return (
            f"MemGPTAdapter("
            f"budget={self.budget_chars}, "
            f"working={self.working_size}, "
            f"recall={self.recall_size}, "
            f"vector_search={self.use_vector_search}"
            f")"
        )
