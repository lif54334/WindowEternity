# Window of Eternity

Window of Eternity / 新世界的窗口 is a local module portal. The first module is a GitHub Trending dashboard that collects repository snapshots, enriches them with repository page details, persists local refresh history, and can run OpenAI-compatible LLM analysis for the refreshed repository set.

## Current Scope

- Portal homepage at `/` for launching feature modules.
- GitHub Trending module at `/github-trending`.
- GitHub Trending settings page at `/github-trending/settings`.
- FastAPI backend API under `/api`.
- Docker Compose deployment with one public gateway on `http://127.0.0.1:3030/`.

The application is currently designed as a local single-user tool. It does not include login, multi-user permissions, or public-network hardening.

## Stack

- Frontend: React, Vite, TypeScript.
- Backend: FastAPI, SQLAlchemy, Pydantic, APScheduler.
- Persistence: SQLite.
- External integrations: GitHub Trending HTML via `httpx` + BeautifulSoup; OpenAI-compatible Chat Completions via `httpx`.
- Deployment: multi-stage Docker build with nginx gateway on port `3030` and backend on Docker-internal port `8000`.

## Repository Layout

```text
backend/
  app/
    api/              # FastAPI route modules
    core/config.py    # environment-driven paths and runtime defaults
    services/         # settings, GitHub scraping, refresh orchestration, LLM client
    db.py             # SQLAlchemy engine/session and SQLite schema initialization
    main.py           # FastAPI app, CORS, scheduler lifecycle, SPA fallback
    models.py         # ORM tables
    schemas.py        # API request/response contracts
    scheduler.py      # APScheduler refresh job
frontend/
  src/
    api/client.ts     # typed API DTOs and fetch wrappers
    pages/            # portal, trending dashboard, settings
    App.tsx           # route shell and font-size bootstrap
    styles.css        # shared UI styling
nginx/default.conf    # public gateway: static frontend + /api proxy
Dockerfile            # frontend builder, backend runtime, nginx gateway stages
docker-compose.yml    # backend + gateway services and SQLite data volume
```

## Backend API

- `GET /api/health`
- `GET /api/settings`
- `PUT /api/settings`
- `GET /api/trending?since=daily|weekly|monthly&language=<optional>`
- `POST /api/trending/refresh`
- `POST /api/trending/analyze`
- `GET /api/trending/stats`
- `GET /api/trending/history?limit=<1..100>`

Settings responses never return the raw LLM API key. They return `has_llm_api_key` instead.

## Data Model

SQLite is initialized automatically on backend startup. The default local path is `./data/window_eternity.db`; Docker stores it in the `window_eternity_data` volume.

Main tables:

- `settings`: singleton runtime configuration, including default filters, time-of-day scheduler setting, max repositories per refresh, UI font-size percentage, LLM endpoint/model/API key, and custom analysis prompt.
- `refresh_runs`: append-only refresh attempts, source URL, status, timestamps, visible error text, and full-list AI summary status/text/error.
- `repositories`: latest repository metadata by owner/name, including Trending card metadata plus detail-page description, topics, and README excerpt.
- `analysis_results`: append-only per-run/per-repository LLM analysis rows.

`backend/app/db.py` currently uses `Base.metadata.create_all` plus a small SQLite column backfill helper for MVP schema evolution. There is no migration framework yet.

## GitHub Trending Module

Supported behavior:

- `daily`, `weekly`, and `monthly` ranges.
- Optional programming-language filter.
- Manual refresh from the UI.
- Scheduled refresh at a configured `HH:MM` time of day when enabled.
- Repository detail-page enrichment for description, topics, and README excerpt when available.
- Refresh/analysis history shown by the dashboard when history exists.
- Statistics for repository count, language distribution, top repositories, and analysis categories.

Out of scope for the MVP:

- GitHub Trending Developers.
- Spoken-language filtering.
- Fetching beyond the visible GitHub Trending result set.

## LLM Analysis

The backend targets OpenAI-compatible Chat Completions.

Settings:

- `llm_base_url`
- `llm_api_key`
- `llm_model`
- `llm_timeout_seconds`
- `llm_custom_prompt`

When valid LLM settings exist, each refresh submits the refreshed repository set in one batch request and stores:

- one overall summary on the `refresh_runs` row;
- one per-repository introduction/category/reason row in `analysis_results`.

If LLM settings are missing or a request fails, raw Trending data remains visible and the analysis error is persisted for the UI.

## Local Development

Run the backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 3030
```

Run the frontend dev server:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

The Vite dev server uses `frontend/vite.config.ts` to proxy `/api` to `http://127.0.0.1:3030`.

## Docker

```powershell
docker compose up --build
```

Open `http://127.0.0.1:3030/`.

Compose services:

- `gateway`: nginx listens on host port `3030`, serves `frontend/dist`, and proxies `/api/` to `backend:8000`.
- `backend`: Uvicorn/FastAPI listens on internal Docker port `8000` and is not published directly to the host.

Future independent modules should be mounted by extending `nginx/default.conf` with additional path-based `location` blocks instead of binding more public ports.

## Environment Variables

- `WINDOW_ETERNITY_DATA_DIR`: data directory; defaults to `<repo>/data`.
- `WINDOW_ETERNITY_DATABASE_URL`: SQLAlchemy database URL; overrides the default SQLite file.
- `WINDOW_ETERNITY_FRONTEND_DIST`: frontend build directory for FastAPI SPA fallback; defaults to `<repo>/frontend/dist`.
- `WINDOW_ETERNITY_HOST`: backend host default for direct backend runs.
- `WINDOW_ETERNITY_PORT`: backend port default for direct backend runs; Docker sets this to `8000`.

## Verification

Recommended checks:

```powershell
python -m compileall backend/app
cd frontend
npm.cmd install
npm.cmd run build
```

When Docker is available:

```powershell
docker compose config
docker compose up --build
```

Then verify:

- `http://127.0.0.1:3030/`
- `http://127.0.0.1:3030/github-trending`
- `http://127.0.0.1:3030/github-trending/settings`
- `http://127.0.0.1:3030/api/health`

Network-dependent refresh and LLM checks require access to GitHub and the configured LLM provider.

## Current Maintenance Notes

- GitHub HTML parsing is intentionally isolated in `backend/app/services/trending.py`.
- API DTOs and client functions are centralized in `frontend/src/api/client.ts`.
- The scheduler uses `refresh_time_of_day`; `refresh_interval_minutes` remains only as a compatibility field.
- UI font-size preference is applied through the root CSS variable `--app-font-scale`.
- Some Chinese UI/LLM copy should be verified during frontend build and browser smoke testing because source encoding issues are easy to miss on Windows terminals.
