"""
OpenClaw-MemBench Grading System

Design Principles:
1. Differentiation: Scores must distinguish between methods (no binary 0/1 scores)
2. Compression-aware: Metrics reflect compression fidelity and budget efficiency
3. Capability-aligned: Scores map to the 5 memory forms (context_cache, state_memory,
   procedural_memory, anti_memory, evidence_graph)
4. Continuous: Use similarity metrics (Jaccard, edit distance, semantic) not binary checks
"""

from __future__ import annotations

import csv
import json
import re
import math
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):
    """Task execution status from result.json"""
    SUCCESS = "success"
    PARTIAL = "partial"
    DEGRADED_FALLBACK = "degraded_fallback"
    ERROR = "error"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class GradingWeights:
    """Configurable weights for different scoring dimensions."""
    # Task completion quality
    execution_quality: float = 0.25

    # Memory form accuracy (did it choose and create the right memory type)
    memory_form_accuracy: float = 0.25

    # Compression fidelity (information retention under budget)
    compression_fidelity: float = 0.20

    # Capability signal strength (depth of understanding, not just keyword count)
    capability_depth: float = 0.15

    # Constraint precision (exact adherence to rules)
    constraint_precision: float = 0.15

    def validate(self):
        total = sum([
            self.execution_quality,
            self.memory_form_accuracy,
            self.compression_fidelity,
            self.capability_depth,
            self.constraint_precision,
        ])
        if abs(total - 1.0) > 0.001:
            factor = 1.0 / total
            self.execution_quality *= factor
            self.memory_form_accuracy *= factor
            self.compression_fidelity *= factor
            self.capability_depth *= factor
            self.constraint_precision *= factor


# Capability-specific weight configurations
CAPABILITY_WEIGHTS = {
    "Recent Constraint Tracking": GradingWeights(
        execution_quality=0.20,
        memory_form_accuracy=0.30,  # Critical: must write to context_cache correctly
        compression_fidelity=0.25,  # Must retain constraints under budget
        capability_depth=0.15,
        constraint_precision=0.10,
    ),
    "Version Update": GradingWeights(
        execution_quality=0.20,
        memory_form_accuracy=0.30,  # Must write versioned state correctly
        compression_fidelity=0.20,
        capability_depth=0.15,
        constraint_precision=0.15,  # High precision for version tracking
    ),
    "Procedure Transfer": GradingWeights(
        execution_quality=0.25,
        memory_form_accuracy=0.30,  # Must extract reusable procedure
        compression_fidelity=0.15,
        capability_depth=0.20,      # Depth matters for abstraction
        constraint_precision=0.10,
    ),
    "Repeated Mistake Prevention": GradingWeights(
        execution_quality=0.25,
        memory_form_accuracy=0.30,  # Must write anti-memory correctly
        compression_fidelity=0.15,
        capability_depth=0.20,
        constraint_precision=0.10,
    ),
    "Source Conflict Resolution": GradingWeights(
        execution_quality=0.20,
        memory_form_accuracy=0.25,  # Must build evidence graph
        compression_fidelity=0.20,
        capability_depth=0.25,      # Deep analysis of conflicts
        constraint_precision=0.10,
    ),
    "Memory Operation Selection": GradingWeights(
        execution_quality=0.25,
        memory_form_accuracy=0.35,  # Core: selecting right memory form
        compression_fidelity=0.15,
        capability_depth=0.20,
        constraint_precision=0.05,
    ),
    "Goal Interruption and Task Resumption": GradingWeights(
        execution_quality=0.20,
        memory_form_accuracy=0.30,  # Must preserve interrupted state
        compression_fidelity=0.25,  # Critical: resume after compression
        capability_depth=0.15,
        constraint_precision=0.10,
    ),
    "Staleness and Applicability Judgment": GradingWeights(
        execution_quality=0.20,
        memory_form_accuracy=0.25,
        compression_fidelity=0.20,
        capability_depth=0.25,      # Deep judgment of applicability
        constraint_precision=0.10,
    ),
}


# ===================== Utility Functions =====================

