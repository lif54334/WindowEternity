# Technical Design

## Scope

Build the first application slice for Window of Eternity:

- A React + Vite + TypeScript frontend for the project portal and GitHub Trending module.
- A Python FastAPI backend exposing APIs consumed by the frontend.
- SQLite persistence for settings, refresh runs, repository snapshots, and LLM analysis results.
- Docker deployment that serves the built frontend and backend on port `3030`.

## Architecture

```
Browser\n  -> nginx gateway on :3030\n  -> React/Vite static app or /api proxy\n  -> FastAPI API routes on internal :8000
  -> service layer
  -> SQLite repositories
  -> GitHub Trending HTML source / OpenAI-compatible LLM API
```

### Frontend

Planned directory:

- `frontend/`
  - `src/App.tsx`: route shell and layout.
  - `src/pages/HomePage.tsx`: module launcher.
  - `src/pages/GitHubTrendingPage.tsx`: repository list, filters, stats, refresh/analyze status.
  - `src/pages/SettingsPage.tsx`: refresh schedule, max repositories, LLM config.
  - `src/api/client.ts`: API client and typed DTOs.
  - `src/styles.css`: app styling.

Frontend routes:

- /: standalone portal homepage with only module-launcher content; no feature sidebar.
- /github-trending: GitHub Trending feature shell with display and statistics.
- /github-trending/settings: GitHub Trending feature shell with module settings.

The frontend owns presentation state only. API response shapes are defined once in `src/api/client.ts`; page components consume those types instead of re-defining payload fields.

### Backend

Planned directory:

- `backend/app/main.py`: FastAPI app factory, startup/shutdown, static frontend serving.
- `backend/app/api/`: route modules.
- `backend/app/core/config.py`: runtime paths and defaults.
- `backend/app/db.py`: SQLite engine/session and schema initialization.
- `backend/app/models.py`: SQLAlchemy models.
- `backend/app/schemas.py`: Pydantic request/response schemas.
- `backend/app/services/trending.py`: GitHub Trending fetch and parse logic.
- `backend/app/services/llm.py`: OpenAI-compatible Chat Completions client.
- `backend/app/services/refresh.py`: refresh orchestration and persistence.
- `backend/app/services/settings.py`: settings persistence and masking.
- `backend/app/scheduler.py`: APScheduler lifecycle and job replacement.

Backend responsibilities:

- Validate incoming settings and refresh requests.
- Fetch GitHub Trending HTML with `httpx`.
- Parse repository cards with BeautifulSoup behind a single parser boundary.
- Fetch each visible repository page after parsing GitHub Trending and normalize richer introduction fields behind the same parser boundary.
- Persist refresh runs and current repository snapshot in SQLite.
- Run one automatic batch LLM analysis for all repositories in the refreshed result set when LLM settings are valid.
- Return visible refresh/analysis errors to the frontend.
- Return recent refresh/analysis history so the frontend can render a history rail.
- Persist UI font-size preference and custom LLM prompt instructions in settings.
- Serve the built frontend as static files for Docker deployment.

## Data Model

SQLite tables:

- `settings`
  - singleton row storing auto refresh enabled, refresh time of day, selected since value, selected language, max repositories, UI font size percent, LLM base URL, API key, model, timeout, and custom prompt instructions.
- `refresh_runs`
  - run id, source URL, since, language, status, started/finished timestamps, error message, batch AI summary status/text/error.
- `repositories`
  - latest repository record per owner/name plus source metadata: owner, name, URL, description, language, stars, forks, stars today, rank, detail page description, topics, README excerpt, last seen run id.
- `analysis_results`
  - run id, repository id, status, summary, category, reasons, error message, created timestamp.

The API should not return the raw LLM API key. Settings responses return only a boolean such as `has_api_key` and masked metadata.

## API Contract

Initial API routes:

- `GET /api/health`
- `GET /api/settings`
- `PUT /api/settings`
- `GET /api/trending?since=daily|weekly|monthly&language=<optional>`
- `POST /api/trending/refresh`
- `POST /api/trending/analyze`
- `GET /api/trending/stats`
- `GET /api/trending/history`

