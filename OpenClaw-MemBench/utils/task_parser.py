from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent


def parse_task_md(task_file: Path) -> dict:
    content = task_file.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not fm_match:
        raise ValueError(f"YAML frontmatter not found: {task_file}")

    metadata = yaml.safe_load(fm_match.group(1))
    body = fm_match.group(2)

    sections: dict[str, str] = {}
    current_section: Optional[str] = None
    lines: list[str] = []

    for line in body.split("\n"):
        header = re.match(r"^##\s+(.+)$", line)
        if header:
            if current_section is not None:
                sections[current_section] = "\n".join(lines).strip()
            current_section = header.group(1)
            lines = []
        else:
            lines.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(lines).strip()

    def strip_codeblock(raw: str) -> str:
        s = re.sub(r"^```[^\n]*\n?", "", raw.strip())
        s = re.sub(r"\n?```$", "", s).strip()
        return s

    task_id = metadata.get("id", task_file.stem)
    timeout_seconds = int(metadata.get("timeout_seconds", 900))

    prompt = sections.get("Prompt", "").strip()
    automated_checks = strip_codeblock(sections.get("Automated Checks", ""))
    workspace_path = strip_codeblock(sections.get("Workspace Path", ""))
    skills_raw = strip_codeblock(sections.get("Skills", ""))
    env_raw = strip_codeblock(sections.get("Env", ""))
    warmup_raw = strip_codeblock(sections.get("Warmup", ""))

    if not workspace_path:
        raise ValueError(f"Missing ## Workspace Path in task file: {task_file}")

    wp = Path(workspace_path)
    if not wp.is_absolute():
        wp = (ROOT_DIR / wp).resolve()

    skills = [
        s.strip()
        for s in re.split(r"[\n,]", skills_raw)
        if s and s.strip()
    ]
    env_vars: dict[str, str] = {}
    for line in env_raw.splitlines():
        ln = line.strip()
        if not ln or ln.startswith("#"):
            continue
        if "=" not in ln:
            continue
        k, v = ln.split("=", 1)
        env_vars[k.strip()] = v.strip()

    scenario_path = wp / "scenario.jsonl"
    oracle_path = wp / "oracle.yaml"

    return {
        "task_id": task_id,
        "name": metadata.get("name", task_id),
        "category": metadata.get("category", task_file.parent.name),
        "capability": metadata.get("capability", ""),
        "timeout_seconds": timeout_seconds,
        "prompt": prompt,
        "automated_checks": automated_checks,
        "skills": skills,
        "env": env_vars,
        "warmup": warmup_raw,
        "workspace_path": str(wp),
        "scenario_path": str(scenario_path),
        "oracle_path": str(oracle_path),
        "task_file": str(task_file.resolve()),
    }
