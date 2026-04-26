from __future__ import annotations

import fnmatch
import json
import os
import shlex
import shutil
import subprocess
import time
import uuid
from pathlib import Path


TMP_WORKSPACE = "/tmp_workspace"


def _run(cmd: list[str], *, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def _prepare_sandbox_workspace(src_workspace: Path, dst_workspace: Path, hidden_patterns: list[str]) -> None:
    if dst_workspace.exists():
        shutil.rmtree(dst_workspace)
    shutil.copytree(src_workspace, dst_workspace)

    hidden = [p.strip() for p in hidden_patterns if p and p.strip()]
    if not hidden:
        return

    for node in sorted(dst_workspace.rglob("*"), reverse=True):
        rel = str(node.relative_to(dst_workspace))
        name = node.name
        if any(fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(name, pattern) for pattern in hidden):
            if node.is_dir():
                shutil.rmtree(node, ignore_errors=True)
            else:
                node.unlink(missing_ok=True)


def _docker_cp_optional(container_name: str, container_path: str, host_path: Path) -> bool:
    host_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["docker", "cp", f"{container_name}:{container_path}", str(host_path)],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _compose_agent_message(system_prompt: str, user_prompt: str, scenario_turns: list[dict]) -> str:
    lines: list[str] = []
    lines.append("[SYSTEM]")
    lines.append(system_prompt.strip())
    lines.append("")

    if scenario_turns:
        lines.append("[SCENARIO_REPLAY]")
        for t in scenario_turns:
            role = str(t.get("role", "user"))
            episode_id = str(t.get("episode_id", "0"))
            content = str(t.get("content", ""))
            lines.append(f"(episode={episode_id}, role={role}) {content}")
        lines.append("")

    lines.append("[TASK]")
    lines.append(user_prompt.strip())
    return "\n".join(lines)


def _extract_assistant_usage_from_chat_jsonl(path: Path) -> dict:
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "total_tokens": 0,
        "request_count": 0,
        "cost_usd": 0.0,
    }
    if not path.exists():
        return totals

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue

        if obj.get("type") != "message":
            continue
        msg = obj.get("message", {})
        if msg.get("role") != "assistant":
            continue

        totals["request_count"] += 1
        usage = msg.get("usage", {}) if isinstance(msg.get("usage", {}), dict) else {}
        totals["input_tokens"] += int(usage.get("input", 0) or 0)
        totals["output_tokens"] += int(usage.get("output", 0) or 0)
        totals["cache_read_tokens"] += int(usage.get("cacheRead", 0) or 0)
        totals["cache_write_tokens"] += int(usage.get("cacheWrite", 0) or 0)
        totals["total_tokens"] += int(usage.get("totalTokens", 0) or 0)
        cost = usage.get("cost", {}) if isinstance(usage.get("cost", {}), dict) else {}
        totals["cost_usd"] += float(cost.get("total", 0.0) or 0.0)

    totals["cost_usd"] = round(totals["cost_usd"], 6)
    return totals


def _chat_jsonl_to_transcript(path: Path) -> list[dict]:
    transcript: list[dict] = []
    if not path.exists():
        return transcript

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("type") != "message":
            continue
        msg = obj.get("message", {})
        role = str(msg.get("role", "assistant"))
        content = msg.get("content", "")
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                    parts.append(str(item.get("text", "")))
            text = "\n".join([p for p in parts if p])
        else:
            text = str(content)
        transcript.append({"role": role, "content": text})

    return transcript


