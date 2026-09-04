import requests

DEFAULT_OLLAMA_URL = 'http://localhost:11434'
DEFAULT_OLLAMA_MODEL = 'gemma3:1b'
DEFAULT_GROQ_MODEL = 'llama-3.1-8b-instant'


def _config_value(config, key, fallback=''):
    if not isinstance(config, dict):
        return fallback
    value = config.get(key)
    return value if value not in (None, '') else fallback


def _normalize_provider(value):
    provider = str(value or 'ollama').strip().lower()
    if provider in {'groq', 'groq_ai', 'groq-ai'}:
        return 'groq'
    return 'ollama'


def check_ollama(config=None):
    config = config or {}
    ollama_url = _config_value(config, 'ollama_url', DEFAULT_OLLAMA_URL).rstrip('/')
    try:
        response = requests.get(f'{ollama_url}/api/tags', timeout=3)
        return response.status_code == 200
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException):
        return False


def check_groq(config=None):
    config = config or {}
    groq_key = _config_value(config, 'groq_api_key', '')
    if not groq_key:
        return False
    try:
        response = requests.get(
            'https://api.groq.com/openai/v1/models',
            headers={'Authorization': f'Bearer {groq_key}'},
            timeout=5,
        )
        return response.status_code == 200
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException):
        return False


def _call_ollama(prompt, config):
    ollama_url = _config_value(config, 'ollama_url', DEFAULT_OLLAMA_URL).rstrip('/')
    model = _config_value(config, 'ollama_model', DEFAULT_OLLAMA_MODEL)

    response = requests.post(
        f'{ollama_url}/api/generate',
        json={'model': model, 'prompt': prompt, 'stream': False},
        timeout=120,
    )
    response.raise_for_status()

    payload = response.json()
    if isinstance(payload, dict):
        if 'response' in payload and payload.get('response'):
            return payload.get('response')
        if 'content' in payload:
            content = payload.get('content')
            if isinstance(content, list):
                return ''.join(str(item.get('text', '')) for item in content if isinstance(item, dict))
            return str(content)

    if not payload:
        raise ValueError('Ollama returned an empty response.')
    return str(payload)


def _call_groq(prompt, config):
    groq_key = _config_value(config, 'groq_api_key', '')
    if not groq_key:
        raise ValueError('Groq API key is missing.')

    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {groq_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': DEFAULT_GROQ_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.2,
        },
        timeout=120,
    )
    response.raise_for_status()

    payload = response.json()
    choices = payload.get('choices', [])
    if not choices:
        raise ValueError('Groq returned an empty response.')

    message = choices[0].get('message', {})
    content = message.get('content')
    if not content:
        content = choices[0].get('text', '')
    if not content:
        raise ValueError('Groq returned an empty response.')
    return str(content)


def generate_test_cases(prompt, config):
    if not prompt or not str(prompt).strip():
        raise ValueError('The prompt is empty.')

    selected_provider = _normalize_provider(_config_value(config, 'llm_provider', 'ollama'))

    if selected_provider == 'ollama':
        if not check_ollama(config):
            if not _config_value(config, 'groq_api_key', ''):
                raise ValueError('Ollama is unavailable and Groq API key is missing.')
            return _call_groq(prompt, config)
        try:
            result = _call_ollama(prompt, config)
            if not result or not str(result).strip():
                raise ValueError('Ollama returned an invalid or empty response.')
            return result
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as exc:
            if not _config_value(config, 'groq_api_key', ''):
                raise ValueError('Ollama failed and no Groq API key is configured.') from exc
            return _call_groq(prompt, config)

    if selected_provider == 'groq':
        try:
            result = _call_groq(prompt, config)
            if not result or not str(result).strip():
                raise ValueError('Groq returned an invalid or empty response.')
            return result
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as exc:
            raise RuntimeError('Groq failed to generate test cases.') from exc

    raise ValueError('LLM configuration is missing or invalid.')
