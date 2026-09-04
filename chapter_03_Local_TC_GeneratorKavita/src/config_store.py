import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'config.json'


def load_config():
    if not CONFIG_PATH.exists():
        return {}

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}

    if isinstance(data, dict):
        return data
    return {}


def save_config(data):
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise TypeError('Configuration must be a dictionary.')

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)
    return data


def get(key, default=None):
    return load_config().get(key, default)
