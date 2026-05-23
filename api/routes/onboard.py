from fastapi import APIRouter
from fastapi.responses import JSONResponse
from api.models.requests import OnboardRequest
from api.models.responses import OnboardResponse
from core.gemini_client import GeminiClient
from core.firebase_client import FirebaseClient

router = APIRouter()
gemini_client = GeminiClient()
firebase_client = FirebaseClient()

def make_error(status_code: int, error: str, error_code: str):
    return JSONResponse(status_code=status_code, content={"success": False, "error": error, "error_code": error_code})

@router.post("/onboard", response_model=OnboardResponse)
async def generate_onboarding_path(request: OnboardRequest):
    core = await firebase_client.get_knowledge_core(request.repo_url)
    if not core:
        return make_error(404, "Analyze this repository first", "NOT_ANALYZED")

    gemini_result = await gemini_client.generate_onboarding(request.repo_url, core, request.feature_description)
    if "error" in gemini_result or "parse_error" in gemini_result:
        return make_error(500, "Gemini failed to generate onboarding", "GEMINI_ERROR")

    checklist = gemini_result.get("checklist", [])
    if not isinstance(checklist, list):
        checklist = []
        
    warning_count = int(gemini_result.get("warning_count", 0))

    return OnboardResponse(
        success=True,
        checklist=checklist,
        warning_count=warning_count
    )