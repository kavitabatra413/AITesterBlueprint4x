import json
import os
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import config_store


class ConfigStoreTests(unittest.TestCase):
    def test_load_config_returns_empty_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_base = config_store.BASE_DIR
            original_path = config_store.CONFIG_PATH
            config_store.BASE_DIR = Path(tmp_dir)
            config_store.CONFIG_PATH = config_store.BASE_DIR / 'config.json'
            try:
                data = config_store.load_config()
                self.assertEqual(data, {})
            finally:
                config_store.BASE_DIR = original_base
                config_store.CONFIG_PATH = original_path

    def test_save_config_persists_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_base = config_store.BASE_DIR
            original_path = config_store.CONFIG_PATH
            config_store.BASE_DIR = Path(tmp_dir)
            config_store.CONFIG_PATH = config_store.BASE_DIR / 'config.json'
            try:
                payload = {'jira_base_url': 'https://example.atlassian.net', 'llm_provider': 'ollama'}
                result = config_store.save_config(payload)
                self.assertEqual(result, payload)
                with open(config_store.CONFIG_PATH, 'r', encoding='utf-8') as file:
                    saved = json.load(file)
                self.assertEqual(saved, payload)
            finally:
                config_store.BASE_DIR = original_base
                config_store.CONFIG_PATH = original_path


if __name__ == '__main__':
    unittest.main()