def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def tokenize(text: str) -> set:
    """Tokenize text into meaningful words."""
    if not text:
        return set()
    # Extract alphanumeric tokens of 3+ chars, lowercase
    tokens = re.findall(r'\b[a-z][a-z0-9_]{2,}\b', text.lower())
    # Filter out common stop words
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
                  'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has',
                  'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see',
                  'two', 'who', 'boy', 'did', 'she', 'use', 'her', 'way', 'many',
                  'oil', 'sit', 'set', 'run', 'eat', 'far', 'sea', 'eye', 'ago',
                  'off', 'too', 'any', 'say', 'man', 'try', 'ask', 'end', 'why',
                  'let', 'put', 'say', 'she', 'try', 'way', 'own', 'say', 'too',
                  'old', 'tell', 'very', 'when', 'much', 'would', 'there', 'their',
                  'what', 'said', 'each', 'which', 'will', 'about', 'could', 'other',
                  'after', 'first', 'never', 'these', 'think', 'where', 'being',
                  'every', 'great', 'might', 'shall', 'still', 'those', 'while',
                  'this', 'that', 'have', 'from', 'they', 'been', 'were', 'with',
                  'have', 'your', 'into', 'just', 'like', 'over', 'also', 'back',
                  'only', 'know', 'take', 'year', 'good', 'come', 'make', 'well',
                  'work', 'even', 'more', 'want', 'here', 'look', 'down', 'most',
                  'long', 'last', 'find', 'give', 'does', 'made', 'part', 'such',
                  'keep', 'call', 'came', 'need', 'feel', 'seem', 'turn', 'hand',
                  'sure', 'upon', 'head', 'help', 'home', 'side', 'move', 'both',
                  'five', 'once', 'same', 'must', 'name', 'left', 'each', 'done',
                  'open', 'case', 'show', 'live', 'play', 'went', 'told', 'seen',
                  'hear', 'talk', 'soon', 'read', 'stop', 'face', 'fact', 'land',
                  'line', 'kind', 'next', 'word', 'came', 'went', 'told', 'seen',
                  'hear', 'talk', 'soon', 'read', 'stop', 'face', 'fact', 'land',
                  'line', 'kind', 'next', 'word', 'came', 'went', 'told', 'seen'}
    return set(t for t in tokens if t not in stop_words)


def ngram_similarity(text_a: str, text_b: str, n: int = 3) -> float:
    """Calculate n-gram similarity between two texts."""
    def get_ngrams(text, n):
        words = re.findall(r'\b\w+\b', text.lower())
        return set(tuple(words[i:i+n]) for i in range(len(words)-n+1))

    ngrams_a = get_ngrams(text_a, n)
    ngrams_b = get_ngrams(text_b, n)
    return jaccard_similarity(ngrams_a, ngrams_b)


def structural_similarity(dict_a: dict, dict_b: dict) -> float:
    """Calculate structural similarity between two dictionaries."""
    if not isinstance(dict_a, dict) or not isinstance(dict_b, dict):
        return 1.0 if dict_a == dict_b else 0.0

    keys_a = set(dict_a.keys())
    keys_b = set(dict_b.keys())

    # Jaccard similarity of keys
    key_sim = jaccard_similarity(keys_a, keys_b)

    # Recursively check values for common keys
    common_keys = keys_a & keys_b
    if not common_keys:
        return key_sim * 0.5  # Penalize if no common keys

    value_sims = []
    for key in common_keys:
        val_a, val_b = dict_a[key], dict_b[key]
        if isinstance(val_a, dict) and isinstance(val_b, dict):
            value_sims.append(structural_similarity(val_a, val_b))
        elif isinstance(val_a, list) and isinstance(val_b, list):
            # Compare list lengths and element types
            len_sim = min(len(val_a), len(val_b)) / max(len(val_a), len(val_b)) if max(len(val_a), len(val_b)) > 0 else 1.0
            value_sims.append(len_sim)
        else:
            value_sims.append(1.0 if val_a == val_b else 0.0)

    avg_value_sim = sum(value_sims) / len(value_sims) if value_sims else 0.0
    return key_sim * 0.3 + avg_value_sim * 0.7


