import importlib
import os
import sys
import unittest
from unittest.mock import patch, MagicMock


def load_gemini_client_module():
	with patch('httpx.AsyncClient.post'):
		os.environ["MISTRAL"] = "test-key"
		module = importlib.import_module("core.gemini_client")
		return importlib.reload(module)


class GeminiClientJsonParsingTests(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		os.environ["MISTRAL"] = "test-key"
		module = importlib.import_module("core.gemini_client")
		cls.client = module.GeminiClient.__new__(module.GeminiClient)

	def test_safe_parse_json_accepts_markdown_fences(self):
		parsed = self.client._safe_parse_json("```json\n{\"answer\": \"ok\"}\n```")
		self.assertEqual(parsed, {"answer": "ok"})

	def test_safe_parse_json_extracts_embedded_object(self):
		parsed = self.client._safe_parse_json("preface {\"answer\": \"ok\", \"confidence\": \"high\"} trailing")
		self.assertEqual(parsed["answer"], "ok")
		self.assertEqual(parsed["confidence"], "high")

	def test_safe_parse_json_reports_parse_error_for_invalid_payload(self):
		parsed = self.client._safe_parse_json("not-json-at-all")
		self.assertTrue(parsed["parse_error"])
		self.assertIn("not-json-at-all", parsed["raw_preview"])

	def test_client_uses_mistral_api_key(self):
		os.environ["MISTRAL"] = "test-mistral-key"
		with patch('httpx.AsyncClient.post'):
			module = importlib.import_module("core.gemini_client")
			client = module.GeminiClient()
			self.assertEqual(client.api_key, "test-mistral-key")


if __name__ == "__main__":
	unittest.main()
