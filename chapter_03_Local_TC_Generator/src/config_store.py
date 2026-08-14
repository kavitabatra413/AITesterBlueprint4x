import json
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

def normalize_value(value):
    if value is None:
        return ""
    return str(value).strip().strip('"').strip("'").strip('“”')


def normalize_provider(value):
    provider = normalize_value(value or "ollama").lower()
    if provider in ("groq", "groq_ai", "groq-ai", "g"):
        return "groq"
    return "ollama"


def load_env():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)


def read_config():
    load_env()
    saved_cfg = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved_cfg = json.load(f)
        except Exception:
            saved_cfg = {}

    env_cfg = {
        "jira_base": normalize_value(os.environ.get("JIRA_BASE") or os.environ.get("JIRA_URL") or saved_cfg.get("jira_base")),
        "jira_user": normalize_value(os.environ.get("JIRA_USER") or os.environ.get("JIRA_EMAIL") or os.environ.get("JIRA_EMAIl") or saved_cfg.get("jira_user")),
        "jira_token": normalize_value(os.environ.get("JIRA_TOKEN") or os.environ.get("JIRA_API_TOKEN") or saved_cfg.get("jira_token")),
        "groq_api_key": normalize_value(os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_API_TOKEN") or saved_cfg.get("groq_api_key") or saved_cfg.get("groq_api_token")),
        "ollama_url": normalize_value(os.environ.get("OLLAMA_URL") or saved_cfg.get("ollama_url") or "http://127.0.0.1:11434"),
        "ollama_token": normalize_value(os.environ.get("OLLAMA_TOKEN") or saved_cfg.get("ollama_token")),
        "ollama_model": normalize_value(os.environ.get("OLLAMA_MODEL") or saved_cfg.get("ollama_model") or "gemma3:1b"),
        "llm_provider": normalize_provider(os.environ.get("LLM_PROVIDER") or os.environ.get("MODEL_PROVIDER") or saved_cfg.get("llm_provider") or saved_cfg.get("provider") or "ollama"),
    }

    merged = dict(saved_cfg)
    for key, value in env_cfg.items():
        if value:
            merged[key] = value
    return merged

def write_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return cfg
