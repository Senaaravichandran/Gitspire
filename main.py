import os
from dotenv import load_dotenv

# Load environment variables from .env file FIRST — before any other imports
load_dotenv()

# Process Base64 credentials for deployment (Railway/Heroku)
import base64
import tempfile
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.routes import analyze, query, alarm, onboard
from core.firebase_client import FirebaseClient
from core.gemini_client import GEMINI_MODEL_DISPLAY_NAME, GEMINI_MODEL_NAME

DEPLOYED_BACKEND_URL = "https://gitspire-5q7m.onrender.com"
DEFAULT_BACKEND_URL = "http://localhost:8000"
DEFAULT_FRONTEND_ORIGINS = [
    DEPLOYED_BACKEND_URL,
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]


def normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    normalized = str(value).strip().rstrip("/")
    return normalized or None


def get_env_urls(env_name: str) -> list[str]:
    raw_value = os.environ.get(env_name, "")
    urls = []
    for part in raw_value.split(","):
        normalized = normalize_url(part)
        if normalized and normalized not in urls:
            urls.append(normalized)
    return urls


def get_allowed_frontend_origins() -> list[str]:
    allowed = []
    for origin in get_env_urls("FRONTEND_URL") + DEFAULT_FRONTEND_ORIGINS:
        if origin not in allowed:
            allowed.append(origin)
    return allowed


def get_primary_frontend_url() -> str:
    configured = get_env_urls("FRONTEND_URL")
    return configured[0] if configured else DEFAULT_FRONTEND_ORIGINS[0]


def get_backend_base_url(request: Request | None = None) -> str:
    configured = get_env_urls("BACKEND_URL")
    if configured:
        return configured[0]

    if request is not None:
        forwarded_host = request.headers.get("x-forwarded-host")
        if forwarded_host:
            forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            scheme = forwarded_proto.split(",")[0].strip() or request.url.scheme
            host = forwarded_host.split(",")[0].strip()
            normalized = normalize_url(f"{scheme}://{host}")
            if normalized:
                return normalized

        return str(request.base_url).rstrip("/")

    return DEFAULT_BACKEND_URL

# Process Base64 credentials for deployment AFTER loading .env
if "FIREBASE_CREDENTIALS_JSON" in os.environ:
    try:
        decoded = base64.b64decode(os.environ["FIREBASE_CREDENTIALS_JSON"])
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, 'wb') as f:
            f.write(decoded)
        os.environ["FIREBASE_CREDENTIALS_PATH"] = path
    except Exception as e:
        logging.error(f"Failed to decode FIREBASE_CREDENTIALS_JSON: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize Firebase connection
    FirebaseClient()
    yield
    # Shutdown: nothing needed

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_frontend_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers enforcing exact error shape
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": str(exc.detail), "error_code": "HTTP_ERROR"}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "error_code": "INTERNAL_ERROR"}
    )

# Mount API routes
app.include_router(analyze.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(alarm.router, prefix="/api")
app.include_router(onboard.router, prefix="/api")

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "service": "gitspire"}


@app.get("/api/meta")
async def api_meta(request: Request):
    return {
        "service": "gitspire",
        "model_name": GEMINI_MODEL_NAME,
        "model_display_name": GEMINI_MODEL_DISPLAY_NAME,
        "api_base_url": get_backend_base_url(request),
        "frontend_url": get_primary_frontend_url(),
    }

# Serve frontend — MUST be last (catch-all)
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