def load_oracle(oracle_path: str | Path) -> dict:
    """Load oracle.yaml with gold standards for grading."""
    p = Path(oracle_path)
    if not p.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def load_scenario(scenario_path: str | Path) -> list[dict]:
    """Load scenario.jsonl with turn-by-turn conversation."""
    p = Path(scenario_path)
    if not p.exists():
        return []
    turns = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            turns.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return turns


# ===================== Differentiated Scoring Functions =====================

def score_execution_quality(result_json_path: Path, usage: dict | None = None) -> dict:
    """
    Score execution quality with continuous metrics.

    Returns scores that vary continuously rather than binary 0/1.
    """
    scores = {}

    if not result_json_path.exists():
        return {
            "execution_status_score": 0.0,
            "execution_completeness": 0.0,
            "execution_api_success": 0.0,
        }

    try:
        data = json.loads(result_json_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "execution_status_score": 0.0,
            "execution_completeness": 0.0,
            "execution_api_success": 0.0,
        }

    status = data.get("status", "").lower()
    reason = data.get("reason", "")

    # Status score - continuous based on status
    status_scores = {
        "success": 1.0,
        "completed": 1.0,
        "done": 1.0,
        "partial": 0.6,
        "degraded_fallback": 0.2,
        "error": 0.0,
        "failed": 0.0,
        "": 0.3,  # Unknown status gets partial credit
    }
    scores["execution_status_score"] = status_scores.get(status, 0.3)

    # Completeness - based on result.json content richness
    required_top_keys = {"task_id", "status", "artifacts", "capability"}
    optional_keys = {"constraints", "version", "procedure", "evidence", "anti_patterns"}

    present_required = sum(1 for k in required_top_keys if k in data)
    present_optional = sum(1 for k in optional_keys if k in data)

    required_ratio = present_required / len(required_top_keys)
    optional_bonus = present_optional / len(optional_keys) * 0.3  # Up to 0.3 bonus

    scores["execution_completeness"] = min(1.0, required_ratio + optional_bonus)

    # API success - check for error indicators in reason
    error_indicators = ["timeout", "connection", "error", "failed", "exception", "refused"]
    error_count = sum(1 for e in error_indicators if e in reason.lower())
    scores["execution_api_success"] = max(0.0, 1.0 - error_count * 0.25)

    return scores


def score_memory_form_accuracy(
    results_dir: Path,
    oracle: dict,
    capability: str,
    scenario: list[dict]
) -> dict:
    """
    Score how accurately the agent created the right memory form.

    This is key for differentiation - different methods should produce
    different quality memory objects.
    """
    scores = {}

    # Determine expected memory form from capability
    capability_memory_map = {
        "Recent Constraint Tracking": "context_cache",
        "Version Update": "state_memory",
        "Procedure Transfer": "procedural_memory",
        "Repeated Mistake Prevention": "anti_memory",
        "Source Conflict Resolution": "evidence_graph",
        "Memory Operation Selection": "memory_router",
        "Goal Interruption and Task Resumption": "context_cache",
        "Staleness and Applicability Judgment": "state_memory",
    }

    expected_form = capability_memory_map.get(capability, "unknown")
    scores["expected_memory_form"] = expected_form

    # Check for memory form files with structural similarity to oracle
    memory_files = {
        "context_cache": ["constraint_trace.json", "context_cache.json", "slots.json"],
        "state_memory": ["version_chain.json", "state_memory.json", "state.json"],
        "procedural_memory": ["procedure_manifest.json", "procedural_memory.json", "workflow.json"],
        "anti_memory": ["guardrail.json", "anti_memory.json", "anti_patterns.json"],
        "evidence_graph": ["evidence_ranking.json", "evidence_graph.json", "conflict_resolution.md"],
        "memory_router": ["operation_log.json", "memory_router.json", "routing_decisions.json"],
    }

    expected_files = memory_files.get(expected_form, [])
    found_files = []
    structural_scores = []

    for ef in expected_files:
        path = results_dir / ef
        if path.exists():
            found_files.append(ef)
            # Calculate structural similarity to oracle if available
            oracle_key = ef.replace(".json", "").replace(".md", "")
            gold_data = oracle.get(f"gold_{oracle_key}", {})
            if gold_data:
                try:
                    actual_data = json.loads(path.read_text(encoding="utf-8"))
                    sim = structural_similarity(actual_data, gold_data)
                    structural_scores.append(sim)
                except Exception:
                    structural_scores.append(0.5)  # File exists but can't compare
            else:
                # No oracle, check basic structure
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and len(data) > 0:
                        structural_scores.append(0.7)  # Decent structure
                    elif isinstance(data, list) and len(data) > 0:
                        structural_scores.append(0.6)
                    else:
                        structural_scores.append(0.3)
                except Exception:
                    structural_scores.append(0.4)  # File exists

    # File presence score (continuous based on how many expected files found)
    if expected_files:
        scores["memory_form_file_presence"] = len(found_files) / len(expected_files)
    else:
        scores["memory_form_file_presence"] = 0.5

    # Structural accuracy score
    if structural_scores:
        scores["memory_form_structural_accuracy"] = sum(structural_scores) / len(structural_scores)
    else:
        scores["memory_form_structural_accuracy"] = 0.0

    # Content richness (how much useful content was captured)
    total_content_size = 0
    for ff in found_files:
        try:
            path = results_dir / ff
            data = json.loads(path.read_text(encoding="utf-8"))
            total_content_size += len(json.dumps(data))
        except Exception:
            pass

    # Normalize content size (expecting ~500-5000 chars for good content)
    content_score = min(1.0, max(0.0, (total_content_size - 100) / 4900))
    scores["memory_form_content_richness"] = content_score

    return scores


