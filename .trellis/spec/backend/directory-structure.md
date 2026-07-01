# Directory Structure

## Overview

The backend is a FastAPI application under `backend/app`. It owns API validation, service orchestration, SQLite persistence, scheduler lifecycle, GitHub Trending parsing, and OpenAI-compatible LLM calls.

## Directory Layout

```text
backend/
  requirements.txt
  app/
    main.py                  # FastAPI app, CORS, startup/shutdown, SPA static fallback
    db.py                    # SQLAlchemy engine/session and schema initialization
    models.py                # SQLAlchemy ORM tables
    schemas.py               # Pydantic request/response contracts
    scheduler.py             # APScheduler job ownership
    api/                     # Route modules only
      health.py
      settings.py
      trending.py
      market_prices.py       # Gold/silver market quote route
    core/
      config.py              # Environment keys, data paths, constants
    services/                # Business logic and external integration boundaries
      settings.py
      trending.py            # GitHub HTML fetch/parse boundary
      llm.py                 # OpenAI-compatible Chat Completions boundary
      refresh.py             # Refresh orchestration and persistence
      market_prices.py       # Gold/silver quote and CNY conversion boundary
```

## Scenario: GitHub Trending Module Backend Slice

### 1. Scope / Trigger

- Trigger: cross-layer feature with API routes, SQLite tables, scheduler state, external GitHub HTML, and LLM integration.
- Applies when adding or extending feature modules under the Window of Eternity portal.

### 2. Signatures

- `GET /api/health`
- `GET /api/settings`
- `PUT /api/settings`
- `GET /api/trending?since=daily|weekly|monthly&language=<optional>&run_id=<optional>`
- `POST /api/trending/refresh`
- `POST /api/trending/analyze`
- `GET /api/trending/stats?since=daily|weekly|monthly&language=<optional>&run_id=<optional>`
- `GET /api/trending/history?limit=<1..100>`

SQLite tables:

- `settings` with refresh time-of-day, UI font size, and custom LLM prompt fields
- `refresh_runs` with full-list AI summary fields (`ai_summary_status`, `ai_summary`, `ai_summary_error`)
- `repositories` with detail-page enrichment fields (`detail_description`, JSON-encoded `topics`, `readme_excerpt`)
- `analysis_results` for append-only per-run/per-repository AI introductions

### 3. Contracts

Environment keys:

- `WINDOW_ETERNITY_DATA_DIR`: optional data directory; defaults to `<repo>/data`.
- `WINDOW_ETERNITY_DATABASE_URL`: optional SQLAlchemy URL; overrides default SQLite path.
- `WINDOW_ETERNITY_FRONTEND_DIST`: optional frontend build path; defaults to `<repo>/frontend/dist`.
- `WINDOW_ETERNITY_PORT`: optional runtime port; defaults to `3030`.

Response contract rules:

- Never return raw `llm_api_key`; return `has_llm_api_key` only.
- Settings responses expose `refresh_time_of_day` (`HH:MM`), `font_size_percent` (80..140), and `llm_custom_prompt`; `refresh_interval_minutes` is compatibility-only for this MVP.
- Scheduler code must use `refresh_time_of_day` with cron semantics, not `refresh_interval_minutes`.
- Trending repository payloads must use Pydantic schemas from `schemas.py`.
- Frontend-facing errors must be visible in `refresh_runs.error_message`, `refresh_runs.ai_summary_error`, or `analysis_results.error_message`.
- Refresh history responses return recent `RefreshRunResponse` records ordered newest first and are owned by `services/refresh.py`.
- Historical run viewing uses `run_id` on `/api/trending` and `/api/trending/stats`; when `run_id` is present it takes precedence over `since` and `language` filters.
- Trending stats responses expose repository count and `language_distribution`; category distribution and top-repository rankings are not part of the frontend-facing stats contract.

### 4. Validation & Error Matrix

- Invalid `since` -> FastAPI query/body validation error.
- Invalid `refresh_time_of_day` -> Pydantic validation error before scheduler reschedule.
- Invalid `font_size_percent` outside 80..140 -> Pydantic validation error.
- Missing LLM config -> raw refresh may succeed; analysis rows use `config_error`.
- GitHub fetch failure -> refresh run status `failed` with message.
- GitHub parser finds no cards -> refresh run status `failed`; do not fake empty success.
- Partial LLM failures -> refresh run status `partial_success`; raw repositories and any successful full-list summary remain visible.

### 5. Good/Base/Bad Cases

- Good: GitHub fetch succeeds, settings contain valid LLM config, all repositories have `success` analysis rows.
- Base: GitHub fetch succeeds, LLM config is absent, repositories display with analysis `config_error`.
- Bad: parser selectors break and return no cards; the refresh run fails visibly.

### 6. Tests Required

