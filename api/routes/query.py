import hashlib
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from api.models.requests import QueryRequest
from api.models.responses import QueryResponse
from core.gemini_client import GeminiClient
from core.firebase_client import FirebaseClient
from core.parser import build_fallback_analysis
from core.repository_url import normalize_github_repo_url

router = APIRouter()
gemini_client = GeminiClient()
firebase_client = FirebaseClient()

def make_error(status_code: int, error: str, error_code: str):
    return JSONResponse(status_code=status_code, content={"success": False, "error": error, "error_code": error_code})

@router.post("/query", response_model=QueryResponse)
async def query_repository(request: QueryRequest):
    try:
        repo_url = normalize_github_repo_url(request.repo_url)
    except ValueError as exc:
        return make_error(400, str(exc), "INVALID_URL")
    if len(request.question) > 500:
        return make_error(400, "Question exceeds max 500 characters", "BAD_REQUEST")

    core = await firebase_client.get_knowledge_core(repo_url)
    if not core:
        return make_error(404, "Analyze this repository first", "NOT_ANALYZED")

    q_hash = hashlib.md5(request.question.encode()).hexdigest()
    cached_resp = await firebase_client.get_cached_query(repo_url, q_hash)
    if cached_resp:
        return QueryResponse(**cached_resp)

    gemini_result = await gemini_client.answer_query(repo_url, core, request.question)
    if "error" in gemini_result or "parse_error" in gemini_result:
        summary = str(core.get("summary", "No summary available."))
        decisions = core.get("decision_atoms", [])
        decision_text = "\n".join([f"- {d.get('decision', '')}" for d in decisions[:5] if isinstance(d, dict)])
        assumptions = core.get("assumptions", [])
        assumption_text = "\n".join([f"- {a.get('statement', '')}" for a in assumptions[:5] if isinstance(a, dict)])
        answer = "Response:\n"
        answer += f"Summary:\n{summary}\n"
        if decision_text:
            answer += f"Key decisions:\n{decision_text}\n"
        if assumption_text:
            answer += f"Key assumptions:\n{assumption_text}\n"
        response = QueryResponse(success=True, answer=answer, citations=[], confidence="low")
        await firebase_client.save_query_cache(repo_url, q_hash, response.model_dump())
        return response

    answer = str(gemini_result.get("answer", "No answer provided."))
    citations = gemini_result.get("citations", [])
    if not isinstance(citations, list):
        citations = []
    citations = [str(c) for c in citations if isinstance(c, (str, int, float))]
    confidence = str(gemini_result.get("confidence", "low")).strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    response = QueryResponse(success=True, answer=answer, citations=citations, confidence=confidence)
    await firebase_client.save_query_cache(repo_url, q_hash, response.model_dump())
    return response