def score_compression_fidelity(
    results_dir: Path,
    oracle: dict,
    scenario: list[dict],
    usage: dict | None = None
) -> dict:
    """
    Score compression fidelity - how well information was retained under budget.

    Key differentiator: better compression methods should score higher.
    """
    scores = {}

    # Budget efficiency from usage data
    if usage:
        raw_chars = usage.get("raw_context_chars", 0)
        compressed_chars = usage.get("compressed_context_chars", 0)
        budget = usage.get("context_budget_chars", 12000)

        if raw_chars > 0:
            # Information retention ratio (higher is better, up to 1.0)
            actual_ratio = compressed_chars / raw_chars if raw_chars > 0 else 1.0
            target_ratio = budget / raw_chars if raw_chars > budget else 1.0

            # Score: how close to target budget while maximizing retention
            # Ideal: compressed is close to budget but not exceeding it much
            if compressed_chars <= budget * 1.1:  # Within 10% of budget
                budget_adherence = 1.0
            elif compressed_chars <= budget * 1.5:
                budget_adherence = 0.7
            else:
                budget_adherence = 0.3

            # Compression ratio efficiency
            compression_efficiency = min(1.0, budget / max(compressed_chars, 1))

            scores["compression_budget_adherence"] = budget_adherence
            scores["compression_efficiency"] = compression_efficiency
            scores["compression_ratio"] = 1.0 - actual_ratio  # Higher compression = higher score
        else:
            scores["compression_budget_adherence"] = 0.5
            scores["compression_efficiency"] = 0.5
            scores["compression_ratio"] = 0.0
    else:
        scores["compression_budget_adherence"] = 0.5
        scores["compression_efficiency"] = 0.5
        scores["compression_ratio"] = 0.0

    # Information retention check - compare scenario content to results
    if scenario:
        scenario_text = " ".join(str(t.get("content", "")) for t in scenario)
        result_text = ""
        for rf in ["result.json", "summary.md"]:
            path = results_dir / rf
            if path.exists():
                try:
                    result_text += path.read_text(encoding="utf-8")
                except Exception:
                    pass

        # Calculate information overlap using n-gram similarity
        if scenario_text and result_text:
            retention_sim = ngram_similarity(scenario_text, result_text, n=2)
            scores["compression_information_retention"] = retention_sim
        else:
            scores["compression_information_retention"] = 0.0
    else:
        scores["compression_information_retention"] = 0.0

    # Key constraint retention (from oracle)
    gold_constraints = oracle.get("gold_constraints", [])
    if gold_constraints and scenario:
        scenario_text = " ".join(str(t.get("content", "")) for t in scenario).lower()
        result_text = ""
        for rf in ["result.json", "summary.md", "constraint_trace.json"]:
            path = results_dir / rf
            if path.exists():
                try:
                    result_text += path.read_text(encoding="utf-8").lower()
                except Exception:
                    pass

        # Check each gold constraint
        constraint_retentions = []
        for constraint in gold_constraints:
            constraint_tokens = tokenize(constraint)
            result_tokens = tokenize(result_text)
            retention = jaccard_similarity(constraint_tokens, result_tokens)
            constraint_retentions.append(retention)

        scores["compression_constraint_retention"] = sum(constraint_retentions) / len(constraint_retentions) if constraint_retentions else 0.0
    else:
        scores["compression_constraint_retention"] = 0.5

    return scores


