import json
import os
import time
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
            return "\n".join([p for p in parts if p])
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
    timeout_override = int(os.environ.get("MB_REQUEST_TIMEOUT", "0"))
    if timeout_override > 0:
        timeout_seconds = timeout_override
    connect_timeout = float(os.environ.get("MB_CONNECT_TIMEOUT", "10"))
    read_timeout = float(os.environ.get("MB_READ_TIMEOUT", str(timeout_seconds)))
    request_timeout = (max(1.0, connect_timeout), max(5.0, read_timeout))
    max_retries = int(os.environ.get("MB_MAX_RETRIES", "4"))
    retry_wait = float(os.environ.get("MB_RETRY_BASE_SECONDS", "3"))

    request_path = os.environ["MB_REQUEST_PATH"]
    response_path = os.environ["MB_RESPONSE_PATH"]
    transcript_path = os.environ["MB_TRANSCRIPT_PATH"]
    assistant_path = os.environ["MB_ASSISTANT_PATH"]

    payload = json.loads(open(request_path, "r", encoding="utf-8").read())
    if provider == "anthropic":
        replay_messages = []
        for m in payload.get("messages", [])[1:]:
            role = m.get("role", "user")
            if role not in {"user", "assistant"}:
                role = "user"
            replay_messages.append({"role": role, "content": m.get("content", "")})
        payload = {
            "model": payload["model"],
            "max_tokens": payload.get("max_tokens", 4096),
            "temperature": payload.get("temperature", 0),
            "system": payload["messages"][0]["content"],
            "messages": replay_messages,
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
        resp = None
        last_err = None
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=request_timeout, verify=verify_ssl)
            except (requests.ReadTimeout, requests.ConnectTimeout, requests.ConnectionError, requests.Timeout) as req_err:
                last_err = req_err
                if attempt < max_retries:
                    time.sleep(retry_wait * (2 ** attempt))
                    continue
                raise
            if resp.status_code < 400:
                break
            if resp.status_code in {429, 500, 502, 503, 504} and attempt < max_retries:
                time.sleep(retry_wait * (2 ** attempt))
                continue
            resp.raise_for_status()

        if resp is None:
            if last_err is not None:
                raise last_err
            raise RuntimeError("No HTTP response returned")

        resp.raise_for_status()
        response_json = resp.json()
        assistant_text = _extract_assistant_text(response_json)

        transcript = [
            {"role": "system", "content": payload["messages"][0]["content"]},
            *payload["messages"][1:],
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
