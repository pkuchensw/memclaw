from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


def aggregate_scores(scores: dict[str, float]) -> float:
    numeric = [v for v in scores.values() if isinstance(v, (int, float))]
    if not numeric:
        return 0.0
    return round(sum(numeric) / len(numeric), 4)


def format_table(rows: list[dict]) -> str:
    header = ["task_id", "overall_score", "status"]
    lines = ["\t".join(header)]
    for r in rows:
        lines.append("\t".join([
            str(r.get("task_id", "")),
            f"{r.get('overall_score', 0.0):.4f}",
            str(r.get("status", "ok")),
        ]))
    return "\n".join(lines)


def write_summary(output_path: Path, rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


# ===================== Oracle and Scenario Loader =====================

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


# ===================== File and Artifact Checkers =====================

def check_required_files(results_dir: Path, required_files: list[str]) -> dict:
    """Check if all required files exist and are parseable."""
    scores = {}
    for rf in required_files:
        path = results_dir / rf
        exists = path.exists()
        parseable = False
        if exists:
            try:
                if rf.endswith(".json"):
                    json.loads(path.read_text(encoding="utf-8"))
                    parseable = True
                elif rf.endswith(".csv"):
                    list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
                    parseable = True
                else:
                    content = path.read_text(encoding="utf-8")
                    parseable = len(content) > 0
            except Exception:
                parseable = False
        scores[f"file_{rf.replace('.', '_')}"] = 1.0 if (exists and parseable) else 0.0
    return scores


def check_json_keys(result_json_path: Path, required_keys: list[str]) -> dict:
    """Check if result.json contains required keys."""
    if not result_json_path.exists():
        return {f"json_key_{k}": 0.0 for k in required_keys}
    try:
        data = json.loads(result_json_path.read_text(encoding="utf-8"))
    except Exception:
        return {f"json_key_{k}": 0.0 for k in required_keys}

    scores = {}
    for k in required_keys:
        scores[f"json_key_{k}"] = 1.0 if k in data else 0.0
    return scores


def check_terms_in_text(text: str, required_terms: list[str], prefix: str = "term") -> dict:
    """Check if required terms appear in text (case-insensitive)."""
    if not text:
        return {f"{prefix}_{t}": 0.0 for t in required_terms}
    low = text.lower()
    return {f"{prefix}_{t}": (1.0 if t.lower() in low else 0.0) for t in required_terms}


def check_manifest_consistency(manifest_csv_path: Path, results_dir: Path) -> float:
    """Check if manifest paths map to real files."""
    if not manifest_csv_path.exists():
        return 0.0
    try:
        rows = list(csv.DictReader(manifest_csv_path.read_text(encoding="utf-8").splitlines()))
    except Exception:
        return 0.0
    if not rows:
        return 0.0
    ok = 0
    for r in rows:
        p = (r.get("path") or "").strip()
        if p and (results_dir / p).exists():
            ok += 1
    return ok / max(1, len(rows))


# ===================== Capability-Specific Graders =====================

class CapabilityGrader:
    """Base class for capability-specific grading logic."""

    def __init__(self, oracle: dict, scenario: list[dict], workspace_path: Path):
        self.oracle = oracle
        self.scenario = scenario
        self.workspace_path = Path(workspace_path)
        self.results_dir = self.workspace_path / "results"

    def grade(self, transcript: list[dict] | None = None) -> dict:
        """Override in subclasses."""
        return {}

    def _get_latest_constraints(self) -> list[str]:
        """Extract latest constraints from scenario turns."""
        constraints = []
        for turn in self.scenario:
            content = turn.get("content", "")
            if isinstance(content, str):
                # Look for constraint patterns
                if any(kw in content.lower() for kw in ["must", "should", "required", "constraint"]):
                    constraints.append(content)
        return constraints

    def _get_result_text(self) -> str:
        """Get combined text from result.json and summary.md."""
        texts = []
        result_json = self.results_dir / "result.json"
        summary_md = self.results_dir / "summary.md"
        if result_json.exists():
            try:
                texts.append(json.dumps(json.loads(result_json.read_text(encoding="utf-8"))))
            except Exception:
                pass
        if summary_md.exists():
            texts.append(summary_md.read_text(encoding="utf-8"))
        return " ".join(texts)


class RecentConstraintTrackingGrader(CapabilityGrader):
    """Grader for C1: Recent Constraint Tracking."""

    def grade(self, transcript: list[dict] | None = None) -> dict:
        scores = {}

        # Check required files
        required = self.oracle.get("gold_artifacts", ["result.json", "summary.md", "manifest.csv"])
        file_scores = check_required_files(self.results_dir, required)
        scores.update(file_scores)

        # Check gold constraints are respected
        gold_constraints = self.oracle.get("gold_constraints", [])
        result_text = self._get_result_text()

        for constraint in gold_constraints:
            # Simple check: constraint keywords appear in output
            constraint_keywords = constraint.lower().replace("_", " ").split()
            matched = sum(1 for kw in constraint_keywords if kw in result_text.lower())
            scores[f"constraint_{constraint}"] = min(1.0, matched / max(1, len(constraint_keywords) * 0.5))

        # Check anti-constraints are NOT present
        anti_constraints = self.oracle.get("gold_anti_rule", [])
        for anti in anti_constraints:
            anti_keywords = anti.lower().replace("_", " ").replace("do not", "").split()
            matched = sum(1 for kw in anti_keywords if kw in result_text.lower())
            # Lower score if anti-constraint keywords appear
            scores[f"anti_constraint_{anti}"] = 1.0 if matched < len(anti_keywords) * 0.5 else 0.0

        # Capability-specific signals in transcript
        if transcript:
            transcript_blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))
            cues = ["constraint", "latest", "correction", "update"]
            hits = sum(1 for c in cues if c in transcript_blob.lower())
            scores["transcript_evidence"] = hits / len(cues)

        # Oracle-defined capability metrics
        metrics = self.oracle.get("capability_metrics", {})
        for metric, weight in metrics.items():
            if metric not in scores:
                scores[metric] = weight  # Use oracle weight as baseline

        return scores