def score_capability_depth(
    transcript: list[dict] | None,
    results_dir: Path,
    capability: str,
    scenario: list[dict]
) -> dict:
    """
    Score depth of capability understanding (not just keyword counting).

    Uses semantic similarity and structural analysis to differentiate
    surface-level keyword matching from deep understanding.
    """
    scores = {}

    # Capability-specific deep signals
    deep_signals = {
        "Recent Constraint Tracking": {
            "primary": ["slot", "constraint", "latest", "superseded", "active"],
            "secondary": ["trace", "evidence", "version", "override"],
            "patterns": [r"latest\s+constraint", r"superseded\s+by", r"active\s+slot"],
        },
        "Version Update": {
            "primary": ["version", "chain", "supersede", "deprecated", "migrate"],
            "secondary": ["previous", "current", "latest", "update", "revision"],
            "patterns": [r"version\s+\d+", r"superseded\s+by", r"migrat(ed|ing|ion)"],
        },
        "Procedure Transfer": {
            "primary": ["procedure", "template", "reusable", "pattern", "abstract"],
            "secondary": ["step", "workflow", "transfer", "apply", "generalize"],
            "patterns": [r"reusable\s+procedure", r"template\s+for", r"abstract\s+pattern"],
        },
        "Repeated Mistake Prevention": {
            "primary": ["anti", "guard", "prevent", "veto", "checklist"],
            "secondary": ["mistake", "error", "avoid", "before", "verify"],
            "patterns": [r"anti\s+pattern", r"guard\s+against", r"veto\s+if"],
        },
        "Source Conflict Resolution": {
            "primary": ["evidence", "arbitration", "priority", "conflict", "source"],
            "secondary": ["rank", "compare", "grounded", "credible", "trust"],
            "patterns": [r"source\s+[A-Z]", r"higher\s+priority", r"evidence\s+for"],
        },
        "Memory Operation Selection": {
            "primary": ["memory", "operation", "select", "route", "cache"],
            "secondary": ["store", "recall", "retrieve", "compress", "budget"],
            "patterns": [r"memory\s+form", r"select\s+operation", r"route\s+to"],
        },
        "Goal Interruption and Task Resumption": {
            "primary": ["resume", "checkpoint", "interrupt", "pending", "continuation"],
            "secondary": ["return", "back", "save", "restore", "progress"],
            "patterns": [r"resume\s+from", r"checkpoint\s+at", r"pending\s+task"],
        },
        "Staleness and Applicability Judgment": {
            "primary": ["stale", "applicable", "deprecated", "invalidate", "fresh"],
            "secondary": ["outdated", "current", "valid", "expired", "recent"],
            "patterns": [r"no\s+longer\s+applicable", r"stale\s+information", r"deprecated\s+since"],
        },
    }

    signals = deep_signals.get(capability, {"primary": [], "secondary": [], "patterns": []})

    # Combine all text sources
    all_text = ""
    if transcript:
        all_text += " ".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))

    for rf in ["result.json", "summary.md"]:
        path = results_dir / rf
        if path.exists():
            try:
                all_text += " " + path.read_text(encoding="utf-8")
            except Exception:
                pass

    text_lower = all_text.lower()
    text_tokens = tokenize(all_text)

    # Score primary signals (weighted more)
    primary_hits = sum(1 for s in signals["primary"] if s in text_lower)
    primary_score = primary_hits / max(1, len(signals["primary"]))

    # Score secondary signals
    secondary_hits = sum(1 for s in signals["secondary"] if s in text_lower)
    secondary_score = secondary_hits / max(1, len(signals["secondary"])) * 0.5  # Half weight

    # Score pattern matches (regex)
    pattern_hits = 0
    for pattern in signals["patterns"]:
        if re.search(pattern, text_lower):
            pattern_hits += 1
    pattern_score = pattern_hits / max(1, len(signals["patterns"]))

    # Semantic depth: check for explanations/rationale
    explanation_signals = ["because", "therefore", "reason", "rationale", "explanation", "why"]
    explanation_count = sum(1 for s in explanation_signals if s in text_lower)
    explanation_score = min(1.0, explanation_count / 3)  # Max at 3+ explanations

    # Combine scores with weights
    scores["capability_primary_signals"] = primary_score
    scores["capability_secondary_signals"] = secondary_score
    scores["capability_pattern_matches"] = pattern_score
    scores["capability_explanation_depth"] = explanation_score

    # Overall depth score (emphasize patterns and explanations)
    scores["capability_depth_overall"] = (
        primary_score * 0.3 +
        secondary_score * 0.2 +
        pattern_score * 0.3 +
        explanation_score * 0.2
    )

    return scores