def run_task_in_openclaw_container(
    *,
    task: dict,
    output_dir: Path,
    docker_image: str,
    docker_network: str,
    docker_extra_args: str,
    clear_proxy: bool,
    http_proxy: str,
    https_proxy: str,
    no_proxy: str,
    hidden_patterns: list[str],
    preserve_container: bool,
    model: str,
    skills_root: Path,
    selected_skills: list[str],
    scenario_turns: list[dict],
    system_prompt: str,
    user_prompt: str,
    timeout_seconds: int,
    warmup_script: str,
    gateway_port: int,
    thinking_default: str,
) -> tuple[list[dict], dict, str | None]:
    # Check Docker image exists BEFORE preparing workspace (to fail fast)
    image_check = subprocess.run(
        ["docker", "image", "inspect", docker_image],
        capture_output=True,
        text=True,
    )
    if image_check.returncode != 0:
        return [], {}, f"Docker image not found: {docker_image}"

    output_dir.mkdir(parents=True, exist_ok=True)
    sandbox = output_dir / "sandbox_workspace"
    src_workspace = Path(task["workspace_path"])
    _prepare_sandbox_workspace(src_workspace, sandbox, hidden_patterns)

    # Make sure results dir always exists to simplify downstream checks.
    (sandbox / "results").mkdir(parents=True, exist_ok=True)

    container_name = f"membench-openclaw-{task['task_id'].lower().replace('_', '-')}-{uuid.uuid4().hex[:8]}"

    docker_cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "--network", docker_network,
        "-v", f"{sandbox}:/app:ro",
        docker_image,
        "/bin/bash", "-lc", "tail -f /dev/null",
    ]

    env_args: list[str] = []
    if clear_proxy:
        # Clear proxy env by default, but do not clear keys that are explicitly set below.
        if not http_proxy.strip():
            env_args += ["-e", "HTTP_PROXY=", "-e", "http_proxy="]
        if not https_proxy.strip():
            env_args += ["-e", "HTTPS_PROXY=", "-e", "https_proxy="]
        if not no_proxy.strip():
            env_args += ["-e", "NO_PROXY=", "-e", "no_proxy="]
        env_args += ["-e", "ALL_PROXY=", "-e", "all_proxy="]

    if http_proxy.strip():
        env_args += ["-e", f"HTTP_PROXY={http_proxy}", "-e", f"http_proxy={http_proxy}"]
    if https_proxy.strip():
        env_args += ["-e", f"HTTPS_PROXY={https_proxy}", "-e", f"https_proxy={https_proxy}"]
    if no_proxy.strip():
        env_args += ["-e", f"NO_PROXY={no_proxy}", "-e", f"no_proxy={no_proxy}"]

    if env_args:
        docker_cmd[2:2] = env_args
    if docker_extra_args.strip():
        docker_cmd[2:2] = docker_extra_args.strip().split()

    gateway_log = output_dir / "gateway.log"
    agent_log = output_dir / "agent.log"
    gateway_proc: subprocess.Popen | None = None

    try:
        _run(docker_cmd)

        _run(["docker", "exec", container_name, "mkdir", "-p", TMP_WORKSPACE])
        _run([
            "docker", "exec", container_name, "/bin/bash", "-lc",
            f"cp -r /app/. {TMP_WORKSPACE} && chmod -R u+w {TMP_WORKSPACE} && mkdir -p {TMP_WORKSPACE}/results",
        ])

        if selected_skills:
            _run(["docker", "exec", container_name, "mkdir", "-p", "/root/skills"])
            for skill in selected_skills:
                skill_src = skills_root / skill
                if not skill_src.exists():
                    continue
                _run(["docker", "cp", str(skill_src), f"{container_name}:/root/skills"]) 

        if warmup_script.strip():
            for line in warmup_script.splitlines():
                cmd = line.strip()
                if not cmd or cmd.startswith("#"):
                    continue
                _run([
                    "docker", "exec", container_name, "/bin/bash", "-lc",
                    f"cd {TMP_WORKSPACE} && {cmd}",
                ])

        provider = os.environ.get("OPENCLAW_API_PROVIDER", "openai").strip().lower()
        base_url = os.environ.get("OPENCLAW_BASE_URL", "").strip()
        api_key = os.environ.get("OPENCLAW_API_KEY", "").strip()
        model_id = model.split("/", 1)[1] if "/" in model else model
        if provider == "openai" and base_url and api_key and model_id:
            provider_cfg = {
                "baseUrl": base_url,
                "apiKey": api_key,
                "api": "openai-completions",
                "auth": "api-key",
                "models": [
                    {
                        "id": model_id,
                        "name": model_id,
                        "reasoning": True,
                        "input": ["text", "image"],
                        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                        "contextWindow": 262144,
                        "maxTokens": 65536,
                    }
                ],
            }
            cfg_json = shlex.quote(json.dumps(provider_cfg, ensure_ascii=False))
            _run([
                "docker", "exec", container_name, "/bin/bash", "-lc",
                f"export PATH=/usr/local/bin:$PATH && openclaw config set models.mode merge && openclaw config set models.providers.openai {cfg_json} --strict-json",
            ])

        _run([
            "docker", "exec", container_name, "/bin/bash", "-lc",
            f"export PATH=/usr/local/bin:$PATH && openclaw models set '{model}'",
        ])

        _run([
            "docker", "exec", container_name, "/bin/bash", "-lc",
            "export PATH=/usr/local/bin:$PATH && openclaw config set gateway.mode local",
        ])

        if thinking_default.strip():
            _run([
                "docker", "exec", container_name, "/bin/bash", "-lc",
                f"export PATH=/usr/local/bin:$PATH && openclaw config set agents.defaults.thinkingDefault {thinking_default.strip()}",
            ])

        prompt_text = _compose_agent_message(system_prompt, user_prompt, scenario_turns)
        prompt_path = output_dir / "agent_prompt.txt"
        prompt_path.write_text(prompt_text, encoding="utf-8")
        _run(["docker", "cp", str(prompt_path), f"{container_name}:/tmp/agent_prompt.txt"])

        gateway_file = gateway_log.open("w", encoding="utf-8")
        gateway_proc = subprocess.Popen(
            [
                "docker", "exec", container_name, "/bin/bash", "-lc",
                f"export PATH=/usr/local/bin:$PATH && cd {TMP_WORKSPACE} && openclaw gateway --allow-unconfigured --port {gateway_port}",
            ],
            stdout=gateway_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        time.sleep(2)

        agent_proc = subprocess.run(
            [
                "docker", "exec", container_name, "/bin/bash", "-lc",
                (
                    f"export PATH=/usr/local/bin:$PATH && cd {TMP_WORKSPACE} && "
                    "MSG=$(cat /tmp/agent_prompt.txt) && "
                    f"openclaw agent --session-id chat --timeout {timeout_seconds} --message \"$MSG\""
                ),
            ],
            capture_output=True,
            text=True,
            timeout=max(120, timeout_seconds + 60),
        )
        agent_log.write_text((agent_proc.stdout or "") + "\n" + (agent_proc.stderr or ""), encoding="utf-8")

        if agent_proc.returncode != 0:
            return [], {}, f"openclaw agent exited with code {agent_proc.returncode}"

        chat_path = output_dir / "chat.jsonl"
        _docker_cp_optional(container_name, "/root/.openclaw/agents/main/sessions/chat.jsonl", chat_path)

        task_output = output_dir / "task_output"
        task_output.mkdir(parents=True, exist_ok=True)
        _docker_cp_optional(container_name, "/tmp/openclaw/.", task_output / "openclaw")

        results_dir = output_dir / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        _docker_cp_optional(container_name, f"{TMP_WORKSPACE}/results/.", results_dir)

        transcript = _chat_jsonl_to_transcript(chat_path)
        usage = _extract_assistant_usage_from_chat_jsonl(chat_path)
        return transcript, usage, None
    except subprocess.TimeoutExpired:
        return [], {}, "openclaw agent timed out"
    except Exception as exc:
        return [], {}, str(exc)
    finally:
        if gateway_proc is not None:
            try:
                gateway_proc.terminate()
            except Exception:
                pass
        if not preserve_container:
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