class VersionUpdateGrader(CapabilityGrader):
    """Grader for C2: Version Update."""

    def grade(self, transcript: list[dict] | None = None) -> dict:
        scores = {}

        required = ["version_chain.json", "result.json", "summary.md", "manifest.csv"]
        scores.update(check_required_files(self.results_dir, required))

        # Check version chain correctness
        version_chain_path = self.results_dir / "version_chain.json"
        if version_chain_path.exists():
            try:
                chain = json.loads(version_chain_path.read_text(encoding="utf-8"))
                gold_chain = self.oracle.get("gold_version_chain", [])
                if isinstance(chain, list) and gold_chain:
                    # Check chain covers expected versions
                    chain_versions = [v.get("version") for v in chain if isinstance(v, dict)]
                    gold_versions = [v.get("version") for v in gold_chain if isinstance(v, dict)]
                    matched = sum(1 for v in gold_versions if v in chain_versions)
                    scores["version_chain_coverage"] = matched / max(1, len(gold_versions))

                    # Check final state is latest
                    if chain:
                        final = chain[-1].get("version", "")
                        expected_final = self.oracle.get("gold_final_state", {}).get("version", "")
                        scores["final_version_correct"] = 1.0 if final == expected_final else 0.0
            except Exception:
                scores["version_chain_valid"] = 0.0

        # Check transcript for version-related signals
        if transcript:
            blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))
            cues = ["version", "superseded", "latest", "deprecated", "v1", "v2", "v3"]
            hits = sum(1 for c in cues if c in blob.lower())
            scores["transcript_version_signals"] = hits / len(cues)

        return scores


class ProcedureTransferGrader(CapabilityGrader):
    """Grader for C3: Procedure Transfer."""

    def grade(self, transcript: list[dict] | None = None) -> dict:
        scores = {}

        required = ["procedure_manifest.json", "result.json", "summary.md", "manifest.csv"]
        scores.update(check_required_files(self.results_dir, required))

        # Check procedure completeness
        proc_path = self.results_dir / "procedure_manifest.json"
        if proc_path.exists():
            try:
                proc = json.loads(proc_path.read_text(encoding="utf-8"))
                gold_procedure = self.oracle.get("gold_procedure", [])
                if isinstance(proc, dict) and "steps" in proc:
                    steps = proc["steps"]
                    if isinstance(steps, list):
                        scores["procedure_step_count"] = min(1.0, len(steps) / max(1, len(gold_procedure)))
                        # Check step names match
                        step_names = [s.get("name", "").lower() for s in steps if isinstance(s, dict)]
                        gold_names = [p.lower() for p in gold_procedure]
                        matched = sum(1 for g in gold_names if any(g in s for s in step_names))
                        scores["procedure_step_match"] = matched / max(1, len(gold_names))
            except Exception:
                scores["procedure_valid"] = 0.0

        if transcript:
            blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))
            cues = ["procedure", "transfer", "step", "template", "reusable"]
            hits = sum(1 for c in cues if c in blob.lower())
            scores["transcript_procedure_signals"] = hits / len(cues)

        return scores


