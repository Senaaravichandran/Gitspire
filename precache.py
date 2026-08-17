import asyncio
from core.github_client import GitHubClient
from core.gemini_client import GeminiClient
from core.firebase_client import FirebaseClient
from core.parser import parse_knowledge_core

async def precache(repo_url):
  gh = GitHubClient()
  gem = GeminiClient()
  fb = FirebaseClient()
  owner, repo = gh.parse_repo_url(repo_url)
  bundle = await gh.fetch_repository_bundle(owner, repo)
  context, translation_metadata = gh.build_archaeology_context(bundle)
  raw = await gem.analyze_repository(context)
  core = parse_knowledge_core(repo_url, raw, translation_metadata)
  await fb.save_knowledge_core(repo_url, core.model_dump())
  print(f"Cached: {repo_url}")

repos = [
  "https://github.com/psf/requests",
  "https://github.com/pallets/flask",
  "https://github.com/fastapi/full-stack-fastapi-template",
]
asyncio.run(asyncio.gather(*[precache(r) for r in repos]))