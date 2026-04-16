from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.task_parser import parse_task_md
from utils.grading import aggregate_scores, write_summary, format_table

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT_DIR / os.environ.get("TASKS_SUBDIR", "tasks")
OUTPUT_DIR = ROOT_DIR / os.environ.get("OUTPUT_SUBDIR", "outputs")


def _to_bool(val: str, default: bool = True) -> bool:
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _extract_assistant_text(payload: dict) -> str:
    if not isinstance(payload, dict):
        return ""

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                    parts.append(str(item.get("text", "")))
            return "\n".join([p for p in parts if p])

    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    if isinstance(payload.get("response"), str):
        return payload["response"]

    content = payload.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join([p for p in parts if p])
    return ""


def run_automated_checks(task: dict, transcript: list[dict]) -> tuple[dict, str | None]:
    checks = task.get("automated_checks", "").strip()
    if not checks:
        return {"overall_score": 0.0}, None

    scope: dict = {}
    try:
        exec(checks, scope)
        grade_fn = scope.get("grade")
        if not callable(grade_fn):
            return {}, "Automated Checks missing callable grade()"

        raw_scores = grade_fn(transcript=transcript, workspace_path=task["workspace_path"])
        if not isinstance(raw_scores, dict):
            return {}, "grade() must return a dict"

        numeric = {k: v for k, v in raw_scores.items() if isinstance(v, (int, float))}
        if "overall_score" not in raw_scores:
            raw_scores["overall_score"] = aggregate_scores(numeric)
        return raw_scores, None
    except Exception:
        return {}, traceback.format_exc()


def _build_prompts(task: dict, workspace_path_for_agent: str) -> tuple[str, str]:
    system_prompt = (
        "You are an OpenClaw benchmark agent. "
        "Use tools if available and complete the task with deterministic outputs."
    )
    user_prompt = (
        f"{task['prompt']}\n\n"
        "Execution context:\n"
        f"- Workspace absolute path: {workspace_path_for_agent}\n"
        f"- Required result directory: {Path(workspace_path_for_agent) / 'results'}\n"
        "- You must produce files in the required result directory.\n"
    )
    return system_prompt, user_prompt