class RepeatedMistakePreventionGrader(CapabilityGrader):
    """Grader for C4: Repeated Mistake Prevention."""

    def grade(self, transcript: list[dict] | None = None) -> dict:
        scores = {}

        required = ["guardrail.json", "result.json", "summary.md", "manifest.csv"]
        scores.update(check_required_files(self.results_dir, required))

        # Check guardrail captures anti-rules
        guard_path = self.results_dir / "guardrail.json"
        if guard_path.exists():
            try:
                guard = json.loads(guard_path.read_text(encoding="utf-8"))
                gold_anti = self.oracle.get("gold_anti_rule", [])
                if isinstance(guard, dict) and "rules" in guard:
                    rules_text = json.dumps(guard["rules"]).lower()
                    matched = sum(1 for anti in gold_anti if any(kw in rules_text for kw in anti.lower().split("_")))
                    scores["anti_rule_coverage"] = matched / max(1, len(gold_anti))
            except Exception:
                scores["guardrail_valid"] = 0.0

        if transcript:
            blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))
            cues = ["guard", "prevent", "error", "mistake", "avoid", "anti"]
            hits = sum(1 for c in cues if c in blob.lower())
            scores["transcript_prevention_signals"] = hits / len(cues)

        return scores


class SourceConflictResolutionGrader(CapabilityGrader):
    """Grader for C5: Source Conflict Resolution."""

    def grade(self, transcript: list[dict] | None = None) -> dict:
        scores = {}

        required = ["evidence_ranking.json", "conflict_resolution.md", "result.json", "summary.md", "manifest.csv"]
        scores.update(check_required_files(self.results_dir, required))

        # Check evidence priority
        ranking_path = self.results_dir / "evidence_ranking.json"
        if ranking_path.exists():
            try:
                ranking = json.loads(ranking_path.read_text(encoding="utf-8"))
                gold_priority = self.oracle.get("gold_evidence_priority", [])
                if isinstance(ranking, list) and gold_priority:
                    # Check ranking order matches gold priority
                    ranking_sources = [r.get("source", "").lower() for r in ranking if isinstance(r, dict)]
                    gold_sources = [g.lower() for g in gold_priority]
                    # Simple: first source in ranking should match first in gold
                    if ranking_sources and gold_sources:
                        scores["top_source_correct"] = 1.0 if ranking_sources[0] == gold_sources[0] else 0.0
            except Exception:
                scores["ranking_valid"] = 0.0

        if transcript:
            blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))
            cues = ["evidence", "conflict", "priority", "rank", "source", "arbitration"]
            hits = sum(1 for c in cues if c in blob.lower())
            scores["transcript_conflict_signals"] = hits / len(cues)

        return scores


class MemoryOperationSelectionGrader(CapabilityGrader):
    """Grader for C6: Memory Operation Selection."""

    def grade(self, transcript: list[dict] | None = None) -> dict:
        scores = {}

        required = ["operation_log.json", "result.json", "summary.md", "manifest.csv"]
        scores.update(check_required_files(self.results_dir, required))

        # Check operation selection
        log_path = self.results_dir / "operation_log.json"
        if log_path.exists():
            try:
                log = json.loads(log_path.read_text(encoding="utf-8"))
                gold_ops = self.oracle.get("gold_memory_operation", [])
                if isinstance(log, list):
                    ops = [entry.get("operation", "").lower() for entry in log if isinstance(entry, dict)]
                    matched = sum(1 for g in gold_ops if any(g.lower() in o for o in ops))
                    scores["operation_coverage"] = matched / max(1, len(gold_ops))
            except Exception:
                scores["operation_log_valid"] = 0.0

        if transcript:
            blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))
            cues = ["memory", "operation", "recall", "store", "cache", "graph"]
            hits = sum(1 for c in cues if c in blob.lower())
            scores["transcript_memory_signals"] = hits / len(cues)

        return scores


class GoalInterruptionResumptionGrader(CapabilityGrader):
    """Grader for C7: Goal Interruption and Task Resumption."""

    def grade(self, transcript: list[dict] | None = None) -> dict:
        scores = {}

        required = ["resume_state.json", "pipeline_progress.md", "result.json", "summary.md", "manifest.csv"]
        scores.update(check_required_files(self.results_dir, required))

        # Check resume state
        resume_path = self.results_dir / "resume_state.json"
        if resume_path.exists():
            try:
                state = json.loads(resume_path.read_text(encoding="utf-8"))
                required_keys = ["checkpoint", "processed", "pending"]
                for key in required_keys:
                    scores[f"resume_{key}_present"] = 1.0 if key in state else 0.0
            except Exception:
                scores["resume_state_valid"] = 0.0

        if transcript:
            blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))
            cues = ["resume", "checkpoint", "interrupt", "pending", "continuation"]
            hits = sum(1 for c in cues if c in blob.lower())
            scores["transcript_resumption_signals"] = hits / len(cues)

        return scores


