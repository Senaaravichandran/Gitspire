from fastapi import APIRouter
from fastapi.responses import JSONResponse
from api.models.requests import OnboardRequest
from api.models.responses import OnboardResponse
from core.gemini_client import GeminiClient
from core.firebase_client import FirebaseClient
from core.repository_url import normalize_github_repo_url

router = APIRouter()
gemini_client = GeminiClient()
firebase_client = FirebaseClient()

def make_error(status_code: int, error: str, error_code: str):
    return JSONResponse(status_code=status_code, content={"success": False, "error": error, "error_code": error_code})

@router.post("/onboard", response_model=OnboardResponse)
async def generate_onboarding_path(request: OnboardRequest):
    try:
        repo_url = normalize_github_repo_url(request.repo_url)
    except ValueError as exc:
        return make_error(400, str(exc), "INVALID_URL")

    core = await firebase_client.get_knowledge_core(repo_url)
    if not core:
        return make_error(404, "Analyze this repository first", "NOT_ANALYZED")

    gemini_result = await gemini_client.generate_onboarding(repo_url, core, request.feature_description)
    if "error" in gemini_result or "parse_error" in gemini_result:
        checklist = []
        for idx, assumption in enumerate(core.get("assumptions", [])[:5], start=1):
            if hasattr(assumption, "id"):
                as_id = getattr(assumption, "id", idx)
                statement = getattr(assumption, "statement", "Review repository assumptions")
            elif isinstance(assumption, dict):
                as_id = assumption.get("id", idx)
                statement = assumption.get("statement", "Review repository assumptions")
            else:
                as_id = idx
                statement = "Review repository assumptions"
            checklist.append({
                "priority": idx,
                "topic": f"Assumption {as_id}",
                "why": (
                    f"{statement} This is a prerequisite for safe changes. "
                    "Validate it against the requested feature before implementation."
                ),
                "evidence": "Stored knowledge core"
            })
        if not checklist:
            checklist = [{
                "priority": 1,
                "topic": "Review repository context",
                "why": (
                    "No assumptions were found; review README and key configs before changes. "
                    "Confirm build and runtime steps to avoid breaking changes."
                ),
                "evidence": "Stored knowledge core"
            }]
        return OnboardResponse(success=True, checklist=checklist, warning_count=0)

    checklist = gemini_result.get("checklist", [])
    if not isinstance(checklist, list):
        checklist = []
        
    warning_count = int(gemini_result.get("warning_count", 0))

    return OnboardResponse(
        success=True,
        checklist=checklist,
        warning_count=warning_count
    )
