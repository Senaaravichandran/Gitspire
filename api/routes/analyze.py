import asyncio
import re
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from api.models.requests import AnalyzeRequest
from api.models.responses import AnalyzeResponse, KnowledgeCore
from core.github_client import GitHubClient
from core.gemini_client import GeminiClient
from core.firebase_client import FirebaseClient
from core.parser import parse_knowledge_core, build_fallback_analysis
from core.rate_limiter import analyze_rate_limiter

router = APIRouter()
github_client = GitHubClient()
gemini_client = GeminiClient()
firebase_client = FirebaseClient()

def normalize_cached_core(raw: dict) -> KnowledgeCore:
    raw.setdefault("decision_atoms", [])
    raw.setdefault("assumptions", [])
    raw.setdefault("failure_memory", [])
    raw.setdefault("ghost_decisions", [])
    raw.setdefault("regretted_decisions", [])
    raw.setdefault("orphaned_architecture", [])
    raw.setdefault("pulse_report", None)
    raw.setdefault("languages_detected", [])
    raw.setdefault("translated_artifact_count", 0)
    raw.setdefault("language_distribution", {})
    raw.setdefault("translation_enabled", False)
    raw.setdefault("summary", "")
    return KnowledgeCore.model_validate(raw)

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
            try:
                normalized = normalize_cached_core(cached_core)
            except Exception:
                normalized = None
            if normalized:
                has_all_sections = all([
                    len(normalized.decision_atoms) > 0,
                    len(normalized.assumptions) > 0,
                    len(normalized.ghost_decisions) > 0,
                    len(normalized.regretted_decisions) > 0,
                    len(normalized.orphaned_architecture) > 0,
                    normalized.pulse_report is not None
                ])
                if has_all_sections:
                    return AnalyzeResponse(success=True, knowledge_core=normalized, cached=True, error=None)

    # 4. Parse owner/repo
    try:
        owner, repo = github_client.parse_repo_url(url)
    except ValueError as e:
        return make_error(400, str(e), "INVALID_URL")

    # 5. Fetch repository bundle
    try:
        bundle = await asyncio.wait_for(
            github_client.fetch_repository_bundle(owner, repo),
            timeout=90
        )
        if not bundle.get("commits") and not bundle.get("metadata"):
            return make_error(404, "Repository not found or empty", "REPO_NOT_FOUND")
    except Exception as e:
        if isinstance(e, asyncio.TimeoutError):
            return make_error(504, "GitHub API timed out", "GITHUB_TIMEOUT")
        return make_error(500, f"GitHub error: {e}", "GITHUB_ERROR")

    # 6. Build context
    context, translation_metadata = github_client.build_archaeology_context(bundle)

    # 7. Gemini Analysis
    try:
        gemini_result = await asyncio.wait_for(
            gemini_client.analyze_repository(context),
            timeout=120
        )
    except asyncio.TimeoutError:
        core = build_fallback_analysis(url, bundle, translation_metadata)
        return AnalyzeResponse(success=True, knowledge_core=core, cached=False, error=None)

    # 8. Error check
    if "error" in gemini_result:
        core = build_fallback_analysis(url, bundle, translation_metadata)
        return AnalyzeResponse(success=True, knowledge_core=core, cached=False, error=None)
    if "parse_error" in gemini_result or not gemini_result:
        core = build_fallback_analysis(url, bundle, translation_metadata)
        return AnalyzeResponse(success=True, knowledge_core=core, cached=False, error=None)

    # 9. Parse into KnowledgeCore
    try:
        core = parse_knowledge_core(url, gemini_result, translation_metadata)
    except Exception as e:
        return make_error(500, f"Parsing error: {e}", "PARSE_ERROR")

    if (
        not core.summary
        or core.summary == "No summary provided."
        or not core.decision_atoms
        or not core.assumptions
    ):
        core = build_fallback_analysis(url, bundle, translation_metadata)

    # 10. Save to Firebase (non-blocking timeout)
    try:
        await asyncio.wait_for(
            firebase_client.save_knowledge_core(url, core.model_dump()),
            timeout=10
        )
    except asyncio.TimeoutError:
        pass

    # 11. Return
    return AnalyzeResponse(success=True, knowledge_core=core, cached=False, error=None)
