import json
import os
import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import config_store


class ReadConfigEnvPrecedenceTest(unittest.TestCase):
    def test_env_values_override_saved_config(self):
        tmp_dir = Path(__file__).resolve().parent / 'tmp_env_config'
        tmp_dir.mkdir(exist_ok=True)
        env_path = tmp_dir / '.env'
        env_path.write_text(
            "JIRA_BASE=https://env.example.com\n"
            "JIRA_USER=env.user@example.com\n"
            "JIRA_API_TOKEN=env-token\n"
            "GROQ_API_TOKEN=env-groq-key\n"
            "OLLAMA_URL=http://env-host:11434\n"
            "OLLAMA_MODEL=llama3:2b\n",
            encoding='utf-8',
        )
        config_path = tmp_dir / 'config.json'
        config_path.write_text(json.dumps({
            'jira_base': 'https://saved.example.com',
            'jira_user': 'saved.user@example.com',
            'jira_token': 'saved-token',
            'groq_api_key': 'saved-groq-key',
            'ollama_url': 'http://saved-host:11434',
            'ollama_model': 'gemma3:1b',
        }), encoding='utf-8')

        original_base = config_store.BASE_DIR
        original_config = config_store.CONFIG_PATH
        original_env = os.environ.copy()
        try:
            config_store.BASE_DIR = tmp_dir
            config_store.CONFIG_PATH = config_path
            os.environ.pop('JIRA_BASE', None)
            os.environ.pop('JIRA_USER', None)
            os.environ.pop('JIRA_API_TOKEN', None)
            os.environ.pop('GROQ_API_TOKEN', None)
            os.environ.pop('OLLAMA_URL', None)
            os.environ.pop('OLLAMA_MODEL', None)
            config_store.load_env()
            cfg = config_store.read_config()
            self.assertEqual(cfg['jira_base'], 'https://env.example.com')
            self.assertEqual(cfg['jira_user'], 'env.user@example.com')
            self.assertEqual(cfg['jira_token'], 'env-token')
            self.assertEqual(cfg['groq_api_key'], 'env-groq-key')
            self.assertEqual(cfg['ollama_url'], 'http://env-host:11434')
            self.assertEqual(cfg['ollama_model'], 'llama3:2b')
        finally:
            config_store.BASE_DIR = original_base
            config_store.CONFIG_PATH = original_config
            os.environ.clear()
            os.environ.update(original_env)


if __name__ == '__main__':
    unittest.main()
