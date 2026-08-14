import requests
import socket
from urllib.parse import urlparse
from config_store import read_config, normalize_provider


def normalize_value(value):
    if value is None:
        return ""
    return str(value).strip().strip('"').strip("'").strip('“”')


def get_selected_provider():
    cfg = read_config()
    return normalize_provider(cfg.get("llm_provider") or cfg.get("provider") or "ollama")


def get_ollama_settings():
    cfg = read_config()
    url = normalize_value(cfg.get("ollama_url") or "http://127.0.0.1:11434")
    model = normalize_value(cfg.get("ollama_model") or "gemma3:1b")
    token = normalize_value(cfg.get("ollama_token"))
    return url, model, token


def check_ollama(timeout=1.0):
    url, _, _ = get_ollama_settings()
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 11434
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False


def check_groq():
    cfg = read_config()
    key = normalize_value(cfg.get("groq_api_key") or cfg.get("groq_api_token"))
    if not key:
        return False
    try:
        url = "https://api.groq.ai/v1/models"
        resp = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=5)
        return resp.status_code in (200, 401)
    except Exception:
        return False


def generate(prompt: str, timeout=180):
    provider = get_selected_provider()

    if provider == "ollama":
        if not check_ollama():
            return "Ollama selected but local server is unavailable"
        url, model, token = get_ollama_settings()
        try:
            endpoint = url.rstrip('/') + "/api/generate"
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            body = {"model": model, "prompt": prompt, "stream": False}
            resp = requests.post(endpoint, json=body, headers=headers, timeout=timeout)
            resp.raise_for_status()
            try:
                j = resp.json()
                if isinstance(j, dict):
                    if "response" in j:
                        return j.get("response", "")
                    if "content" in j:
                        content = j.get("content")
                        if isinstance(content, list):
                            return "".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
                        return str(content)
                    return str(j)
                return str(j)
            except Exception:
                return resp.text
        except Exception as e:
            return f"Ollama generation failed: {e}"

    cfg = read_config()
    key = normalize_value(cfg.get("groq_api_key") or cfg.get("groq_api_token"))
    if not key:
        return "Groq selected but GROQ_API_KEY not set"
    try:
        url = "https://api.groq.ai/v1/generate"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        body = {"model": "llama-3.1-8b-instant", "input": prompt}
        resp = requests.post(url, json=body, headers=headers, timeout=timeout)
        resp.raise_for_status()
        j = resp.json()
        if "output" in j:
            return j.get("output")
        if "choices" in j:
            return "\n".join([c.get("text", "") for c in j.get("choices", [])])
        return str(j)
    except Exception as e:
        return f"LLM generation failed: {e}"
