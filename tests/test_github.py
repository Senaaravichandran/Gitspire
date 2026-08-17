import unittest

from core.github_client import GitHubClient
from core.translation import TranslationResult


class FakeTranslationService:
	enabled = True

	def translate_text(self, text: str) -> TranslationResult:
		if text.startswith("jp:"):
			translated = text.replace("jp:", "EN: ", 1)
			return TranslationResult(text, translated, "ja", True)
		return TranslationResult(text, text, "en", False)


class GitHubClientTests(unittest.TestCase):

	def setUp(self):
		self.client = GitHubClient()
		self.client.translation = FakeTranslationService()

	def test_parse_repo_url_accepts_git_suffix(self):
		owner, repo = self.client.parse_repo_url("https://github.com/octocat/Hello-World.git")
		self.assertEqual(owner, "octocat")
		self.assertEqual(repo, "Hello-World")

	def test_parse_repo_url_rejects_non_github_host(self):
		with self.assertRaises(ValueError):
			self.client.parse_repo_url("https://example.com/octocat/Hello-World")

	def test_parse_repo_url_rejects_extra_path_segments(self):
		with self.assertRaises(ValueError):
			self.client.parse_repo_url("https://github.com/octocat/Hello-World/issues")

	def test_parse_repo_url_rejects_query_parameters(self):
		with self.assertRaises(ValueError):
			self.client.parse_repo_url("https://github.com/octocat/Hello-World?tab=readme")

	def test_build_archaeology_context_tracks_languages_and_reorders_commits(self):
		context, stats = self.client.build_archaeology_context(
			{
				"metadata": {"description": "Demo repo"},
				"key_files": {"README.md": "# Demo"},
				"commits": [
					{
						"sha": "new1234",
						"message": "newest commit",
						"author": "Alice",
						"date": "2024-03-02T00:00:00Z",
					},
					{
						"sha": "old1234",
						"message": "jp:oldest commit",
						"author": "Bob",
						"date": "2024-03-01T00:00:00Z",
					},
				],
				"issues": [
					{
						"number": 7,
						"title": "jp:queue failure",
						"body": "Needs retry policy",
						"state": "open",
					}
				],
				"pull_requests": [
					{
						"number": 3,
						"title": "Add worker metrics",
						"body": "jp:add observability",
						"state": "merged",
					}
				],
			}
		)

		self.assertIn("TOTAL CONTEXT:", context)
		self.assertLess(context.index("jp:oldest commit"), context.index("newest commit"))
		self.assertIn("languages_detected: en, ja", context)
		self.assertEqual(stats["languages_detected"], ["en", "ja"])
		self.assertGreaterEqual(stats["translated_artifact_count"], 1)


if __name__ == "__main__":
	unittest.main()