def score_constraint_precision(
    results_dir: Path,
    oracle: dict,
    scenario: list[dict]
) -> dict:
    """
    Score precision of constraint adherence with continuous metrics.
    """
    scores = {}

    result_text = ""
    for rf in ["result.json", "summary.md", "constraint_trace.json"]:
        path = results_dir / rf
        if path.exists():
            try:
                result_text += " " + path.read_text(encoding="utf-8")
            except Exception:
                pass

    result_lower = result_text.lower()
    result_tokens = tokenize(result_text)

    # Gold constraints evaluation with token similarity
    gold_constraints = oracle.get("gold_constraints", [])
    constraint_scores = []

    for constraint in gold_constraints:
        constraint_lower = constraint.lower()
        constraint_tokens = tokenize(constraint)

        # Token similarity (Jaccard)
        token_sim = jaccard_similarity(constraint_tokens, result_tokens)

        # Exact substring match bonus
        substring_bonus = 0.2 if constraint_lower in result_lower else 0.0

        # Number/date matching (for year ranges, versions)
        numbers_in_constraint = set(re.findall(r'\d+(?:\.\d+)*', constraint))
        numbers_in_result = set(re.findall(r'\d+(?:\.\d+)*', result_text))
        if numbers_in_constraint:
            number_match = len(numbers_in_constraint & numbers_in_result) / len(numbers_in_constraint)
        else:
            number_match = 0.0

        combined_score = min(1.0, token_sim * 0.5 + substring_bonus + number_match * 0.3)
        constraint_scores.append(combined_score)

    if constraint_scores:
        scores["constraint_adherence_overall"] = sum(constraint_scores) / len(constraint_scores)
    else:
        scores["constraint_adherence_overall"] = 0.5

    # Anti-constraints (should NOT be present)
    anti_constraints = oracle.get("gold_anti_rule", [])
    anti_scores = []

    for anti in anti_constraints:
        anti_tokens = tokenize(anti)
        overlap = jaccard_similarity(anti_tokens, result_tokens)
        # Lower score if high overlap (violation)
        anti_score = 1.0 - overlap
        anti_scores.append(anti_score)

    if anti_scores:
        scores["anti_constraint_adherence"] = sum(anti_scores) / len(anti_scores)
    else:
        scores["anti_constraint_adherence"] = 1.0  # No anti-constraints to violate

    # Schema precision (for CSV files)
    csv_files = list(results_dir.glob("*.csv"))
    if csv_files:
        schema_scores = []
        for csv_path in csv_files:
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames or []

                    # Check against gold schema if available
                    gold_schema = oracle.get("gold_schema", [])
                    if gold_schema:
                        # Exact match
                        if fieldnames == gold_schema:
                            schema_scores.append(1.0)
                        else:
                            # Partial match
                            matches = sum(1 for f in gold_schema if f in fieldnames)
                            schema_scores.append(matches / len(gold_schema))
                    else:
                        schema_scores.append(0.7)  # Has CSV with some structure
            except Exception:
                schema_scores.append(0.0)

        scores["constraint_schema_precision"] = sum(schema_scores) / len(schema_scores) if schema_scores else 0.0
    else:
        scores["constraint_schema_precision"] = 0.0

    return scores


