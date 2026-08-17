from fastapi import APIRouter
from fastapi.responses import JSONResponse
from api.models.requests import AlarmRequest
from api.models.responses import AlarmResponse, Assumption
from core.gemini_client import GeminiClient
from core.firebase_client import FirebaseClient
from core.repository_url import normalize_github_repo_url

router = APIRouter()
gemini_client = GeminiClient()
firebase_client = FirebaseClient()

def make_error(status_code: int, error: str, error_code: str):
    return JSONResponse(status_code=status_code, content={"success": False, "error": error, "error_code": error_code})

@router.post("/alarm", response_model=AlarmResponse)
async def check_assumption_alarm(request: AlarmRequest):
    try:
        repo_url = normalize_github_repo_url(request.repo_url)
    except ValueError as exc:
        return make_error(400, str(exc), "INVALID_URL")
    if len(request.code_snippet) > 10000:
        return make_error(400, "Code snippet exceeds max 10,000 characters", "BAD_REQUEST")

    core = await firebase_client.get_knowledge_core(repo_url)
    if not core:
        return make_error(404, "Analyze this repository first", "NOT_ANALYZED")

    assumptions = core.get("assumptions", [])
    
    gemini_result = await gemini_client.check_alarm(repo_url, assumptions, request.code_snippet)
    if "error" in gemini_result or "parse_error" in gemini_result:
        return AlarmResponse(
            success=True,
            violation_detected=False,
            violated_assumption=None,
            explanation=(
                "No violation detected. "
                "The analysis did not confirm a conflict, so treat this as a preliminary check and review manually."
            ),
            new_assumption_introduced=None
        )

    violation = gemini_result.get("violation_detected") is True
    violated_id = gemini_result.get("violated_assumption_id")
    explanation = str(gemini_result.get("explanation", ""))
    new_assumption = gemini_result.get("new_assumption_introduced")
    
    if new_assumption is not None:
        new_assumption = str(new_assumption)

    violated_asmp = next((a for a in assumptions if a.get("id") == violated_id), None) if violated_id else None
    
    # ensure it's mapped to Pydantic model if it exists
    if violated_asmp:
        violated_asmp = Assumption(**violated_asmp)

    return AlarmResponse(
        success=True,
        violation_detected=violation,
        violated_assumption=violated_asmp,
        explanation=explanation,
        new_assumption_introduced=new_assumption
    )
