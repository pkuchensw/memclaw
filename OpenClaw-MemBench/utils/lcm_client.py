"""OpenClaw LCM (Lossless Context Management) API Client.

This module provides integration with the OpenClaw LCM service for
intelligent context compression and memory management.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass
class LCMConfig:
    """Configuration for LCM API connection."""

    base_url: str
    api_key: str | None = None
    timeout: int = 60
    verify_ssl: bool = True
    default_budget_chars: int = 12000

    @classmethod
    def from_env(cls) -> "LCMConfig":
        """Create config from environment variables."""
        return cls(
            base_url=os.environ.get("OPENCLAW_LCM_BASE_URL", "http://127.0.0.1:18790"),
            api_key=os.environ.get("OPENCLAW_LCM_API_KEY") or None,
            timeout=int(os.environ.get("OPENCLAW_LCM_TIMEOUT", "60")),
            verify_ssl=os.environ.get("OPENCLAW_VERIFY_SSL", "true").lower() in {"1", "true", "yes"},
            default_budget_chars=int(os.environ.get("OPENCLAW_CONTEXT_BUDGET_CHARS", "12000")),
        )


@dataclass
class CompressionResult:
    """Result of LCM compression operation."""

    method: str
    raw_chars: int
    compressed_chars: int
    reduction_ratio: float
    context: str
    metadata: dict[str, Any]
    compression_events: list[dict]
    layer_info: dict[str, Any] | None = None


class LCMClient:
    """Client for OpenClaw LCM API."""

    def __init__(self, config: LCMConfig | None = None):
        self.config = config or LCMConfig.from_env()
        self.session = requests.Session()
        if self.config.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.config.api_key}"
        self.session.headers["Content-Type"] = "application/json"

    def _make_request(self, endpoint: str, payload: dict) -> dict:
        """Make HTTP request to LCM API."""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            error_body = e.response.text if e.response else ""
            raise LCMError(f"LCM API error: {e}\nResponse: {error_body}") from e
        except requests.RequestException as e:
            raise LCMError(f"LCM request failed: {e}") from e

    def compress_context(
        self,
        text: str,
        method: str = "lcm",
        budget_chars: int | None = None,
        scenario_turns: list[dict] | None = None,
        skill_hints: list[str] | None = None,
    ) -> CompressionResult:
        """Compress context using LCM API.

        Args:
            text: Raw context text to compress
            method: Compression method (lcm, hierarchical, semantic)
            budget_chars: Target character budget
            scenario_turns: Optional scenario turns for episode-aware compression
            skill_hints: Optional skill hints to guide compression

        Returns:
            CompressionResult with compressed context and metadata
        """
        budget = budget_chars or self.config.default_budget_chars

        payload = {
            "text": text,
            "method": method,
            "budget_chars": budget,
            "preserve_structures": ["episode", "checkpoint", "constraint"],
        }

        if scenario_turns:
            payload["episodes"] = self._extract_episodes(scenario_turns)

        if skill_hints:
            payload["skill_hints"] = skill_hints

        # Try LCM API first
        try:
            result = self._make_request("/v1/compress", payload)
            return CompressionResult(
                method=method,
                raw_chars=len(text),
                compressed_chars=len(result.get("compressed_text", "")),
                reduction_ratio=result.get("reduction_ratio", 0.0),
                context=result.get("compressed_text", ""),
                metadata=result.get("metadata", {}),
                compression_events=result.get("compression_events", []),
                layer_info=result.get("layer_info"),
            )
        except LCMError:
            # Fall back to local proxy implementation
            return self._fallback_compression(text, method, budget, scenario_turns)

    def _extract_episodes(self, scenario_turns: list[dict]) -> list[dict]:
        """Extract episode structure from scenario turns."""
        episodes = []
        current_episode = None

        for turn in sorted(scenario_turns, key=lambda x: x.get("turn_id", 0)):
            ep_id = turn.get("episode_id", "")
            hint = turn.get("compression_hint", "")

            if ep_id and ep_id != current_episode:
                current_episode = ep_id
                episodes.append({
                    "id": ep_id,
                    "turns": [],
                    "hint": hint,
                })

            if episodes:
                episodes[-1]["turns"].append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", ""),
                    "turn_id": turn.get("turn_id", 0),
                })

        return episodes

    def _fallback_compression(
        self,
        text: str,
        method: str,
        budget_chars: int,
        scenario_turns: list[dict] | None = None,
    ) -> CompressionResult:
        """Fallback compression when LCM API is unavailable."""
        # Import local compression logic
        from utils.compression_profiles import build_context

        # Create temporary workspace for compatibility
        temp_workspace = "/tmp/lcm_fallback"
        Path(temp_workspace).mkdir(parents=True, exist_ok=True)

        # Write text to episodes folder for processing
        episodes_dir = Path(temp_workspace) / "episodes"
        episodes_dir.mkdir(exist_ok=True)
        (episodes_dir / "context.txt").write_text(text, encoding="utf-8")

        result = build_context(temp_workspace, method, budget_chars)

        return CompressionResult(
            method=result.get("method", method),
            raw_chars=result.get("raw_chars", len(text)),
            compressed_chars=result.get("compressed_chars", len(result.get("context", ""))),
            reduction_ratio=result.get("reduction_ratio", 0.0),
            context=result.get("context", ""),
            metadata={"fallback": True, "note": "LCM API unavailable, using local proxy"},
            compression_events=[],
            layer_info=None,
        )

    def summarize_layer(
        self,
        text: str,
        layer_type: str = "episode",
        preserve_constraints: bool = True,
    ) -> dict:
        """Request layer-specific summarization from LCM.

        Args:
            text: Text to summarize
            layer_type: Type of layer (episode, checkpoint, constraint)
            preserve_constraints: Whether to preserve constraint statements

        Returns:
            Dict with summary and metadata
        """
        payload = {
            "text": text,
            "layer_type": layer_type,
            "preserve_constraints": preserve_constraints,
        }

        try:
            return self._make_request("/v1/summarize", payload)
        except LCMError as e:
            return {
                "summary": text[:2000],  # Simple truncation fallback
                "error": str(e),
                "fallback": True,
            }

    def check_compression_health(self) -> dict:
        """Check if LCM service is healthy."""
        try:
            url = f"{self.config.base_url.rstrip('/')}/health"
            resp = self.session.get(url, timeout=10, verify=self.config.verify_ssl)
            resp.raise_for_status()
            return {"healthy": True, "details": resp.json()}
        except Exception as e:
            return {"healthy": False, "error": str(e)}


class LCMError(Exception):
    """Exception raised for LCM API errors."""
    pass


# ===================== Integration with existing compression_profiles =====================

def build_context_with_lcm(
    workspace_path: str,
    method: str = "lcm",
    budget_chars: int = 12000,
    scenario_turns: list[dict] | None = None,
    use_api: bool = True,
) -> dict:
    """Build compressed context with LCM integration.

    This is the enhanced version of compression_profiles.build_context()
    that uses real LCM API when available.

    Args:
        workspace_path: Path to workspace with context files
        method: Compression method
        budget_chars: Character budget
        scenario_turns: Optional scenario turns for episode awareness
        use_api: Whether to try LCM API (falls back to local if unavailable)

    Returns:
        Dict with compression results compatible with existing interface
    """
    # First collect workspace files
    ws = Path(workspace_path)
    files: list[tuple[str, str]] = []
    for sub in ["episodes", "evidence"]:
        folder = ws / sub
        if not folder.exists():
            continue
        for p in sorted([x for x in folder.rglob("*") if x.is_file()]):
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            files.append((str(p.relative_to(ws)), txt))

    if not files:
        return {
            "method": method,
            "raw_chars": 0,
            "compressed_chars": 0,
            "reduction_ratio": 0.0,
            "context": "No workspace context files found.",
            "lcm_used": False,
        }

    # Merge files
    merged = "\n\n".join([f"[FILE] {path}\n{text}" for path, text in files])

    # Use LCM client if API mode requested
    if use_api and method in {"lcm", "lcm-proxy", "hierarchical"}:
        try:
            client = LCMClient()
            health = client.check_compression_health()

            if health.get("healthy"):
                result = client.compress_context(
                    text=merged,
                    method="lcm" if method == "lcm-proxy" else method,
                    budget_chars=budget_chars,
                    scenario_turns=scenario_turns,
                )
                return {
                    "method": result.method,
                    "raw_chars": result.raw_chars,
                    "compressed_chars": result.compressed_chars,
                    "reduction_ratio": result.reduction_ratio,
                    "context": result.context,
                    "lcm_used": True,
                    "lcm_metadata": result.metadata,
                    "compression_events": result.compression_events,
                }
        except Exception:
            pass  # Fall through to local implementation

    # Use local compression_profiles implementation
    from utils.compression_profiles import build_context as local_build_context
    result = local_build_context(workspace_path, method, budget_chars)
    result["lcm_used"] = False
    return result