# ===================== Main Grading Entry Point =====================

def grade_task(
    task_capability: str,
    workspace_path: str | Path,
    oracle_path: str | Path | None = None,
    scenario_path: str | Path | None = None,
    transcript: list[dict] | None = None,
    usage: dict | None = None,
) -> dict:
    """
    Main entry point for grading a task.

    Args:
        task_capability: The primary capability being tested
        workspace_path: Path to the task workspace (with results/ subdirectory)
        oracle_path: Optional path to oracle.yaml
        scenario_path: Optional path to scenario.jsonl
        transcript: Optional conversation transcript
        usage: Optional usage data with compression metrics

    Returns:
        Dict with individual scores and overall_score
    """
    workspace_path = Path(workspace_path)
    results_dir = workspace_path / "results"

    # Load oracle and scenario
    oracle = load_oracle(oracle_path) if oracle_path else {}
    if not oracle and (workspace_path / "oracle.yaml").exists():
        oracle = load_oracle(workspace_path / "oracle.yaml")

    scenario = load_scenario(scenario_path) if scenario_path else []
    if not scenario and (workspace_path / "scenario.jsonl").exists():
        scenario = load_scenario(workspace_path / "scenario.jsonl")

    all_scores = {}

    # 1. Execution quality
    result_json_path = results_dir / "result.json"
    execution_scores = score_execution_quality(result_json_path, usage)
    all_scores.update(execution_scores)

    # 2. Memory form accuracy
    memory_scores = score_memory_form_accuracy(results_dir, oracle, task_capability, scenario)
    all_scores.update(memory_scores)

    # 3. Compression fidelity
    compression_scores = score_compression_fidelity(results_dir, oracle, scenario, usage)
    all_scores.update(compression_scores)

    # 4. Capability depth
    depth_scores = score_capability_depth(transcript, results_dir, task_capability, scenario)
    all_scores.update(depth_scores)

    # 5. Constraint precision
    constraint_scores = score_constraint_precision(results_dir, oracle, scenario)
    all_scores.update(constraint_scores)

    # Calculate weighted final score
    weights = CAPABILITY_WEIGHTS.get(task_capability, GradingWeights())
    weights.validate()

    # Component aggregates
    execution = execution_scores.get("execution_status_score", 0.0)
    memory_form = (
        memory_scores.get("memory_form_file_presence", 0.0) * 0.4 +
        memory_scores.get("memory_form_structural_accuracy", 0.0) * 0.4 +
        memory_scores.get("memory_form_content_richness", 0.0) * 0.2
    )
    compression = (
        compression_scores.get("compression_information_retention", 0.0) * 0.4 +
        compression_scores.get("compression_constraint_retention", 0.0) * 0.4 +
        compression_scores.get("compression_efficiency", 0.0) * 0.2
    )
    depth = depth_scores.get("capability_depth_overall", 0.0)
    constraint = (
        constraint_scores.get("constraint_adherence_overall", 0.0) * 0.6 +
        constraint_scores.get("anti_constraint_adherence", 0.0) * 0.4
    )

    weighted_overall = (
        execution * weights.execution_quality +
        memory_form * weights.memory_form_accuracy +
        compression * weights.compression_fidelity +
        depth * weights.capability_depth +
        constraint * weights.constraint_precision
    )

    all_scores["overall_score"] = round(weighted_overall, 4)
    all_scores["execution_quality_score"] = round(execution, 4)
    all_scores["memory_form_accuracy_score"] = round(memory_form, 4)
    all_scores["compression_fidelity_score"] = round(compression, 4)
    all_scores["capability_depth_score"] = round(depth, 4)
    all_scores["constraint_precision_score"] = round(constraint, 4)
    all_scores["grading_weights_applied"] = {
        "execution_quality": round(weights.execution_quality, 4),
        "memory_form_accuracy": round(weights.memory_form_accuracy, 4),
        "compression_fidelity": round(weights.compression_fidelity, 4),
        "capability_depth": round(weights.capability_depth, 4),
        "constraint_precision": round(weights.constraint_precision, 4),
    }

    return all_scores


