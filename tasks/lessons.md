# Lessons

- Do not ship fake repository verdict values in static HTML. Render a neutral pre-analysis state, then populate the guard card from live analysis data.
- Keep the Gemini model selection pinned in backend code, and let the frontend read the visible model label from backend metadata instead of hardcoding it in the static UI.
- When the frontend can be served by a plain static server, do not assume same-origin `/api/*` requests. Resolve the GitSpire API base explicitly or probe for the backend first.
- Add backward-compatible defaults to response models when cached Firebase payloads may have been written by an older schema version.
- For deployment, keep public frontend/backend URLs backend-owned via env-backed `/api/meta` fields and retain localhost fallbacks for local runs.