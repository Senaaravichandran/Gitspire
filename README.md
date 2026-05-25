<div align="center">

```
  ██████╗ ██╗████████╗███████╗██████╗ ██╗██████╗ ███████╗
 ██╔════╝ ██║╚══██╔══╝██╔════╝██╔══██╗██║██╔══██╗██╔════╝
 ██║  ███╗██║   ██║   ███████╗██████╔╝██║██████╔╝█████╗  
 ██║   ██║██║   ██║   ╚════██║██╔═══╝ ██║██╔══██╗██╔══╝  
 ╚██████╔╝██║   ██║   ███████║██║     ██║██║  ██║███████╗
  ╚═════╝ ╚═╝   ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝
```

**Repository Archaeology Powered by Gemini**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini_1.5_Pro-1M_Context-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Firebase](https://img.shields.io/badge/Firebase-RTDB-FBBC04?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-MIT-34A853?style=for-the-badge)](LICENSE)

> **Built for Codesprint with Gemini**
> 
> Team **DRAGORITHM** · Senaaravichandran A · Gowshik S

---

### *"GitHub Copilot knows WHAT your code does. GitSpire knows WHY."*

---

</div>

## Table of Contents

- [The Problem](#the-problem)
- [What GitSpire Does](#what-gitspire-does)
- [How Gemini Powers Everything](#how-gemini-powers-everything)
- [Full Architecture](#full-architecture)
- [The Knowledge Core](#the-knowledge-core)
- [Tech Stack](#tech-stack)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [The BABEL Layer — Multilingual Support](#the-babel-layer--multilingual-support)
- [GitSpire Guard](#gitspire-guard)
- [Deployment](#deployment)

---

## The Problem

Every developer has inherited a codebase and asked **"why is this built this way?"**

The answer is never in the code. It lives in:
- The head of a senior developer who left two years ago
- A Slack thread from 2021 that nobody linked to anything
- A closed GitHub issue that the PR never referenced
- A commit message that just says `"fix auth"`

**The git history is write-only.** You can dump it with `git log`, but reading it in a way that extracts meaning is impossible with existing tools.

| What exists today | What's missing |
|---|---|
| GitHub Copilot — explains WHAT code does | Nothing that explains WHY decisions were made |
| SonarQube — detects code complexity | Nothing that connects complexity to the decision that caused it |
| Dependabot — flags outdated packages | Nothing that checks if the original REASONING for choosing that package still holds |
| git blame — shows WHO touched a line | Nothing that explains WHY that line is the way it is |

**GitSpire is the missing layer.**

---

## What GitSpire Does

GitSpire reads an entire GitHub repository — every commit, issue, pull request, and key file — and sends it to **Gemini 1.5 Pro** in a single long-context prompt. Gemini reconstructs the invisible **WHY-layer**: the reasoning behind every non-obvious architectural decision, the failed approaches that were tried and abandoned, the implicit assumptions the codebase silently depends on, and the ghost decisions that look intentional but have zero documentation trail.

The output is a structured **Knowledge Core** — a permanent, queryable record of *why* the codebase is the way it is.

### What the User Gets

```
1. Paste a GitHub URL
2. Click "Analyze Repository"
3. Wait 30–90 seconds (entire repo processed in one Gemini call)
4. Receive a Knowledge Core with 7 types of insight
5. Ask questions, check assumptions, generate onboarding paths
```

---

## How Gemini Powers Everything

Gemini is not an auxiliary feature in GitSpire. **It is the entire reasoning engine.** Every insight the system produces comes from Gemini. Here is exactly how.

### The Core Innovation: One Call, Whole Repo

Most AI-powered code tools use **RAG (Retrieval-Augmented Generation)** — they chunk the codebase into pieces, embed them, retrieve relevant chunks, and pass them to the model. This approach loses cross-chunk context. GitSpire does the opposite:

```
Traditional RAG approach:
  Codebase (500k tokens) → chunk → embed → retrieve → Gemini (small window)
  ⚠ Context lost between chunks. Decisions that span commits are invisible.

GitSpire approach:
  Codebase (500k tokens) → build_archaeology_context() → Gemini 1.5 Pro (1M tokens)
  ✓ Entire repository. One call. Zero context loss.
```

Gemini 1.5 Pro's **1 million token context window** makes this possible. No other approach would work — the entire point of archaeology is reading the *complete* artifact trail.

### Gemini Call 1 — Repository Archaeology (`gemini_client.py` → `analyze_repository()`)

This is the primary call. It receives the full `archaeology_context` string (up to 800,000 characters) and returns a deeply structured JSON object.

**Model configuration:**
```python
model = GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=GenerationConfig(
        temperature=0.2,        # Low: precision over creativity
        top_p=0.8,
        max_output_tokens=8192,
        response_mime_type="application/json"  # Forces clean JSON output
    )
)
```

**Why temperature 0.2?** Archaeological analysis requires precision and repeatability. The same repository should yield consistent insights across multiple analyses. A low temperature also forces Gemini to commit to specific evidence (commit SHAs, issue numbers) rather than vague generalities.

**The prompt** (`prompts.py` → `PROMPT_ARCHAEOLOGY`) instructs Gemini to:
- Read the full context as a software archaeologist
- Extract only what is evidenced — no hallucination
- Cite specific commits (`commit:abc1234`), issues (`issue:#42`), and PRs (`pr:#7`) for every claim
- Return strict JSON with no markdown fences, no preamble

**Output shape** (strictly enforced by the prompt):
```json
{
  "summary": "2-3 sentence plain English description",
  "decision_atoms": [
    {
      "id": "da_001",
      "decision": "What architectural choice was made",
      "reasoning": "WHY — with specific evidence from history",
      "evidence": ["commit:abc1234", "issue:#42", "pr:#7"],
      "confidence": 0.91
    }
  ],
  "assumptions": [
    {
      "id": "as_001",
      "statement": "What must remain true for this system to work",
      "risk_level": "critical | moderate | low",
      "depends_on": ["as_002"]
    }
  ],
  "failure_memory": [
    {
      "approach": "What was tried",
      "reason_failed": "Why it was abandoned",
      "evidence": ["commit:def5678"]
    }
  ],
  "ghost_decisions": [
    {
      "location": "src/auth/middleware.py:47",
      "observation": "What looks intentional",
      "possible_reasons": ["Reason A", "Reason B"]
    }
  ],
  "regretted_decisions": [...],
  "orphaned_architecture": [...],
  "pulse_report": { "freshness_score": 74, "stale_areas": [...] }
}
```

### Gemini Call 2 — Why Query (`gemini_client.py` → `answer_query()`)

When a developer types a question in the **Ask Why** panel, Gemini receives:
- The full cached Knowledge Core (as JSON)
- The developer's question in plain English

**Prompt** (`PROMPT_WHY_QUERY`): Instructs Gemini to answer ONLY from the provided Knowledge Core — never from general training knowledge. Every answer must include citations back to the decision atoms or assumptions that support it.

**Output:**
```json
{
  "answer": "Markdown-formatted answer with specific citations",
  "citations": ["commit:abc1234", "issue:#89", "da_003"],
  "confidence": "high | medium | low"
}
```

### Gemini Call 3 — Assumption Alarm (`gemini_client.py` → `check_alarm()`)

When a developer pastes a code snippet, Gemini receives:
- The extracted assumptions list from the Knowledge Core
- The code snippet (up to 10,000 characters)

**Prompt** (`PROMPT_ASSUMPTION_ALARM`): Instructs Gemini to act as a violation detector. It must check whether the snippet violates any assumption, and if so, which one and why.

**Output:**
```json
{
  "violation_detected": true,
  "violated_assumption_id": "as_002",
  "explanation": "This snippet introduces Redis as a hard dependency. Assumption #2 states Redis must always be optional with a memory fallback.",
  "new_assumption_introduced": "Redis is always available in production"
}
```

### Gemini Call 4 — Onboarding Path (`gemini_client.py` → `generate_onboarding()`)

When a developer describes a feature they want to build, Gemini receives:
- The full Knowledge Core
- The feature description

**Prompt** (`PROMPT_ONBOARDING`): Instructs Gemini to generate a ranked checklist of what the developer MUST understand before safely implementing the feature. Ranked by danger — most likely to break first.

**Output:**
```json
{
  "checklist": [
    {
      "priority": 1,
      "topic": "Auth middleware bypass pattern",
      "why": "Your feature touches the auth layer. Decision Atom #3 explains a non-obvious bypass pattern that your implementation must preserve.",
      "evidence": "commit:abc1234"
    }
  ],
  "warning_count": 3
}
```

### JSON Safety — `_safe_parse_json()`

Gemini returns JSON mode responses, but edge cases exist. The `_safe_parse_json()` method in `gemini_client.py` handles this with a three-attempt strategy:

```python
def _safe_parse_json(self, text: str) -> dict:
    # Attempt 1: Clean parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Attempt 2: Find JSON boundaries (strip surrounding text)
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    # Attempt 3: Graceful degradation
    return {"parse_error": True, "raw_preview": text[:500]}
```

---

## Full Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                               │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  GitHub REST API │  │ Google Translate  │  │   Gemini 1.5 Pro     │  │
│  │  api.github.com  │  │ cloud.google.com  │  │  1M Token Context    │  │
│  │       /v3        │  │   /translate      │  │  JSON Mode · T=0.2   │  │
│  └────────┬─────────┘  └────────┬──────────┘  └──────────┬───────────┘  │
│           │ github_client.py    │ translation.py          │ gemini_client.py│
└───────────┼─────────────────────┼─────────────────────────┼─────────────┘
            │                     │                         │
            ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND                                  │
│                    main.py · uvicorn · Pydantic v2                      │
│                                                                         │
│  ┌──────────────┐ ┌─────────────┐ ┌────────────┐ ┌──────────────────┐  │
│  │ analyze.py   │ │  query.py   │ │  alarm.py  │ │   onboard.py     │  │
│  │POST /analyze │ │ POST /query │ │ POST /alarm│ │  POST /onboard   │  │
│  └──────┬───────┘ └──────┬──────┘ └─────┬──────┘ └────────┬─────────┘  │
│         │                │              │                  │            │
│         └────────────────┴──────────────┴──────────────────┘            │
│                                    │                                    │
│              ┌─────────────────────┼──────────────────────┐             │
│              ▼                     ▼                      ▼             │
│         parser.py             prompts.py         firebase_client.py    │
│      (Gemini→Pydantic)    (all prompt templates)  (cache read/write)   │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
         ┌──────────────────┐  ┌──────────────┐  ┌────────────────────┐
         │  KNOWLEDGE CORE  │  │   Firebase   │  │   GitSpire SPA     │
         │  (in Firebase)   │  │  Realtime DB │  │  index.html        │
         │                  │  │  SHA256 key  │  │  app.js · api.js   │
         │  Decision Atoms  │  │  24hr TTL    │  │  ui.js · panels.js │
         │  Assumptions     │  └──────────────┘  │  Marked.js         │
         │  Failure Memory  │                     │  Lottie Animations │
         │  Ghost Decisions │◄────────────────────│                    │
         │  Regretted Decs  │                     └────────────────────┘
         │  Orphaned Arch   │
         │  Pulse Report    │
         └──────────────────┘
```

### Request Lifecycle — Full Trace

#### `POST /api/analyze` (the main pipeline)

```
1. VALIDATE
   analyze.py → validate repo_url against regex
   r'^https://github\.com/[\w.-]+/[\w.-]+/?$'
   → 400 INVALID_URL if not matched

2. RATE LIMIT
   analyze.py → check in-memory dict (IP → [timestamps])
   max 10 calls/hour per IP
   → 429 RATE_LIMITED if exceeded

3. CACHE CHECK
   firebase_client.py → get_knowledge_core(repo_url)
   Key = SHA256(repo_url)[:16]
   Check analyzed_at — if < 24hrs, return cached
   → AnalyzeResponse(cached=True) if found

4. GITHUB INGESTION
   github_client.py → fetch_repository_bundle(owner, repo)
   
   Runs CONCURRENTLY via asyncio.gather():
   ├── fetch_metadata()     → GET /repos/{owner}/{repo}
   ├── fetch_commits()      → GET /repos/{owner}/{repo}/commits (paginate to 150)
   ├── fetch_issues()       → GET /repos/{owner}/{repo}/issues?state=all (to 100)
   ├── fetch_pull_requests()→ GET /repos/{owner}/{repo}/pulls?state=all (to 50)
   ├── fetch_file_tree()    → GET /repos/{owner}/{repo}/git/trees/HEAD?recursive=1
   └── fetch_key_files()    → GET /repos/{owner}/{repo}/contents/{path} × 10

5. TRANSLATION (optional)
   translation.py → detect_and_translate(bundle)
   
   For every commit message, issue body, PR body:
   ├── Detect language via Google Translate API
   ├── If not English → translate to English
   ├── Keep original + translated text
   └── Track: languages_detected, translated_count, language_distribution

6. CONTEXT BUILDING
   github_client.py → build_archaeology_context(bundle)
   
   Assembles structured text block:
   ├── === REPOSITORY METADATA ===
   ├── === KEY FILES ===          (README, config files, ARCHITECTURE docs)
   ├── === COMMIT HISTORY ===     (oldest first, full messages preserved)
   ├── === ISSUES (all states) ===
   └── === PULL REQUESTS ===
   
   Hard limit: 800,000 characters
   Truncation order: oldest commits → issue bodies → PR bodies
   (commit messages are NEVER truncated mid-sentence)

7. GEMINI ANALYSIS
   gemini_client.py → analyze_repository(archaeology_context)
   
   Single API call to Gemini 1.5 Pro
   Model: gemini-1.5-pro
   Temp: 0.2, max_tokens: 8192, response_mime_type: application/json
   
   Extracts:
   ├── summary
   ├── decision_atoms[]      (5–10 major architectural choices + WHY)
   ├── assumptions[]         (hidden truths system depends on)
   ├── failure_memory[]      (tried & abandoned approaches)
   ├── ghost_decisions[]     (intentional-looking, zero docs)
   ├── regretted_decisions[] (choices that show regret signals)
   ├── orphaned_architecture[] (code with no active owner)
   └── pulse_report          (freshness score + stale areas)

8. PARSE
   parser.py → parse_knowledge_core(repo_url, gemini_response)
   
   Gemini JSON dict → KnowledgeCore Pydantic model
   Handles all missing/malformed fields gracefully
   Generates IDs for missing records (da_001, as_002...)
   NEVER raises — always returns valid (possibly partial) model

9. CACHE
   firebase_client.py → save_knowledge_core(repo_url, core)
   
   Writes to /knowledge_cores/{sha256_key}
   Adds analyzed_at: datetime.utcnow().isoformat()
   Key structure: /knowledge_cores/{16-char-sha256-hash}

10. RESPOND
    → AnalyzeResponse(success=True, knowledge_core=core, cached=False)
```

#### `POST /api/query`

```
1. Validate question ≤ 500 chars
2. Load KnowledgeCore from Firebase (→ 404 NOT_ANALYZED if missing)
3. Check query cache: /query_cache/{repo_key}/{md5(question)}
4. If not cached: gemini_client.answer_query(core, question)
5. Save to query cache
6. Return QueryResponse(answer, citations, confidence)
```

#### `POST /api/alarm`

```
1. Validate code_snippet ≤ 10,000 chars
2. Load KnowledgeCore from Firebase
3. Extract assumptions list only (keeps prompt smaller)
4. gemini_client.check_alarm(assumptions, code_snippet)
5. Return AlarmResponse(violation_detected, violated_assumption, explanation)
```

#### `POST /api/onboard`

```
1. Load KnowledgeCore from Firebase
2. gemini_client.generate_onboarding(core, feature_description)
3. Return OnboardResponse(checklist[], warning_count)
```

---

## The Knowledge Core

The Knowledge Core is the central data artifact of GitSpire. It is extracted once, cached in Firebase, and serves as the source of truth for all subsequent tool calls.

### Seven Insight Types

| Tab | Type | What It Contains |
|---|---|---|
| 🔵 Decision Atoms | `decision_atoms[]` | Major architectural choices with WHY they were made, evidence citations, and confidence scores |
| 🟢 Assumptions | `assumptions[]` | Hidden truths the system silently depends on, risk-rated critical/moderate/low |
| 🔴 Failure Memory | `failure_memory[]` | Approaches that were tried and abandoned, with the reason they failed |
| 🟣 Ghost Decisions | `ghost_decisions[]` | Intentional-looking patterns with zero documentation trail |
| 🟡 Regretted Decisions | `regretted_decisions[]` | Choices that show regret signals in the artifact trail (reverts, TODOs, issue language) |
| 🔵 Orphaned Architecture | `orphaned_architecture[]` | Code areas with no active owner or understanding |
| ⚪ Decision Pulse | `pulse_report` | Freshness score and staleness report for the whole architecture |

### Pydantic Models (`api/models/responses.py`)

```python
class DecisionAtom(BaseModel):
    id: str                       # "da_001"
    decision: str                 # What was decided
    reasoning: str                # WHY — with evidence woven in
    evidence: list[str]           # ["commit:abc1234", "issue:#42", "pr:#7"]
    confidence: float             # 0.0 → 1.0

class Assumption(BaseModel):
    id: str                       # "as_001"
    statement: str                # What must remain true
    risk_level: str               # "critical" | "moderate" | "low"
    depends_on: list[str]         # IDs of other assumptions this depends on

class FailureRecord(BaseModel):
    approach: str                 # What was tried
    reason_failed: str            # Why it didn't work
    evidence: list[str]           # Commit/issue references

class GhostDecision(BaseModel):
    location: str                 # "src/auth/middleware.py:47"
    observation: str              # What looks intentional
    possible_reasons: list[str]   # Inferred candidates

class KnowledgeCore(BaseModel):
    repo_url: str
    analyzed_at: str              # ISO timestamp
    decision_atoms: list[DecisionAtom]
    assumptions: list[Assumption]
    failure_memory: list[FailureRecord]
    ghost_decisions: list[GhostDecision]
    regretted_decisions: list[dict]
    orphaned_architecture: list[dict]
    pulse_report: dict
    summary: str
    languages_detected: list[str]        # From BABEL translation layer
    translated_artifact_count: int
```

### Firebase Cache Structure

```
firebase-project/
└── knowledge_cores/
    └── {sha256(repo_url)[:16]}/
        ├── repo_url: "https://github.com/psf/requests"
        ├── analyzed_at: "2025-06-01T14:22:10.123456"
        ├── summary: "..."
        ├── decision_atoms: [...]
        ├── assumptions: [...]
        ├── failure_memory: [...]
        ├── ghost_decisions: [...]
        └── ...
└── query_cache/
    └── {repo_key}/
        └── {md5(question)}/
            ├── answer: "..."
            ├── citations: [...]
            └── confidence: "high"
```

---

## Tech Stack

### Backend

| Technology | Version | Role |
|---|---|---|
| **Python** | 3.11+ | Core runtime |
| **FastAPI** | 0.111.0 | REST API framework, async request handling |
| **Uvicorn** | 0.30.1 | ASGI server (with standard extras for WebSocket support) |
| **httpx** | 0.27.0 | Async HTTP client for GitHub REST API calls |
| **google-generativeai** | 0.7.2 | Official Gemini SDK — all LLM calls go through this |
| **firebase-admin** | 6.5.0 | Firebase Realtime Database for Knowledge Core caching |
| **Pydantic** | 2.7.1 | Request/response model validation, data coercion |
| **python-dotenv** | 1.0.1 | Environment variable management |

### Google / Firebase Services

| Service | SDK / API | Role in GitSpire |
|---|---|---|
| **Gemini 1.5 Pro** | `google-generativeai` | Core reasoning engine — all 4 insight extraction calls |
| **Firebase Realtime Database** | `firebase-admin` | Knowledge Core persistence, query result caching |
| **Google Translate API** | `google-cloud-translate` | BABEL layer — multilingual commit/issue normalization |

### Frontend

| Technology | Role |
|---|---|
| **Vanilla HTML5/CSS3/JS** | Full SPA — zero build step, zero framework dependency |
| **Marked.js** (CDN) | Render Gemini's markdown responses in the Why Query panel |
| **Lottie / bodymovin** | Loading animations during the 30–90s analysis wait |

### Frontend File Roles

| File | Role |
|---|---|
| `static/index.html` | Full SPA structure — all sections, panels, tab nav |
| `static/js/app.js` | State machine — manages IDLE/ANALYZING/READY transitions |
| `static/js/api.js` | Fetch wrappers for all `/api/*` endpoints |
| `static/js/ui.js` | Pure render functions — return HTML strings for all cards |
| `static/js/panels.js` | Tab switching, tool panel wiring, delegated event handlers |
| `static/css/design-system.css` | All CSS variables — single source of truth for every color |
| `static/css/components.css` | Card, badge, evidence chip, confidence bar styles |
| `static/css/animations.css` | Keyframes, staggered card entrance, skeleton loaders |
| `static/css/layout.css` | Page layout, header, hero, tools grid |

---

## API Reference

### `POST /api/analyze`

Ingests a GitHub repository and returns a Knowledge Core.

**Request:**
```json
{
  "repo_url": "https://github.com/psf/requests",
  "force_refresh": false
}
```

**Response:**
```json
{
  "success": true,
  "cached": false,
  "knowledge_core": {
    "repo_url": "https://github.com/psf/requests",
    "analyzed_at": "2025-06-01T14:22:10.123456",
    "summary": "The requests library...",
    "decision_atoms": [...],
    "assumptions": [...],
    "failure_memory": [...],
    "ghost_decisions": [...],
    "regretted_decisions": [...],
    "orphaned_architecture": [...],
    "pulse_report": { "freshness_score": 82, "stale_areas": [...] },
    "languages_detected": ["en", "zh", "ja"],
    "translated_artifact_count": 47
  }
}
```

**Error codes:** `INVALID_URL` · `RATE_LIMITED` · `REPO_NOT_FOUND` · `GITHUB_ERROR` · `GEMINI_ERROR` · `PARSE_ERROR`

---

### `POST /api/query`

Asks a natural language question answered from the Knowledge Core.

**Request:**
```json
{
  "repo_url": "https://github.com/psf/requests",
  "question": "Why does requests use urllib3 instead of httpx?"
}
```

**Response:**
```json
{
  "success": true,
  "answer": "The urllib3 dependency predates httpx by several years...",
  "citations": ["commit:abc1234", "issue:#1234", "da_003"],
  "confidence": "high"
}
```

---

### `POST /api/alarm`

Checks whether a code snippet violates any extracted assumptions.

**Request:**
```json
{
  "repo_url": "https://github.com/psf/requests",
  "code_snippet": "import redis\ncache = redis.Redis(host='localhost')\n..."
}
```

**Response:**
```json
{
  "success": true,
  "violation_detected": true,
  "violated_assumption": {
    "id": "as_002",
    "statement": "All caching must fall back to in-memory if external cache is unavailable",
    "risk_level": "critical"
  },
  "explanation": "This snippet creates a hard Redis dependency with no fallback path...",
  "new_assumption_introduced": "Redis is always available in the deployment environment"
}
```

---

### `POST /api/onboard`

Generates a risk-ranked onboarding checklist for a proposed feature.

**Request:**
```json
{
  "repo_url": "https://github.com/psf/requests",
  "feature_description": "I want to add async support using asyncio"
}
```

**Response:**
```json
{
  "success": true,
  "checklist": [
    {
      "priority": 1,
      "topic": "Session state threading model",
      "why": "The Session object assumes thread-local state. Async breaks this assumption completely.",
      "evidence": "da_004"
    }
  ],
  "warning_count": 3
}
```

---

### `GET /health`

```json
{ "status": "ok", "service": "gitspire" }
```

---

## Project Structure

```
gitspire/
│
├── .env                         # Environment variables (never commit)
├── .env.example                 # Template — copy to .env
├── .gitignore
├── requirements.txt             # Exact pinned versions
├── README.md
├── railway.json                 # Railway deployment config
├── Procfile                     # uvicorn start command
├── firebase-credentials.json    # Never commit — add to .gitignore
│
├── main.py                      # FastAPI app, CORS, StaticFiles, lifespan
│
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── analyze.py           # POST /api/analyze — full pipeline
│   │   ├── query.py             # POST /api/query — WHY questions
│   │   ├── alarm.py             # POST /api/alarm — assumption violations
│   │   └── onboard.py           # POST /api/onboard — feature checklists
│   └── models/
│       ├── __init__.py
│       ├── requests.py          # Pydantic request models
│       └── responses.py         # Pydantic response models (KnowledgeCore etc.)
│
├── core/
│   ├── __init__.py
│   ├── github_client.py         # GitHub REST API ingestion (async, concurrent)
│   ├── gemini_client.py         # All Gemini API calls — 4 methods
│   ├── firebase_client.py       # Firebase RTDB read/write with caching
│   ├── prompts.py               # ALL prompt templates — zero inline prompts elsewhere
│   ├── parser.py                # Gemini JSON dict → Pydantic KnowledgeCore
│   └── translation.py           # Google Translate BABEL layer
│
├── static/
│   ├── index.html               # Full SPA — all sections defined here
│   ├── css/
│   │   ├── reset.css            # Browser reset
│   │   ├── design-system.css    # All CSS variables (--accent-primary etc.)
│   │   ├── components.css       # Cards, chips, badges, panels
│   │   ├── animations.css       # Keyframes, stagger, skeleton loaders
│   │   └── layout.css           # Page layout, header, hero, tools grid
│   └── js/
│       ├── app.js               # State machine + main controller
│       ├── api.js               # fetch() wrappers for all /api/* endpoints
│       ├── ui.js                # Pure render functions (return HTML strings)
│       └── panels.js            # Tab switching + tool panel event wiring
│
└── tests/
    ├── test_github.py
    ├── test_gemini.py
    └── test_parser.py
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- A Google AI Studio account (for Gemini API key)
- A Firebase project with Realtime Database enabled
- A GitHub account (optional token for higher rate limits)

### Step 1 — Clone and Install

```bash
git clone https://github.com/your-username/gitspire.git
cd gitspire
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env` — see [Environment Variables](#environment-variables) below.

### Step 3 — Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Project Settings → Service Accounts → Generate new private key
3. Rename the downloaded file to `firebase-credentials.json`
4. Place it in the project root
5. Ensure it's in `.gitignore` — **never commit this file**

### Step 4 — Run

```bash
uvicorn main:app --reload --port 8000
```

Open: **http://localhost:8000**

### Step 5 — Verify

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/psf/requests"}'
```

Expected: JSON response with `success: true` and a populated `knowledge_core`.

### Pre-cache Demo Repositories

Run this before any demo to ensure instant responses:

```bash
python -c "
import asyncio
from core.github_client import GitHubClient
from core.gemini_client import GeminiClient
from core.firebase_client import FirebaseClient
from core.parser import parse_knowledge_core

async def precache(url):
    gh = GitHubClient()
    gem = GeminiClient()
    fb = FirebaseClient()
    owner, repo = gh.parse_repo_url(url)
    bundle = await gh.fetch_repository_bundle(owner, repo)
    ctx = gh.build_archaeology_context(bundle)
    raw = await gem.analyze_repository(ctx)
    core = parse_knowledge_core(url, raw)
    await fb.save_knowledge_core(url, core.model_dump())
    print(f'✓ Cached: {url}')

repos = [
    'https://github.com/psf/requests',
    'https://github.com/pallets/flask',
    'https://github.com/tiangolo/fastapi',
]
asyncio.run(asyncio.gather(*[precache(r) for r in repos]))
"
```

---

## Environment Variables

```dotenv
# ── REQUIRED ──────────────────────────────────────────────

# Gemini API Key
# Get from: https://aistudio.google.com → Get API Key
GEMINI_API_KEY=AIzaSy...

# Firebase Realtime Database URL
# Get from: Firebase Console → Realtime Database → copy the URL
FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com

# Path to Firebase service account credentials JSON
# Get from: Firebase Console → Project Settings → Service Accounts → Generate Key
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json


# ── OPTIONAL ──────────────────────────────────────────────

# GitHub Personal Access Token
# Without: 60 requests/hour | With: 5,000 requests/hour
# Get from: https://github.com/settings/tokens → classic → public_repo scope
GITHUB_TOKEN=ghp_...

# Enable multilingual repository support (BABEL layer)
# Requires GOOGLE_TRANSLATE_API_KEY if set to true
TRANSLATION_ENABLED=false

# Google Translate API Key (only needed if TRANSLATION_ENABLED=true)
# Get from: Google Cloud Console → APIs & Services → Credentials
GOOGLE_TRANSLATE_API_KEY=AIzaSy...
```

---

## The BABEL Layer — Multilingual Support

GitSpire includes an optional translation layer (`core/translation.py`) that normalizes non-English repository content before sending it to Gemini. This is important because many open source repositories have contributors writing commit messages, issue titles, and PR descriptions in their native language.

### Without BABEL

```
Commits ingested: 847
Commits Gemini sees in full: 312  ← English only
Decision atoms extracted: 6
Languages missed: Chinese, Japanese, Portuguese
```

### With BABEL

```
Commits ingested: 847
Languages detected: English, Chinese (Simplified), Japanese, Portuguese
Translated by Google Translate: 535 commits, 48 issues, 23 PRs
Decision atoms extracted: 11  ← 5 new ones from non-English artifacts
Languages detected shown in UI: 🇺🇸 🇨🇳 🇯🇵 🇧🇷
```

### How It Works

```python
# translation.py
class TranslationLayer:
    def __init__(self):
        self.client = translate.Client()  # google-cloud-translate

    def detect_and_translate(self, text: str) -> TranslationResult:
        detected = self.client.detect_language(text)
        if detected["language"] == "en" or detected["confidence"] < 0.8:
            return TranslationResult(original=text, translated=text, lang="en")
        result = self.client.translate(text, target_language="en")
        return TranslationResult(
            original=text,
            translated=result["translatedText"],
            lang=detected["language"]
        )
```

The translated text replaces the original in the archaeology context. Both versions are preserved in the bundle. Language statistics are attached to the Knowledge Core and shown in the UI.

### Enable BABEL

```dotenv
TRANSLATION_ENABLED=true
GOOGLE_TRANSLATE_API_KEY=AIzaSy...
```

---

## GitSpire Guard

GitSpire Guard is the next-layer capability: a **GitHub App** that uses the stored Knowledge Core to automatically review PRs for architectural violations before they merge.

### Concept

Once a repository is analyzed and its Knowledge Core is stored in Firebase, Guard can be installed as a GitHub App on that repository. When any PR is opened:

```
PR opened on GitHub
       ↓
GitHub sends webhook → POST /webhook/github (Guard server)
       ↓
Guard fetches PR diff via GitHub API
       ↓
Guard loads Knowledge Core from Firebase (instant — already cached)
       ↓
Single Gemini call: "Does this diff violate any decisions or assumptions?"
       ↓
Guard posts automated PR review comment on GitHub
       ↓
Firebase Cloud Messaging sends push notification to developer's browser
```

### What a Guard Review Comment Looks Like

```
⚡ GitSpire Guard — Architectural Review

DNA Score: 71/100  ⚠️ Review Recommended

✅ CONSISTENT   Decision Atom #1
   Your change correctly follows the async-first pattern.

⚠️ REVIEW       Decision Atom #4
   This PR bypasses JWT validation on internal routes.
   Original reasoning (commit abc1234) requires all routes to validate.

🔴 VIOLATION    Assumption #2
   This codebase assumes Redis is always optional.
   Your change (cache.service.js:47) introduces a hard Redis dependency.
```

### Guard is Currently a Capability Preview

The GitSpire UI includes a Guard panel that explains this flow. The `/webhook/github` endpoint is scaffolded and ready for a GitHub App registration — it is not activated by default as it requires a registered GitHub App installation.

---

## Deployment

### Railway (Recommended)

**`railway.json`:**
```json
{
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**Environment variables to set in Railway dashboard:**
- `GEMINI_API_KEY`
- `FIREBASE_DATABASE_URL`
- `FIREBASE_CREDENTIALS_JSON` — base64-encoded content of `firebase-credentials.json`

**Decode credentials at startup** (add to `main.py` lifespan):
```python
import base64, json, tempfile, os

creds_b64 = os.environ.get("FIREBASE_CREDENTIALS_JSON")
if creds_b64:
    creds_json = base64.b64decode(creds_b64).decode()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(creds_json)
        os.environ["FIREBASE_CREDENTIALS_PATH"] = f.name
```

### `Procfile`

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Iron Rules

These rules are enforced throughout the codebase and must never be broken:

```
1. All Gemini calls → core/gemini_client.py ONLY
2. All prompt strings → core/prompts.py ONLY (zero inline prompts in routes)
3. All Firebase operations → core/firebase_client.py ONLY
4. API routes are thin — orchestrate core/, contain zero business logic
5. Frontend calls only /api/* — never GitHub or Gemini directly
6. All CSS colors are CSS variables from design-system.css — no hardcoded hex anywhere
7. All error responses → { "success": false, "error": str, "error_code": str }
8. No placeholder functions — every function is fully implemented
```

---

## Error Reference

| Error Code | HTTP | Meaning |
|---|---|---|
| `INVALID_URL` | 400 | Not a valid `github.com/{owner}/{repo}` URL |
| `REPO_NOT_FOUND` | 404 | GitHub returned 404 for this repository |
| `RATE_LIMITED` | 429 | More than 10 analysis calls/hour from this IP |
| `GITHUB_ERROR` | 502 | GitHub API call failed |
| `GEMINI_ERROR` | 502 | Gemini API call failed or timed out |
| `PARSE_ERROR` | 500 | Could not parse Gemini's JSON response |
| `NOT_ANALYZED` | 404 | Tool called but repository not yet analyzed |
| `INTERNAL_ERROR` | 500 | Unhandled exception |

---

## Hackathon Context

**Event:** Codesprint with Gemini 

**Core Gemini Feature Demonstrated:**
> Gemini 1.5 Pro's **1 million token long-context window** used to ingest an entire GitHub repository — commits, issues, PRs, file contents — in a single API call, with no RAG, no chunking, and no context loss. This is what makes GitSpire possible. No other approach would allow the full archaeological trace needed to extract WHY-layer insights from the complete artifact trail.

**Team:** DRAGORITHM

| Member | Role |
|---|---|
| Senaaravichandran A | Backend architecture, Gemini integration, Firebase pipeline |
| Gowshik S | Frontend design, API wiring, deployment |

---

<div align="center">

Built with ♥ by **DRAGORITHM**

*Codesprint with Gemini · Google AI Hackathon · 2025*

</div>
