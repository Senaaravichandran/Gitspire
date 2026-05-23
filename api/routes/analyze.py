import re
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from api.models.requests import AnalyzeRequest
from api.models.responses import AnalyzeResponse
from core.github_client import GitHubClient
from core.gemini_client import GeminiClient
from core.firebase_client import FirebaseClient
from core.parser import parse_knowledge_core
from core.rate_limiter import analyze_rate_limiter

router = APIRouter()
github_client = GitHubClient()
gemini_client = GeminiClient()
firebase_client = FirebaseClient()

def make_error(status_code: int, error: str, error_code: str):
    return JSONResponse(status_code=status_code, content={"success": False, "error": error, "error_code": error_code})

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest, req: Request):
    # 1. Validate repo_url security via regex
    url = request.repo_url
    if not re.match(r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$', url):
        return make_error(400, "Invalid GitHub URL format", "INVALID_URL")
    
    # 2. Check rate limit
    client_ip = req.client.host if req.client and req.client.host else "unknown"
    if not analyze_rate_limiter.is_allowed(client_ip):
        return make_error(429, "Rate limit exceeded", "RATE_LIMITED")

    # 3. Check Firebase cache
    if not request.force_refresh:
        cached_core = await firebase_client.get_knowledge_core(url)
        if cached_core:
            return AnalyzeResponse(success=True, knowledge_core=cached_core, cached=True, error=None)

    # 4. Parse owner/repo
    try:
        owner, repo = github_client.parse_repo_url(url)
    except ValueError as e:
        return make_error(400, str(e), "INVALID_URL")

    # 5. Fetch repository bundle
    try:
        bundle = await github_client.fetch_repository_bundle(owner, repo)
        if not bundle.get("commits") and not bundle.get("metadata"):
            return make_error(404, "Repository not found or empty", "REPO_NOT_FOUND")
    except Exception as e:
        return make_error(500, f"GitHub error: {e}", "GITHUB_ERROR")

    # 6. Build context
    context = github_client.build_archaeology_context(bundle)

    # 7. Gemini Analysis
    gemini_result = await gemini_client.analyze_repository(context)

    # 8. Error check
    if "error" in gemini_result:
        return make_error(500, gemini_result.get("detail", "Unknown Gemini Error"), "GEMINI_ERROR")
    if "parse_error" in gemini_result:
        return make_error(500, "Failed to parse Gemini response", "PARSE_ERROR")

    # 9. Parse into KnowledgeCore
    try:
        core = parse_knowledge_core(url, gemini_result)
    except Exception as e:
        return make_error(500, f"Parsing error: {e}", "PARSE_ERROR")

    # 10. Save to Firebase
    await firebase_client.save_knowledge_core(url, core.model_dump())

    # 11. Return
    return AnalyzeResponse(success=True, knowledge_core=core, cached=False, error=None)
