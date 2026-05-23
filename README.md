Gitspire
========

Gitspire is a repository archaeology system that reconstructs the invisible
"why-layer" of a GitHub codebase. It ingests commits, issues, pull requests,
and key files, then surfaces architectural decisions, implicit assumptions,
failed approaches, and undocumented ghost decisions.

Problem
-------
Every developer eventually asks: "Why is this built this way?" The answer
rarely lives in code. It lives in old issues, abandoned PRs, or a design choice
made under constraints that were never documented. New engineers waste days
rediscovering context, or they ship risky changes because the real assumptions
are invisible.

Solution
--------
Gitspire reads the entire repository history and reconstructs the missing
intent layer. You get:

- Decision Atoms: why key architectural choices were made.
- Assumption Graph: the implicit truths the system depends on.
- Failure Memory: what was tried and abandoned.
- Ghost Decisions: intentional-looking choices with no documented trail.

Project Name
------------
Gitspire

Tech Stack
---------
Backend
- Python 3.11+
- FastAPI + Uvicorn
- httpx for GitHub REST ingestion
- google-generativeai (Gemini)
- firebase-admin (Realtime Database caching)
- Pydantic v2

Frontend
- Vanilla HTML/CSS/JS (no build step)
- Marked.js for Markdown rendering

Architecture
------------
Gitspire is built as a thin API layer with a long-context reasoning core and a
static SPA frontend.

1) Ingestion
	 - GitHubClient fetches metadata, commits, issues, PRs, file tree, key files.
	 - A single structured context block is assembled for Gemini.

2) Reasoning
	 - GeminiClient formats prompts from core/prompts.py and returns strict JSON.
	 - Parser converts raw JSON into Pydantic models with safe defaults.

3) Caching
	 - Firebase stores knowledge cores (24h) and query caches (by question hash).

4) Delivery
	 - FastAPI serves /api endpoints and the static SPA.
	 - The frontend renders Decision Atoms, Assumptions, Failure Memory,
		 and Ghost Decisions, plus three interactive tools (Ask Why, Alarm,
		 Onboarding Path).

Project Structure
----------------
- api/: FastAPI routers + request/response models
- core/: GitHub ingestion, Gemini prompts, parsing, Firebase caching
- static/: Single-page app (HTML/CSS/JS)

Quick Start
-----------
1) Create a Python 3.11+ environment and install dependencies:

```
pip install -r requirements.txt
```

2) Create .env (or copy .env.example) with:

```
GEMINI_API_KEY=your_key_here
FIREBASE_DATABASE_URL=https://YOUR_DB.firebaseio.com/
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
GITHUB_TOKEN=optional_github_pat
GEMINI_MODEL=models/gemini-2.5-pro
```

3) Run the server:

```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4) Open the app:

```
http://localhost:8000
```

User Flow
--------
1) Paste a GitHub repo URL.
2) Click Analyze Repository.
3) Wait for the long-context analysis to complete.
4) Explore the four knowledge tabs and tool panels.

API Endpoints
------------
- POST /api/analyze
	Body: { "repo_url": "https://github.com/owner/repo", "force_refresh": false }
- POST /api/query
	Body: { "repo_url": "...", "question": "Why ...?" }
- POST /api/alarm
	Body: { "repo_url": "...", "code_snippet": "..." }
- POST /api/onboard
	Body: { "repo_url": "...", "feature_description": "..." }

Notes on Gemini Models
----------------------
If you see a Gemini 404 model error, set GEMINI_MODEL to an available model
listed by your API key. Example:

```
GEMINI_MODEL=models/gemini-2.5-pro
```

Caching
-------
- Knowledge cores are cached in Firebase for 24 hours per repo URL.
- Query answers are cached by a hash of the question.

Troubleshooting
---------------
- 500 /api/analyze with GEMINI_ERROR:
	- Verify GEMINI_API_KEY and GEMINI_MODEL in .env.
- 403 from GitHub:
	- Add a valid GITHUB_TOKEN to increase rate limits.
- Firebase errors:
	- Check FIREBASE_DATABASE_URL and firebase-credentials.json path.
- Blank UI:
	- Open DevTools Console for JS errors and check /api/analyze response.

Security
--------
- Keep .env and firebase-credentials.json out of source control.
- Do not expose private repos or tokens to the client; all calls go through /api.

License
-------
Hackathon project. Add a license if you plan to publish.
