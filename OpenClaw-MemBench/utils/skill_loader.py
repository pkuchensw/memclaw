from __future__ import annotations

from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT_DIR / "skills"
REGISTRY_PATH = SKILL_DIR / "registry.yaml"


def _load_registry() -> dict[str, dict]:
    if not REGISTRY_PATH.exists():
        return {}
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    skills = data.get("skills", [])
    out: dict[str, dict] = {}
    for s in skills:
        sid = str(s.get("id", "")).strip()
        if sid:
            out[sid] = s
    return out


def load_skill_prompts(skill_ids: list[str]) -> list[dict]:
    registry = _load_registry()
    prompts: list[dict] = []
    for sid in skill_ids:
        meta = registry.get(sid)
        if not meta:
            continue
        rel = str(meta.get("file", "")).strip()
        if not rel:
            continue
        p = SKILL_DIR / rel
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            continue
        prompts.append(
            {
                "id": sid,
                "name": str(meta.get("name", sid)),
                "content": content,
            }
        )
    return prompts