- Compile/import check: `python -m compileall backend/app`.
- Smoke: `GET /api/health` returns 200.
- Smoke: `GET /api/settings` initializes SQLite and returns `default_since=daily`, `max_repositories_per_refresh=25`, `refresh_time_of_day=09:00`, and `font_size_percent=100`.
- Smoke: `GET /api/trending/history` returns a `runs` array without exposing repository HTML parsing details.
- Smoke: `GET /api/trending?run_id=<id>` and `GET /api/trending/stats?run_id=<id>` return the selected historical run data when the run exists.
- Parser test should use stored sample HTML before selector changes.
- Refresh tests should assert that raw repository data remains visible when LLM calls fail.

### 7. Wrong vs Correct

#### Wrong

```python
# Frontend or route code reaches into GitHub HTML details directly.
article.select_one("h2 a")
```

#### Correct

```python
# HTML selector logic stays in services/trending.py.
parsed_repos = parse_trending_html(html, limit=settings.max_repositories_per_refresh)
```


## Scenario: Market Prices Module Backend Slice

### 1. Scope / Trigger

- Trigger: cross-layer module that fetches external gold/silver quotes and displays CNY-converted prices in React.

### 2. Signatures

- `GET /api/market-prices`

Response schemas:

- `MarketPricesResponse`
- `MetalPriceResponse`

### 3. Contracts

- `services/market_prices.py` is the only owner of external quote and exchange-rate calls.
- Metal quotes use Gold API symbols `XAU` and `XAG`, returned in USD per troy ounce.
- USD/CNY uses `open.er-api.com/v6/latest/USD` and `rates.CNY`.
- The API returns `price_usd_per_ounce`, `usd_cny_rate`, `price_cny_per_ounce`, `price_cny_per_gram`, source timestamps, and backend `fetched_at`.
- The module does not persist quote snapshots in SQLite in this slice.

### 4. Validation & Error Matrix

- Metal quote HTTP/JSON failure -> HTTP 502 with visible `detail`.
- Missing or non-positive metal price -> HTTP 502 with visible `detail`.
- Missing or non-positive USD/CNY rate -> HTTP 502 with visible `detail`.
- Source currency other than USD for metal quotes -> HTTP 502 with visible `detail`.

### 5. Good/Base/Bad Cases

- Good: both metals and USD/CNY return valid data; UI shows CNY per troy ounce and CNY per gram.
- Base: one source timestamp is missing; response still includes backend `fetched_at`.
- Bad: quote provider blocks or changes payload; route returns 502 instead of fake/stale prices.

### 6. Tests Required

- Compile/import check: `python -m compileall backend/app`.
- Network smoke when allowed: `GET /api/market-prices` returns two prices with positive `price_cny_per_gram`.

### 7. Wrong vs Correct

#### Wrong

```typescript
// Component bypasses the backend source boundary.
fetch('https://api.gold-api.com/price/XAU')
```

#### Correct

```typescript
const prices = await getMarketPrices();
```

## Module Organization

- Route modules are thin: dependency injection, request schemas, service calls, response schemas.
- Services own side effects and external boundaries.
- `refresh.py` owns the complete refresh transaction and status semantics.
- `trending.py` is the only owner of GitHub Trending and repository detail-page HTML selectors.
- `llm.py` is the only owner of OpenAI-compatible request formatting, including the batch prompt that analyzes a full refreshed repository set in one request.
- `market_prices.py` is the only owner of gold/silver quote fetches and CNY conversion.

## Naming Conventions

- Backend files use snake_case.
- SQLAlchemy models use singular class names and plural table names.
- Pydantic response classes end in `Response`; request body classes end in `Request` or `Update`.
## Scenario: Docker Gateway Topology

### 1. Scope / Trigger

- Trigger: Docker deployment exposes one public host port while supporting future independently deployed modules under path prefixes.

### 2. Signatures

- Host entry: `gateway:3030` published as `3030:3030`.
- Internal backend: `backend:8000`, exposed only on the Docker network.
- nginx config: `nginx/default.conf`.

### 3. Contracts

- nginx owns public routing on port `3030`.
- React static assets are served by nginx from `/usr/share/nginx/html`.
- `/api/` is proxied to `http://backend:8000/api/`.
- Future independent modules should add nginx `location` blocks instead of binding additional host ports.

### 4. Validation & Error Matrix

- Missing Docker CLI -> document as unverified locally; do not claim Docker build passed.
- Broken nginx route -> `/` or `/github-trending` should fail before backend APIs are tested.
- Broken backend proxy -> static pages load but `/api/health` fails through gateway.

### 5. Good/Base/Bad Cases

- Good: `http://127.0.0.1:3030/` serves React, `/api/health` proxies to FastAPI.
- Base: backend can still run directly for local development without nginx.
- Bad: FastAPI publishes host `3030` in Docker and bypasses nginx, preventing future module routing.

### 6. Tests Required

- `docker compose config` when Docker CLI is available.
- `docker compose up --build` then verify `/`, `/github-trending`, and `/api/health` through port `3030`.

### 7. Wrong vs Correct

#### Wrong

```yaml
services:
  backend:
    ports:
      - "3030:3030"
```

#### Correct

```yaml
services:
  backend:
    expose:
      - "8000"
  gateway:
    ports:
      - "3030:3030"
```
