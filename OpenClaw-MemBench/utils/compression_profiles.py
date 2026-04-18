from __future__ import annotations

from pathlib import Path


KEYWORDS = [
    "constraint",
    "latest",
    "version",
    "must",
    "error",
    "conflict",
    "evidence",
    "resume",
    "stale",
    "deprecated",
    "schema",
    "path",
    "output",
    "episode",
]


def _load_workspace_files(workspace_path: str) -> list[tuple[str, str]]:
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
    return files


def _to_chunk(path: str, text: str) -> str:
    return f"[FILE] {path}\n{text}"


def _sliding_window(text: str, budget_chars: int) -> str:
    if budget_chars <= 0 or len(text) <= budget_chars:
        return text
    return text[-budget_chars:]


def _keyword_extract(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    kept = [ln for ln in lines if any(k in ln.lower() for k in KEYWORDS)]
    if not kept:
        kept = lines[:12]
    return "\n".join(kept)


def _lcm_proxy(text: str) -> str:
    # Approximate a two-layer summary: signal lines + recent raw tail.
    signal = _keyword_extract(text)
    tail = _sliding_window(text, 2500)
    return f"[LCM_PROXY_SUMMARY]\n{signal}\n\n[RECENT_RAW_TAIL]\n{tail}"


def _episode_digest(text: str) -> str:
    out: list[str] = []
    block: list[str] = []
    episode_id = 0
    for ln in text.splitlines():
        low = ln.lower()
        if "episode" in low and len(block) > 6:
            episode_id += 1
            out.append(f"Episode {episode_id}: {' '.join(block[:4])}")
            block = []
        if ln.strip():
            block.append(ln.strip())
    if block:
        episode_id += 1
        out.append(f"Episode {episode_id}: {' '.join(block[:4])}")
    return "\n".join(out[:80])


def build_context(workspace_path: str, method: str, budget_chars: int) -> dict:
    files = _load_workspace_files(workspace_path)
    if not files:
        return {
            "method": method,
            "raw_chars": 0,
            "compressed_chars": 0,
            "reduction_ratio": 0.0,
            "context": "No workspace context files found.",
        }

    merged = "\n\n".join([_to_chunk(path, text) for path, text in files])
    raw_chars = len(merged)
    method = (method or "full").strip().lower()

    if method in {"full", "full-context", "none"}:
        compressed = merged
    elif method in {"sliding-window", "window"}:
        compressed = _sliding_window(merged, budget_chars)
    elif method in {"keyword", "keyword-extract"}:
        compressed = _keyword_extract(merged)
        compressed = _sliding_window(compressed, budget_chars)
    elif method in {"lcm", "lcm-proxy", "hierarchical"}:
        compressed = _lcm_proxy(merged)
        compressed = _sliding_window(compressed, budget_chars)
    elif method in {"episode", "episode-digest"}:
        compressed = _episode_digest(merged)
        compressed = _sliding_window(compressed, budget_chars)
    else:
        compressed = _sliding_window(merged, budget_chars)

    # Compression method should never enlarge context beyond raw source text.
    if len(compressed) > raw_chars:
        compressed = compressed[:raw_chars]

    compressed_chars = len(compressed)
    reduction_ratio = 0.0
    if raw_chars > 0:
        reduction_ratio = round(1.0 - (compressed_chars / raw_chars), 4)

    return {
        "method": method,
        "raw_chars": raw_chars,
        "compressed_chars": compressed_chars,
        "reduction_ratio": reduction_ratio,
        "context": compressed,
    }