def run_task_via_api(task: dict, base_url: str, path: str, model: str, api_key: str,
                     verify_ssl: bool, temperature: float, output_dir: Path,
                     max_tokens: int,
                     provider: str = "openai") -> tuple[list[dict], dict, str | None]:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

    system_prompt, user_prompt = _build_prompts(task, task["workspace_path"])

    provider = provider.strip().lower()
    if provider == "anthropic":
        payload = {
            "model": model,
            "max_tokens": 4096,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if api_key:
            headers["x-api-key"] = api_key
    else:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

    timeout_seconds = max(60, int(task.get("timeout_seconds", 900)))

    try:
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout_seconds,
            verify=verify_ssl,
        )
        resp.raise_for_status()
        response_json = resp.json()
        assistant_text = _extract_assistant_text(response_json)

        transcript = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_text},
        ]

        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "request.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (output_dir / "response.json").write_text(
            json.dumps(response_json, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (output_dir / "transcript.json").write_text(
            json.dumps(transcript, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (output_dir / "assistant.txt").write_text(assistant_text or "", encoding="utf-8")

        return transcript, response_json, None
    except requests.HTTPError as http_err:
        output_dir.mkdir(parents=True, exist_ok=True)
        body = ""
        if http_err.response is not None:
            body = http_err.response.text or ""
        (output_dir / "http_error_body.txt").write_text(body, encoding="utf-8")
        return [], {}, f"{traceback.format_exc()}\nHTTP body saved: {output_dir / 'http_error_body.txt'}"
    except Exception:
        return [], {}, traceback.format_exc()


def run_task_via_docker(task: dict, base_url: str, path: str, model: str, api_key: str,
                        verify_ssl: bool, temperature: float, output_dir: Path,
                        max_tokens: int,
                        image: str, network: str, extra_args: str,
                        workspace_mount: str, output_mount: str,
                        container_prefix: str, provider: str = "openai") -> tuple[list[dict], dict, str | None]:
    output_dir.mkdir(parents=True, exist_ok=True)

    image_check = subprocess.run(
        ["docker", "image", "inspect", image],
        capture_output=True,
        text=True,
    )
    if image_check.returncode != 0:
        return [], {}, f"Docker image not found: {image}. Build it first."

    system_prompt, user_prompt = _build_prompts(task, workspace_mount)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    request_path = output_dir / "request.json"
    response_path = output_dir / "response.json"
    transcript_path = output_dir / "transcript.json"
    assistant_path = output_dir / "assistant.txt"
    runner_path = output_dir / "docker_runner.py"

    request_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    runner_code = """
import json
import os
import traceback
import requests

def _extract_assistant_text(payload):
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                    parts.append(str(item.get("text", "")))
            return "\\n".join([p for p in parts if p])
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    if isinstance(payload.get("response"), str):
        return payload["response"]
    return ""

def main():
    base_url = os.environ["MB_BASE_URL"]
    path = os.environ["MB_PATH"]
    provider = os.environ.get("MB_PROVIDER", "openai").strip().lower()
    api_key = os.environ.get("MB_API_KEY", "")
    verify_ssl = os.environ.get("MB_VERIFY_SSL", "true").lower() in {"1", "true", "yes", "y", "on"}
    timeout_seconds = int(os.environ.get("MB_TIMEOUT", "900"))

    request_path = os.environ["MB_REQUEST_PATH"]
    response_path = os.environ["MB_RESPONSE_PATH"]
    transcript_path = os.environ["MB_TRANSCRIPT_PATH"]
    assistant_path = os.environ["MB_ASSISTANT_PATH"]

    payload = json.loads(open(request_path, "r", encoding="utf-8").read())
    if provider == "anthropic":
        payload = {
            "model": payload["model"],
            "max_tokens": payload.get("max_tokens", 4096),
            "temperature": payload.get("temperature", 0),
            "system": payload["messages"][0]["content"],
            "messages": [{"role": "user", "content": payload["messages"][1]["content"]}],
        }
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if api_key:
            headers["x-api-key"] = api_key
    else:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=max(60, timeout_seconds), verify=verify_ssl)
        resp.raise_for_status()
        response_json = resp.json()
        assistant_text = _extract_assistant_text(response_json)

        transcript = [
            {"role": "system", "content": payload["messages"][0]["content"]},
            {"role": "user", "content": payload["messages"][1]["content"]},
            {"role": "assistant", "content": assistant_text},
        ]

        open(response_path, "w", encoding="utf-8").write(json.dumps(response_json, indent=2, ensure_ascii=False))
        open(transcript_path, "w", encoding="utf-8").write(json.dumps(transcript, indent=2, ensure_ascii=False))
        open(assistant_path, "w", encoding="utf-8").write(assistant_text or "")
    except Exception:
        open(response_path, "w", encoding="utf-8").write(json.dumps({"error": traceback.format_exc()}, indent=2, ensure_ascii=False))
        raise

if __name__ == "__main__":
    main()
""".strip()
    runner_path.write_text(runner_code + "\n", encoding="utf-8")

    container_name = f"{container_prefix}-{task['task_id'].lower().replace('_', '-')}-{uuid.uuid4().hex[:8]}"
    docker_cmd = [
        "docker", "run", "--rm",
        "--name", container_name,
        "--network", network,
        "-v", f"{task['workspace_path']}:{workspace_mount}",
        "-v", f"{output_dir}:{output_mount}",
        "-e", f"MB_BASE_URL={base_url}",
        "-e", f"MB_PATH={path}",
        "-e", f"MB_PROVIDER={provider}",
        "-e", f"MB_API_KEY={api_key}",
        "-e", f"MB_VERIFY_SSL={'true' if verify_ssl else 'false'}",
        "-e", f"MB_TIMEOUT={int(task.get('timeout_seconds', 900))}",
        "-e", f"MB_REQUEST_PATH={output_mount}/request.json",
        "-e", f"MB_RESPONSE_PATH={output_mount}/response.json",
        "-e", f"MB_TRANSCRIPT_PATH={output_mount}/transcript.json",
        "-e", f"MB_ASSISTANT_PATH={output_mount}/assistant.txt",
    ]
    if extra_args.strip():
        docker_cmd.extend(extra_args.strip().split())
    docker_cmd.extend([image, "python", f"{output_mount}/docker_runner.py"])

    proc = subprocess.run(docker_cmd, capture_output=True, text=True)
    (output_dir / "docker_stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (output_dir / "docker_stderr.log").write_text(proc.stderr or "", encoding="utf-8")

    if proc.returncode != 0:
        return [], {}, (
            f"Docker run failed (exit={proc.returncode}). "
            f"See {output_dir / 'docker_stderr.log'}"
        )

    if not transcript_path.exists():
        return [], {}, "Docker execution finished but transcript.json was not generated."

    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    response_json = {}
    if response_path.exists():
        try:
            response_json = json.loads(response_path.read_text(encoding="utf-8"))
        except Exception:
            response_json = {}

    return transcript, response_json, None


def collect_tasks(category: str | None = None) -> list[Path]:
    if category:
        return sorted((TASKS_DIR / category).glob("*.md"))

    files: list[Path] = []
    for d in sorted(TASKS_DIR.iterdir()):
        if d.is_dir():
            files.extend(sorted(d.glob("*.md")))
    return files


def run_single(task_file: Path, dry_run: bool = False) -> dict:
    task = parse_task_md(task_file)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / task["category"] / task["task_id"] / run_stamp

    result = {
        "task_id": task["task_id"],
        "category": task["category"],
        "status": "ok",
        "overall_score": 0.0,
        "error": None,
        "task_file": str(task_file),
        "output_dir": str(run_dir),
    }

    if dry_run:
        score_components = {
            "has_prompt": 1.0 if task["prompt"] else 0.0,
            "has_checks": 1.0 if task["automated_checks"] else 0.0,
            "workspace_exists": 1.0 if Path(task["workspace_path"]).exists() else 0.0,
        }
        result["overall_score"] = aggregate_scores(score_components)
        result["score_components"] = score_components
        return result

    base_url = os.environ.get("OPENCLAW_BASE_URL", "http://127.0.0.1:18789")
    model = os.environ.get("OPENCLAW_MODEL", "anthropic/claude-sonnet-4-5")
    api_key = os.environ.get("OPENCLAW_API_KEY", "")
    chat_path = os.environ.get("OPENCLAW_CHAT_COMPLETIONS_PATH", "/v1/chat/completions")
    provider = os.environ.get("OPENCLAW_API_PROVIDER", "openai").strip().lower()
    verify_ssl = _to_bool(os.environ.get("OPENCLAW_VERIFY_SSL", "true"), default=True)
    temperature = float(os.environ.get("OPENCLAW_TEMPERATURE", "0"))
    max_tokens = int(os.environ.get("OPENCLAW_MAX_TOKENS", "2048"))
    runtime = os.environ.get("OPENCLAW_RUNTIME", "api").strip().lower()

    docker_image = os.environ.get("DOCKER_IMAGE", "openclaw-membench-executor:latest")
    docker_network = os.environ.get("DOCKER_NETWORK", "host")
    docker_extra_args = os.environ.get("DOCKER_EXTRA_ARGS", "")
    docker_workspace_mount = os.environ.get("DOCKER_WORKSPACE_MOUNT", "/tmp_workspace")
    docker_output_mount = os.environ.get("DOCKER_OUTPUT_MOUNT", "/tmp_output")
    docker_prefix = os.environ.get("DOCKER_CONTAINER_PREFIX", "membench")

    if runtime == "docker":
        transcript, _, call_err = run_task_via_docker(
            task=task,
            base_url=base_url,
            path=chat_path,
            model=model,
            api_key=api_key,
            verify_ssl=verify_ssl,
            temperature=temperature,
            max_tokens=max_tokens,
            output_dir=run_dir,
            image=docker_image,
            network=docker_network,
            extra_args=docker_extra_args,
            workspace_mount=docker_workspace_mount,
            output_mount=docker_output_mount,
            container_prefix=docker_prefix,
            provider=provider,
        )
    else:
        transcript, _, call_err = run_task_via_api(
            task=task,
            base_url=base_url,
            path=chat_path,
            model=model,
            api_key=api_key,
            verify_ssl=verify_ssl,
            temperature=temperature,
            max_tokens=max_tokens,
            output_dir=run_dir,
            provider=provider,
        )
    if call_err:
        result["status"] = "api_error"
        result["error"] = call_err
        return result

    scores, check_err = run_automated_checks(task, transcript)
    if check_err:
        result["status"] = "grading_error"
        result["error"] = check_err
        return result

    result["scores"] = scores
    result["overall_score"] = float(scores.get("overall_score", 0.0))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OpenClaw-MemBench")
    parser.add_argument("--category", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Validate tasks and grading blocks only")
    parser.add_argument("--runtime", choices=["api", "docker"], default=None,
                        help="Execution runtime. Overrides OPENCLAW_RUNTIME when provided")
    parser.add_argument("--max-tasks", type=int, default=0, help="Limit the number of tasks to execute")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR / "summary.json"))
    args = parser.parse_args()

    if args.runtime:
        os.environ["OPENCLAW_RUNTIME"] = args.runtime

    task_files = collect_tasks(args.category)
    if args.max_tasks > 0:
        task_files = task_files[:args.max_tasks]
    if not task_files:
        raise SystemExit("No task files found.")

    results = []
    for tf in task_files:
        try:
            results.append(run_single(tf, dry_run=args.dry_run))
        except Exception as exc:
            results.append({
                "task_id": tf.stem,
                "category": tf.parent.name,
                "status": "error",
                "overall_score": 0.0,
                "error": f"{exc}\n{traceback.format_exc()}",
                "task_file": str(tf),
            })

    output_path = Path(args.output)
    write_summary(output_path, results)
    print(format_table(results))
    print(f"\nSummary written to: {output_path}")


if __name__ == "__main__":
    main()