class StalenessApplicabilityGrader(CapabilityGrader):
    """Grader for C8: Staleness and Applicability Judgment."""

    def grade(self, transcript: list[dict] | None = None) -> dict:
        scores = {}

        required = ["staleness_decision.json", "result.json", "summary.md", "manifest.csv"]
        scores.update(check_required_files(self.results_dir, required))

        # Check staleness decisions
        decision_path = self.results_dir / "staleness_decision.json"
        if decision_path.exists():
            try:
                decision = json.loads(decision_path.read_text(encoding="utf-8"))
                # Should have entries classified as active/stale/conditional
                if isinstance(decision, list):
                    classifications = [d.get("status", "").lower() for d in decision if isinstance(d, dict)]
                    has_active = "active" in classifications
                    has_stale = "stale" in classifications
                    scores["staleness_classification_active"] = 1.0 if has_active else 0.0
                    scores["staleness_classification_stale"] = 1.0 if has_stale else 0.0
            except Exception:
                scores["staleness_decision_valid"] = 0.0

        if transcript:
            blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))
            cues = ["stale", "applicable", "deprecated", "latest", "invalidate"]
            hits = sum(1 for c in cues if c in blob.lower())
            scores["transcript_staleness_signals"] = hits / len(cues)

        return scores


# ===================== Main Grading Entry Point =====================

CAPABILITY_GRADERS = {
    "Recent Constraint Tracking": RecentConstraintTrackingGrader,
    "Version Update": VersionUpdateGrader,
    "Procedure Transfer": ProcedureTransferGrader,
    "Repeated Mistake Prevention": RepeatedMistakePreventionGrader,
    "Source Conflict Resolution": SourceConflictResolutionGrader,
    "Memory Operation Selection": MemoryOperationSelectionGrader,
    "Goal Interruption and Task Resumption": GoalInterruptionResumptionGrader,
    "Staleness and Applicability Judgment": StalenessApplicabilityGrader,
}


def grade_task(
    task_capability: str,
    workspace_path: str | Path,
    oracle_path: str | Path | None = None,
    scenario_path: str | Path | None = None,
    transcript: list[dict] | None = None,
) -> dict:
    """Main entry point for grading a task.

    Args:
        task_capability: The primary capability being tested
        workspace_path: Path to the task workspace (with results/ subdirectory)
        oracle_path: Optional path to oracle.yaml
        scenario_path: Optional path to scenario.jsonl
        transcript: Optional conversation transcript

    Returns:
        Dict with individual scores and overall_score
    """
    workspace_path = Path(workspace_path)
    results_dir = workspace_path / "results"

    # Load oracle and scenario
    oracle = {}
    if oracle_path:
        oracle = load_oracle(oracle_path)
    else:
        # Try default location
        default_oracle = workspace_path / "oracle.yaml"
        if default_oracle.exists():
            oracle = load_oracle(default_oracle)

    scenario = []
    if scenario_path:
        scenario = load_scenario(scenario_path)
    else:
        default_scenario = workspace_path / "scenario.jsonl"
        if default_scenario.exists():
            scenario = load_scenario(default_scenario)

    # Get appropriate grader
    grader_class = CAPABILITY_GRADERS.get(task_capability, CapabilityGrader)
    grader = grader_class(oracle, scenario, workspace_path)

    # Run capability-specific grading
    scores = grader.grade(transcript)

    # Add generic checks
    manifest_csv = results_dir / "manifest.csv"
    if manifest_csv.exists():
        scores["manifest_consistency"] = check_manifest_consistency(manifest_csv, results_dir)

    # Transcript evidence check
    if transcript:
        blob = "\n".join(str(m.get("content", "")) for m in transcript if isinstance(m, dict))
        generic_cues = ["source", "latest", "constraint", "evidence", "artifact"]
        hits = sum(1 for c in generic_cues if c in blob.lower())
        scores["transcript_evidence_signal"] = hits / len(generic_cues)

    # Calculate overall score
    scores["overall_score"] = aggregate_scores(scores)
    return scores


def run_grading_from_task_md(
    task: dict,
    transcript: list[dict] | None = None,
    workspace_override: str | None = None,
) -> tuple[dict, str | None]:
    """Run grading from a parsed task markdown dict.

    This is the main entry point used by run_batch.py.

    Args:
        task: Parsed task dict from parse_task_md
        transcript: Optional conversation transcript
        workspace_override: Optional override for workspace path

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
        )
        return scores, None
    except Exception as e:
        import traceback
        return {"overall_score": 0.0}, f"Grading error: {e}\n{traceback.format_exc()}"
