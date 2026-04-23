"""Mem0 baseline - memory system with entity extraction and semantic search.

This baseline simulates Mem0's approach:
1. Extract facts/entities from conversations
2. Deduplicate and update facts
3. Retrieve relevant facts based on semantic similarity
"""

from __future__ import annotations

import re
from typing import Any
from collections import defaultdict

from baselines.base import BaseBaseline, BaselineResult


class Mem0Baseline(BaseBaseline):
    """Mem0-style memory baseline with fact extraction and retrieval.

    Mem0 extracts facts from conversations, maintains them in a structured
    format, and retrieves relevant facts based on the current query.

    Pros:
        - Structured fact storage
        - Automatic deduplication
        - Semantic retrieval
        - Good for state tracking

    Cons:
        - May lose procedural flow
        - Fact extraction can miss implicit information
        - No episode structure preservation
    """

    def __init__(
        self,
        budget_chars: int = 12000,
        max_facts_per_type: int = 20,
        fact_extraction_keywords: bool = True,
    ):
        """Initialize Mem0 baseline.

        Args:
            budget_chars: Target character budget
            max_facts_per_type: Maximum facts to keep per category
            fact_extraction_keywords: Use keyword-based fact extraction
        """
        super().__init__(budget_chars)
        self.max_facts_per_type = max_facts_per_type
        self.fact_extraction_keywords = fact_extraction_keywords

        # Fact categories (simulating Mem0's structured memory)
        self.facts = defaultdict(list)

    def _extract_facts(self, text: str) -> dict[str, list[str]]:
        """Extract structured facts from text.

        Returns categories:
        - preferences: User preferences and requirements
        - facts: General factual information
        - procedures: Steps and processes
        - constraints: Rules and limitations
        - errors: Mistakes and their resolutions
        """
        facts = {
            "preferences": [],
            "facts": [],
            "procedures": [],
            "constraints": [],
            "errors": [],
        }

        lines = text.splitlines()

        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue

            line_lower = line.lower()

            # Preference patterns
            if any(p in line_lower for p in ["prefer", "want", "would like", "require"]):
                facts["preferences"].append(line)

            # Constraint patterns
            elif any(c in line_lower for c in ["must", "should", "required", "constraint", "only", "never"]):
                facts["constraints"].append(line)

            # Procedure patterns
            elif any(p in line_lower for p in ["step", "first", "then", "finally", "procedure", "workflow"]):
                facts["procedures"].append(line)

            # Error patterns
            elif any(e in line_lower for e in ["error", "failed", "mistake", "wrong", "fix", "resolved"]):
                facts["errors"].append(line)

            # General facts (with version/state info)
            elif any(f in line_lower for f in ["version", "state", "update", "current", "latest"]):
                facts["facts"].append(line)

        return facts

    def _deduplicate_facts(self, facts: list[str]) -> list[str]:
        """Remove duplicate/similar facts."""
        if not facts:
            return []

        # Simple deduplication based on shared words
        unique_facts = []
        for fact in facts:
            is_duplicate = False
            fact_words = set(fact.lower().split())

            for existing in unique_facts:
                existing_words = set(existing.lower().split())
                # If high overlap, consider duplicate
                if len(fact_words & existing_words) / max(len(fact_words), 1) > 0.7:
                    # Keep the more detailed one
                    if len(fact) > len(existing):
                        unique_facts.remove(existing)
                        unique_facts.append(fact)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_facts.append(fact)

        return unique_facts

    def _score_fact_relevance(self, fact: str, query: str) -> float:
        """Score relevance of a fact to the query."""
        fact_lower = fact.lower()
        query_lower = query.lower()

        # Word overlap score
        fact_words = set(fact_lower.split())
        query_words = set(query_lower.split())

        if not fact_words or not query_words:
            return 0.0

        overlap = len(fact_words & query_words)
        score = overlap / max(len(query_words), 1)

        # Boost for constraint-related facts
        constraint_keywords = {"must", "should", "required", "constraint", "schema", "format"}
        if any(kw in fact_lower for kw in constraint_keywords):
            score *= 1.2

        return score

    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Apply Mem0-style memory compression.

        Strategy:
        1. Extract facts from all content
        2. Categorize and deduplicate
        3. Score relevance to task
        4. Include most relevant facts within budget
        """
        # Extract facts from all sources
        all_facts = defaultdict(list)

        # Facts from workspace files
        for path, content in workspace_files:
            file_facts = self._extract_facts(content)
            for category, facts in file_facts.items():
                all_facts[category].extend(facts)

        # Facts from scenario turns
        for turn in scenario_turns:
            content = turn.get("content", "")
            turn_facts = self._extract_facts(content)
            for category, facts in turn_facts.items():
                # Add episode context
                ep_id = turn.get("episode_id", "")
                annotated_facts = [f"[{ep_id}] {f}" for f in facts] if ep_id else facts
                all_facts[category].extend(annotated_facts)

        # Deduplicate facts per category
        for category in all_facts:
            all_facts[category] = self._deduplicate_facts(all_facts[category])
            # Limit per category
            all_facts[category] = all_facts[category][-self.max_facts_per_type:]

        # Build memory context
        # Priority: constraints > preferences > procedures > errors > facts
        priority_order = ["constraints", "preferences", "procedures", "errors", "facts"]

        budget_remaining = self.budget_chars - len(task_prompt) - 300
        result_parts: list[str] = []

        # Add facts by priority
        facts_included = {cat: 0 for cat in priority_order}

        for category in priority_order:
            facts = all_facts.get(category, [])
            if not facts:
                continue

            category_header = f"=== {category.upper()} ==="
            category_text = category_header + "\n"

            included = []
            for fact in facts:
                # Score relevance if task prompt is available
                if task_prompt:
                    relevance = self._score_fact_relevance(fact, task_prompt)
                    # Skip low-relevance facts if budget is tight
                    if relevance < 0.1 and budget_remaining < 2000:
                        continue

                new_text = category_text + "\n".join(included + [f"• {fact}"])
                if len(new_text) <= budget_remaining * 0.4:  # Reserve budget for other categories
                    included.append(f"• {fact}")
                    facts_included[category] += 1
                else:
                    break

            if included:
                result_parts.append(f"{category_header}\n" + "\n".join(included))
                budget_remaining -= len(result_parts[-1]) + 2

        # Add recent raw context if there's budget (simulating Mem0's recent context window)
        if budget_remaining > 1000 and scenario_turns:
            recent_turns = scenario_turns[-3:]  # Last 3 turns
            recent_text = "=== RECENT CONTEXT ===\n"
            for turn in recent_turns:
                role = turn.get("role", "user")
                content = turn.get("content", "")[:200]  # Truncate each turn
                recent_text += f"[{role}] {content}\n"

            if len(recent_text) <= budget_remaining:
                result_parts.append(recent_text)

        # Add task prompt
        if task_prompt:
            result_parts.append(f"=== CURRENT TASK ===\n{task_prompt}")

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
            method="mem0",
            metadata={
                "num_workspace_files": len(workspace_files),
                "num_scenario_turns": len(scenario_turns),
                "max_facts_per_type": self.max_facts_per_type,
            },
            retrieval_stats={
                "facts_extracted": {cat: len(all_facts[cat]) for cat in priority_order},
                "facts_included": facts_included,
            },
        )