`POST /api/trending/refresh` should:

1. Read effective settings and request filters.
2. Create a `refresh_runs` row with status `running`.
3. Fetch and parse GitHub Trending up to `max_repositories_per_refresh`.
4. Persist the repository snapshot.
5. If LLM settings are valid, submit the whole refreshed repository set to the LLM and persist per-repository introductions plus the overall batch summary.
6. Mark the run `success`, `partial_success`, or `failed` with error details.
7. Return the current display payload and run status.

`POST /api/trending/analyze` should support manual retry for the current list and should re-analyze all repositories in scope.

`GET /api/trending/history` should return recent refresh runs ordered newest first, including start/finish timestamps, refresh status, AI summary status, AI summary/error, since, and language.

## GitHub Trending Parsing Boundary

GitHub Trending and repository detail HTML are external unstable sources. All selector logic must stay inside `services/trending.py`. The rest of the backend consumes normalized repository objects only.

The parser should record partial missing metadata as nullable fields instead of failing the whole refresh when one card lacks optional metadata.

Repository detail-page fetch failures should not hide the raw Trending list. The parser should preserve card data and simply leave detail fields empty when a specific repository page cannot be enriched.

## LLM Analysis Contract

Use OpenAI-compatible Chat Completions:

- Endpoint: `${base_url}/v1/chat/completions` unless the configured base URL already includes the full path.
- Auth: `Authorization: Bearer <api_key>`.
- Model: configured `model`.

The prompt should send all refreshed repositories together and ask for concise Chinese output containing:

- one overall summary of the current trending set;
- one per-repository introduction covering what it does, likely category, why it may be trending, and practical value.
- any saved custom prompt instructions as additional user-controlled guidance.

The backend should prefer JSON responses but tolerate plain text responses. If JSON parsing fails, fallback text should still preserve a useful overall summary.

## Scheduler

APScheduler runs in the backend process. Updating settings should replace the scheduled refresh job. The scheduler uses the saved settings and runs the same refresh orchestration as manual refresh.

Scheduled refresh uses a configured `HH:MM` time of day with APScheduler cron semantics in the service process timezone. The old interval setting may remain in storage for compatibility, but the UI and scheduler should use the time-of-day setting for this MVP.

For MVP Docker single-process deployment, this is acceptable. If the app later scales to multiple backend workers, scheduler ownership must be revisited to avoid duplicate jobs.

## Docker Deployment

Use Docker Compose with nginx as the public gateway:

1. Node stage builds `frontend/dist`.
2. `nginx-gateway` image copies `frontend/dist` and `nginx/default.conf`.
3. `gateway` service listens on host `3030`, serves static frontend routes, and proxies `/api/` to `backend:8000`.
4. `backend` service runs Uvicorn/FastAPI on Docker-internal `0.0.0.0:8000`.

This keeps host port `3030` as the single public entry point and leaves room for future independent modules to be mounted by adding nginx `location` rules such as `/new-module/ -> new-module-service:port`.

SQLite data should live under a configurable data directory such as `/app/data`, with a Docker volume recommendation in `docker-compose.yml`.

## Error Handling

- GitHub fetch errors should create a failed refresh run and show a visible UI message.
- GitHub parser changes should fail with a clear parser error instead of returning fake empty success.
- Missing LLM settings should allow raw repository refresh to succeed but mark analysis as skipped/configuration error.
- LLM request failures should mark analysis rows failed and keep raw repository data visible.
- Settings validation errors should return HTTP 422 with field-level messages where possible.

## Trade-Offs

- React + Vite + TypeScript adds frontend tooling but keeps future module expansion clean.
- SQLite adds schema work but keeps configuration, history, and statistics queryable.
- Re-analyzing all repositories on every refresh is intentionally more expensive but matches product intent for fresh analysis.
- Scraping GitHub Trending HTML is fragile; the parser boundary reduces blast radius when GitHub changes markup.