def run_grading_from_task_md(
    task: dict,
    transcript: list[dict] | None = None,
    workspace_override: str | None = None,
    usage: dict | None = None,
) -> tuple[dict, str | None]:
    """
    Run grading from a parsed task markdown dict.

    This is the main entry point used by run_batch.py.

    Args:
        task: Parsed task dict from parse_task_md
        transcript: Optional conversation transcript
        workspace_override: Optional override for workspace path
        usage: Optional usage data

    Returns:
        Tuple of (scores_dict, error_message_or_none)
    """
    workspace = Path(workspace_override or task.get("workspace_path", "/tmp_workspace"))
    capability = task.get("capability", "")

    # Find oracle and scenario paths
    oracle_path = task.get("oracle_path") or (workspace / "oracle.yaml")
    scenario_path = task.get("scenario_path") or (workspace / "scenario.jsonl")

    try:
        scores = grade_task(
            task_capability=capability,
            workspace_path=workspace,
            oracle_path=oracle_path,
            scenario_path=scenario_path,
            transcript=transcript,
            usage=usage,
        )
        return scores, None
    except Exception as e:
        import traceback
        return {"overall_score": 0.0}, f"Grading error: {e}\n{traceback.format_exc()}"


# ===================== Utility Functions (for run_batch.py compatibility) =====================

def aggregate_scores(scores: dict[str, float]) -> float:
    """Aggregate scores - returns overall_score if present, else calculates average."""
    if "overall_score" in scores:
        return scores["overall_score"]
    numeric = [v for v in scores.values() if isinstance(v, (int, float))]
    if not numeric:
        return 0.0
    return round(sum(numeric) / len(numeric), 4)


def write_summary(output_path: Path, rows: list[dict]) -> None:
    """Write scores to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def format_table(rows: list[dict]) -> str:
    """Format scores as TSV table."""
    header = ["task_id", "overall_score", "execution_quality", "memory_form", "compression", "capability_depth", "constraint_precision", "status"]
    lines = ["\t".join(header)]
    for r in rows:
        lines.append("\t".join([
            str(r.get("task_id", "")),
            f"{r.get('overall_score', 0.0):.4f}",
            f"{r.get('scores', {}).get('execution_quality_score', 0.0):.4f}",
            f"{r.get('scores', {}).get('memory_form_accuracy_score', 0.0):.4f}",
            f"{r.get('scores', {}).get('compression_fidelity_score', 0.0):.4f}",
            f"{r.get('scores', {}).get('capability_depth_score', 0.0):.4f}",
            f"{r.get('scores', {}).get('constraint_precision_score', 0.0):.4f}",
            str(r.get("status", "ok")),
        ]))
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo run
    import sys

    if len(sys.argv) > 1:
        workspace = Path(sys.argv[1])
    else:
        workspace = Path("workspace/01_Recent_Constraint_Tracking/task_01_arxiv_csv_digest")

    print(f"Running grading on: {workspace}")

    scores = grade_task(
        task_capability="Recent Constraint Tracking",
        workspace_path=workspace,
    )

    print(f"\nOverall Score: {scores.get('overall_score', 0.0):.4f}")
    print(f"Execution Quality: {scores.get('execution_quality_score', 0.0):.4f}")
    print(f"Memory Form Accuracy: {scores.get('memory_form_accuracy_score', 0.0):.4f}")
    print(f"Compression Fidelity: {scores.get('compression_fidelity_score', 0.0):.4f}")
    print(f"Capability Depth: {scores.get('capability_depth_score', 0.0):.4f}")
    print(f"Constraint Precision: {scores.get('constraint_precision_score', 0.0):.4f}")
