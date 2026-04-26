"""Mem0 adapter - AI memory layer for agents.

Repository: https://github.com/mem0ai/mem0
Paper: "Mem0: Building production-ready AI agents with scalable long-term memory"
PyPI: mem0ai

Installation:
    pip install mem0ai

Optional dependencies (for vector stores):
    pip install chromadb  # or qdrant-client, pinecone-client

Requirements:
    - mem0ai
    - Vector database (Chroma, Qdrant, or Pinecone)
    - OpenAI API key or other LLM provider

This adapter wraps the official Mem0 library to provide
a unified interface for OpenClaw-MemBench baseline comparison.

Note: Mem0 is designed for multi-turn conversation memory, so this adapter
simulates using it for context compression by extracting memories from
scenario history and using them as compressed context.
"""

from __future__ import annotations

from typing import Any

from baselines.base import BaseBaseline, BaselineResult


class Mem0Adapter(BaseBaseline):
    """Mem0 memory-based context compression baseline.

    Mem0 extracts facts, preferences, and entities from conversations
    and stores them in a hybrid architecture (vector + graph + KV store).
    This adapter uses Mem0 to extract memories from the scenario history,
    then uses those memories as the compressed context.

    Key features:
    - Hybrid storage (vector + graph + key-value)
    - Automatic fact extraction and deduplication
    - Cross-session persistence
    - Multi-level memory (user, session, agent)

    References:
        - Paper: arXiv:2504.19413
        - Code: https://github.com/mem0ai/mem0
        - Docs: https://docs.mem0.ai
    """

    def __init__(
        self,
        budget_chars: int = 12000,
        vector_store: str = "chroma",  # "chroma", "qdrant", "pinecone"
        user_id: str = "test_user",
        agent_id: str = "test_agent",
        search_limit: int = 50,
    ):
        """Initialize Mem0 adapter.

        Args:
            budget_chars: Target character budget
            vector_store: Vector database backend
            user_id: User identifier for memory isolation
            agent_id: Agent identifier
            search_limit: Maximum memories to retrieve
        """
        super().__init__(budget_chars)
        self.vector_store = vector_store
        self.user_id = user_id
        self.agent_id = agent_id
        self.search_limit = search_limit

        # Import here to allow graceful fallback
        try:
            from mem0 import Memory

            # Configure Mem0 based on vector store choice
            config = self._build_config()
            self._memory = Memory.from_config(config)

        except ImportError:
            raise ImportError(
                "Mem0 not installed. Install with: pip install mem0ai\n"
                "Also install vector store: pip install chromadb (or qdrant-client)"
            )
        except Exception as e:
            # Mem0 might fail if no API key or DB connection
            raise RuntimeError(
                f"Failed to initialize Mem0: {e}\n"
                "Make sure you have:\n"
                "1. OpenAI API key set (OPENAI_API_KEY)\n"
                "2. Vector database running (if using Qdrant/Pinecone)"
            )

    def _build_config(self) -> dict:
        """Build Mem0 configuration."""
        config = {
            "vector_store": {
                "provider": self.vector_store,
                "config": {
                    "collection_name": "openclaw_membench",
                },
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.0,
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                },
            },
        }

        # Vector store specific config
        if self.vector_store == "chroma":
            config["vector_store"]["config"]["path"] = "/tmp/mem0_chroma"
        elif self.vector_store == "qdrant":
            config["vector_store"]["config"]["host"] = "localhost"
            config["vector_store"]["config"]["port"] = 6333

        return config

    def _extract_memories_from_text(self, text: str) -> list[dict]:
        """Extract memories from text using Mem0."""
        try:
            # Add to memory and get extracted facts
            result = self._memory.add(
                text,
                user_id=self.user_id,
                agent_id=self.agent_id,
                metadata={"source": "scenario"},
            )
            return result if isinstance(result, list) else []
        except Exception:
            return []

    def _search_relevant_memories(self, query: str) -> list[dict]:
        """Search for relevant memories."""
        try:
            results = self._memory.search(
                query=query,
                user_id=self.user_id,
                agent_id=self.agent_id,
                limit=self.search_limit,
            )
            return results if isinstance(results, list) else []
        except Exception:
            return []

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Compress context using Mem0 memory extraction.

        Strategy:
        1. Extract memories from workspace files and scenario turns
        2. Store in Mem0 memory system
        3. Search for memories relevant to task prompt
        4. Use retrieved memories as compressed context

        Args:
            workspace_files: List of (path, content) tuples
            scenario_turns: List of scenario conversation turns
            task_prompt: Final task instruction

        Returns:
            BaselineResult with compressed context (retrieved memories)
        """
        # Clear previous memories (for clean state)
        try:
            self._memory.delete_all(user_id=self.user_id)
        except Exception:
            pass

        # Build raw context for statistics
        context_parts: list[str] = []
        for path, content in workspace_files:
            context_parts.append(f"=== {path} ===\n{content}")

        turn_texts = []
        for turn in scenario_turns:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            turn_texts.append(f"[{role}] {content}")
        if turn_texts:
            context_parts.append("=== Conversation ===\n" + "\n".join(turn_texts))

        full_context = "\n\n".join(context_parts)
        raw_chars = len(full_context)

        # Extract memories from all content
        all_memories: list[dict] = []

        # Extract from workspace files
        for path, content in workspace_files:
            memories = self._extract_memories_from_text(f"File {path}: {content}")
            all_memories.extend(memories)

        # Extract from scenario turns
        for turn in scenario_turns:
            content = turn.get("content", "")
            if content:
                memories = self._extract_memories_from_text(content)
                all_memories.extend(memories)

        # Search for relevant memories
        search_query = task_prompt if task_prompt else "current task"
        relevant_memories = self._search_relevant_memories(search_query)

        # Build compressed context from memories
        memory_texts: list[str] = []

        # Add retrieved memories
        for mem in relevant_memories:
            if isinstance(mem, dict):
                memory_text = mem.get("memory", "")
                if memory_text:
                    memory_texts.append(f"- {memory_text}")

        # If no memories retrieved, use raw context (fallback)
        if not memory_texts:
            compressed_context = full_context[:self.budget_chars]
        else:
            # Combine memories within budget
            memory_section = "\n".join(memory_texts)
            if len(memory_section) > self.budget_chars:
                memory_section = memory_section[:self.budget_chars]
            compressed_context = f"=== EXTRACTED MEMORIES ===\n{memory_section}"

        # Add task prompt
        if task_prompt:
            final_context = f"{compressed_context}\n\n=== TASK ===\n{task_prompt}"
        else:
            final_context = compressed_context

        compressed_chars = len(final_context)
        reduction_ratio = (
            (raw_chars - compressed_chars) / raw_chars if raw_chars > 0 else 0.0
        )

        return BaselineResult(
            context=final_context,
            raw_chars=raw_chars,
            compressed_chars=compressed_chars,
            reduction_ratio=round(reduction_ratio, 4),
            method="mem0-lib",
            metadata={
                "vector_store": self.vector_store,
                "user_id": self.user_id,
                "agent_id": self.agent_id,
                "num_workspace_files": len(workspace_files),
                "num_scenario_turns": len(scenario_turns),
                "memories_extracted": len(all_memories),
                "memories_retrieved": len(relevant_memories),
            },
            retrieval_stats={
                "memories": [
                    m.get("memory", "") for m in relevant_memories[:10]
                ],  # Limit for size
            },
        )

    def __repr__(self) -> str:
        return (
            f"Mem0Adapter("
            f"store='{self.vector_store}', "
            f"budget={self.budget_chars}, "
            f"user='{self.user_id}'"
            f")"
        )
