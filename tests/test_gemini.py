import importlib
import os
import sys
import types
import unittest


def load_gemini_client_module():
	google_module = sys.modules.get("google")
	if google_module is None:
		google_module = types.ModuleType("google")
		google_module.__path__ = []
		sys.modules["google"] = google_module

	genai_module = types.ModuleType("google.generativeai")

	def configure(**kwargs):
		return kwargs

	class GenerativeModel:
		def __init__(self, *args, **kwargs):
			self.args = args
			self.kwargs = kwargs

	genai_module.configure = configure
	genai_module.GenerativeModel = GenerativeModel
	sys.modules["google.generativeai"] = genai_module
	setattr(google_module, "generativeai", genai_module)

	module = importlib.import_module("core.gemini_client")
	return importlib.reload(module)


class GeminiClientJsonParsingTests(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		module = load_gemini_client_module()
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

	def test_client_uses_backend_pinned_model_even_when_env_override_exists(self):
		os.environ["GEMINI_API_KEY"] = "test-key"
		os.environ["GEMINI_MODEL"] = "models/gemini-3.1-pro"
		module = load_gemini_client_module()
		client = module.GeminiClient()
		self.assertEqual(client.model.kwargs["model_name"], module.GEMINI_MODEL_NAME)


if __name__ == "__main__":
	unittest.main()
