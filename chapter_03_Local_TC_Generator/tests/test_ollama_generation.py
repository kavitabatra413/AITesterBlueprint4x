import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import llm_client


class OllamaGenerationEndpointTest(unittest.TestCase):
    @patch('llm_client.check_ollama', return_value=True)
    @patch('llm_client.requests.post')
    @patch('llm_client.read_config')
    def test_generate_uses_native_ollama_endpoint(self, mock_read_config, mock_post, mock_check_ollama):
        mock_read_config.return_value = {
            'ollama_url': 'http://localhost:11434',
            'ollama_model': 'llama3.2:3b',
            'ollama_token': '',
            'llm_provider': 'ollama',
        }

        fake_response = types.SimpleNamespace(
            status_code=200,
            ok=True,
            json=lambda: {'response': 'Generated text'},
            raise_for_status=lambda: None,
            text='Generated text',
        )
        mock_post.return_value = fake_response

        result = llm_client.generate('hello', timeout=10)

        self.assertEqual(result, 'Generated text')
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.args[0], 'http://localhost:11434/api/generate')
        self.assertEqual(mock_post.call_args.kwargs['json']['model'], 'llama3.2:3b')
        self.assertFalse(mock_post.call_args.kwargs['json'].get('stream', True))


if __name__ == '__main__':
    unittest.main()
