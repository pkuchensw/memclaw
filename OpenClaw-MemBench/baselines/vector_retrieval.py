"""Vector Retrieval baseline - semantic search over conversation chunks.

This baseline simulates a vector store approach:
1. Chunk conversations into segments
2. Compute embeddings (simulated with keyword overlap)
3. Retrieve most relevant chunks based on query similarity
"""

from __future__ import annotations

import math
from typing import Any
from collections import Counter

from baselines.base import BaseBaseline, BaselineResult


class VectorRetrievalBaseline(BaseBaseline):
    """Vector store retrieval baseline using semantic similarity.

    This baseline:
    1. Chunks content into segments
    2. Creates term-frequency vectors (simulating embeddings)
    3. Retrieves top-k most similar chunks to the task query

    Pros:
        - Semantic retrieval (content-based)
        - Query-adaptive
        - Good for finding relevant context

    Cons:
        - No episode structure preservation
        - Requires good query representation
        - May miss implicit relationships
    """

    def __init__(
        self,
        budget_chars: int = 12000,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        top_k_chunks: int = 10,
        use_tfidf: bool = True,
        max_chunks: int = 50,  # 限制最大块数，防止内存爆炸
    ):
        """Initialize vector retrieval baseline.

        Args:
            budget_chars: Target character budget
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks
            top_k_chunks: Number of top chunks to retrieve
            use_tfidf: Use TF-IDF weighting (vs simple term frequency)
            max_chunks: Maximum number of chunks to process (memory limit)
        """
        super().__init__(budget_chars)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k_chunks = top_k_chunks
        self.use_tfidf = use_tfidf
        self.max_chunks = max_chunks

        # Document frequency for TF-IDF
        self.doc_frequency: dict[str, int] = {}
        self.total_docs = 0

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        # Lowercase and extract words
        words = []
        current = ""
        for char in text.lower():
            if char.isalnum():
                current += char
            else:
                if current:
                    words.append(current)
                    current = ""
        if current:
            words.append(current)
        return words

    def _create_vector(self, text: str) -> dict[str, float]:
        """Create term frequency vector for text."""
        tokens = self._tokenize(text)
        if not tokens:
            return {}

        tf = Counter(tokens)
        vector = {}

        for term, count in tf.items():
            term_freq = count / len(tokens)

            if self.use_tfidf and self.doc_frequency:
                # TF-IDF weighting
                idf = math.log(
                    (self.total_docs + 1) / (self.doc_frequency.get(term, 0) + 1)
                ) + 1
                vector[term] = term_freq * idf
            else:
                vector[term] = term_freq

        return vector

    def _cosine_similarity(self, vec1: dict[str, float], vec2: dict[str, float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0

        # Dot product
        dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in set(vec1) & set(vec2))

        # Magnitudes
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def _chunk_text(self, text: str, source: str) -> list[dict[str, Any]]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0

        while start < len(text) and len(chunks) < self.max_chunks:
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]

            # Try to break at a sentence boundary
            if end < len(text):
                for punct in ['. ', '! ', '? ', '\n']:
                    last_punct = chunk_text.rfind(punct)
                    if last_punct > self.chunk_size * 0.5:
                        chunk_text = chunk_text[:last_punct + 1]
                        end = start + len(chunk_text)
                        break

            chunks.append({
                'text': chunk_text,
                'source': source,
                'start': start,
                'end': end,
            })

            start += self.chunk_size - self.chunk_overlap

        return chunks

    def _build_corpus(self, chunks: list[dict[str, Any]]) -> None:
        """Build document frequency statistics for TF-IDF."""
        self.doc_frequency = {}
        self.total_docs = len(chunks)

        for chunk in chunks:
            tokens = set(self._tokenize(chunk['text']))
            for token in tokens:
                self.doc_frequency[token] = self.doc_frequency.get(token, 0) + 1

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Apply vector retrieval compression.

        Strategy:
        1. Chunk all content into segments
        2. Build TF-IDF vectors
        3. Compute query vector
        4. Retrieve top-k most similar chunks
        5. Combine into final context
        """
        # Create chunks from all sources
        all_chunks: list[dict[str, Any]] = []

        # Chunks from workspace files
        for path, content in workspace_files:
            file_chunks = self._chunk_text(content, f"file:{path}")
            all_chunks.extend(file_chunks)

        # Chunks from scenario turns
        for turn in scenario_turns:
            content = turn.get("content", "")
            ep_id = turn.get("episode_id", "")
            role = turn.get("role", "user")
            source = f"episode:{ep_id}:{role}" if ep_id else f"turn:{role}"
            turn_chunks = self._chunk_text(content, source)
            all_chunks.extend(turn_chunks)

        if not all_chunks:
            # No content to retrieve from
            compressed = f"[TASK]\n{task_prompt}" if task_prompt else ""
            return BaselineResult(
                context=compressed,
                raw_chars=0,
                compressed_chars=len(compressed),
                reduction_ratio=0.0,
                method="vector-retrieval",
                metadata={"error": "No content to retrieve from"},
            )

        # Build corpus statistics
        self._build_corpus(all_chunks)

        # Create vectors for all chunks
        for chunk in all_chunks:
            chunk['vector'] = self._create_vector(chunk['text'])

        # Create query vector
        query_vector = self._create_vector(task_prompt)

        # Score all chunks by similarity to query
        for chunk in all_chunks:
            chunk['score'] = self._cosine_similarity(chunk['vector'], query_vector)

        # Sort by score and retrieve top-k
        all_chunks.sort(key=lambda x: x['score'], reverse=True)

        # Select chunks within budget
        budget_remaining = self.budget_chars - len(task_prompt) - 200
        selected_chunks: list[dict[str, Any]] = []

        for chunk in all_chunks[:self.top_k_chunks]:
            if len(chunk['text']) <= budget_remaining:
                selected_chunks.append(chunk)
                budget_remaining -= len(chunk['text']) + 50  # Account for metadata
            else:
                # Try to take partial chunk
                if budget_remaining > 100:
                    partial = chunk['text'][:budget_remaining - 50]
                    selected_chunks.append({
                        **chunk,
                        'text': partial + "...",
                        'truncated': True,
                    })
                break

        # Build output
        result_parts: list[str] = []

        # Add selected chunks with metadata
        for i, chunk in enumerate(selected_chunks, 1):
            header = f"[CHUNK {i} | {chunk['source']} | score={chunk['score']:.3f}]"
            result_parts.append(f"{header}\n{chunk['text']}")

        # Add task prompt
        if task_prompt:
            result_parts.append(f"[TASK QUERY]\n{task_prompt}")

        compressed = "\n\n".join(result_parts)

        # Calculate statistics
        raw_chars = sum(len(c) for _, c in workspace_files)
        raw_chars += sum(len(t.get("content", "")) for t in scenario_turns)
        compressed_chars = len(compressed)
        reduction_ratio = round(1 - compressed_chars / max(1, raw_chars), 4)

        return BaselineResult(
            context=compressed,
            raw_chars=raw_chars,
            compressed_chars=compressed_chars,
            reduction_ratio=reduction_ratio,
            method="vector-retrieval",
            metadata={
                "num_workspace_files": len(workspace_files),
                "num_scenario_turns": len(scenario_turns),
                "total_chunks": len(all_chunks),
                "chunks_selected": len(selected_chunks),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "top_k": self.top_k_chunks,
                "use_tfidf": self.use_tfidf,
            },
            retrieval_stats={
                "retrieval_scores": [c['score'] for c in selected_chunks],
                "avg_retrieval_score": sum(c['score'] for c in selected_chunks) / max(1, len(selected_chunks)),
            },
        )
