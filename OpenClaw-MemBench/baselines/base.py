"""Base class for memory management baselines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BaselineResult:
    """Result of baseline context processing.

    Attributes:
        context: The processed context string to be sent to the model
        raw_chars: Original context size in characters
        compressed_chars: Final context size in characters
        reduction_ratio: Proportion of context removed (0.0 to 1.0)
        method: Name of the baseline method used
        metadata: Additional method-specific information
        tokens_used: Token usage statistics if available
        retrieval_stats: Statistics about memory retrieval operations
    """

    context: str
    raw_chars: int
    compressed_chars: int
    reduction_ratio: float
    method: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tokens_used: dict[str, int] = field(default_factory=dict)
    retrieval_stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "context": self.context,
            "raw_chars": self.raw_chars,
            "compressed_chars": self.compressed_chars,
            "reduction_ratio": self.reduction_ratio,
            "method": self.method,
            "metadata": self.metadata,
            "tokens_used": self.tokens_used,
            "retrieval_stats": self.retrieval_stats,
        }


@dataclass
class Episode:
    """Represents an episode in the scenario.

    Attributes:
        episode_id: Unique identifier for the episode
        turns: List of conversation turns in this episode
        metadata: Additional episode metadata
    """

    episode_id: str
    turns: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_text(self) -> str:
        """Convert episode to text representation."""
        lines = [f"=== Episode: {self.episode_id} ==="]
        for turn in self.turns:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            lines.append(f"[{role}] {content}")
        return "\n".join(lines)


class BaseBaseline(ABC):
    """Abstract base class for memory management baselines.

    All baselines must implement the `compress` method which takes
    workspace content and scenario turns and returns compressed context.
    """

    def __init__(
        self,
        budget_chars: int = 12000,
        budget_tokens: int | None = None,
        preserve_constraints: bool = True,
    ):
        """Initialize baseline.

        Args:
            budget_chars: Target character budget for compressed context
            budget_tokens: Target token budget (if None, derived from chars)
            preserve_constraints: Whether to try preserving constraint-related content
        """
        self.budget_chars = budget_chars
        self.budget_tokens = budget_tokens or (budget_chars // 4)
        self.preserve_constraints = preserve_constraints
        self.name = self.__class__.__name__.replace("Baseline", "").lower()

    @abstractmethod
    def compress(
        self,
        workspace_files: list[tuple[str, str]],
        scenario_turns: list[dict[str, Any]],
        task_prompt: str = "",
    ) -> BaselineResult:
        """Compress context using this baseline method.

        Args:
            workspace_files: List of (path, content) tuples from workspace
            scenario_turns: List of scenario turns with role, content, etc.
            task_prompt: The final task prompt to be executed

        Returns:
            BaselineResult with compressed context and statistics
        """
        pass

    def _group_turns_by_episode(
        self, turns: list[dict[str, Any]]
    ) -> list[Episode]:
        """Group scenario turns by episode_id."""
        episodes: dict[str, Episode] = {}
        for turn in turns:
            ep_id = turn.get("episode_id", "default")
            if ep_id not in episodes:
                episodes[ep_id] = Episode(episode_id=ep_id)
            episodes[ep_id].turns.append(turn)

        # Sort by first turn_id in each episode
        return sorted(episodes.values(), key=lambda e: e.turns[0].get("turn_id", 0))

    def _load_workspace_text(self, workspace_path: str | Path) -> list[tuple[str, str]]:
        """Load text files from workspace.

        Returns list of (relative_path, content) tuples.
        """
        ws = Path(workspace_path)
        files: list[tuple[str, str]] = []
        text_extensions = {
            ".txt", ".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".log",
            ".py", ".js", ".ts", ".html", ".css", ".sh", ".xml", ".toml",
        }

        for subdir in ["episodes", "evidence"]:
            folder = ws / subdir
            if not folder.exists():
                continue
            for filepath in sorted(folder.rglob("*")):
                if not filepath.is_file():
                    continue
                if filepath.suffix.lower() not in text_extensions:
                    continue
                try:
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    rel_path = str(filepath.relative_to(ws))
                    files.append((rel_path, content))
                except Exception:
                    continue

        return files

    def _extract_constraint_keywords(self) -> set[str]:
        """Extract keywords that likely indicate constraints."""
        return {
            "must", "should", "required", "constraint", "exactly",
            "only", "never", "always", "latest", "version",
            "schema", "path", "output", "format", "year",
        }

    def _is_constraint_related(self, text: str) -> bool:
        """Check if text contains constraint-related keywords."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self._extract_constraint_keywords())

    def _simple_token_estimate(self, text: str) -> int:
        """Rough token estimate (chars / 4 is a common approximation)."""
        return len(text) // 4

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(budget_chars={self.budget_chars})"
