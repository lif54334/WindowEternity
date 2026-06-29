# Implementation Plan

## Preconditions

- PRD reviewed and accepted.
- This `design.md` reviewed and accepted.
- This `implement.md` reviewed and accepted.
- Task started with `python ./.trellis/scripts/task.py start 06-29-window-eternity-github-trending` before code changes.

## Implementation Steps

1. Scaffold project structure
   - Create `backend/` FastAPI package.
   - Create `frontend/` React + Vite + TypeScript app files.
   - Add root Docker and compose files.
   - Add README or run instructions for local and Docker execution.

2. Backend foundation
   - Add backend dependency file.
   - Add FastAPI app, CORS/dev settings, health route, static frontend serving.
   - Add SQLite engine/session setup and schema initialization.
   - Add SQLAlchemy models and Pydantic schemas.

3. Settings persistence
   - Implement singleton settings read/update service.
   - Store LLM API key but never return it raw.
   - Store UI font-size percent, time-of-day refresh setting, and custom LLM prompt text.
   - Add API routes for `GET /api/settings` and `PUT /api/settings`.

4. GitHub Trending refresh
   - Implement URL builder for `daily`, `weekly`, `monthly`, and optional programming language.
   - Implement `httpx` fetch with timeout and user agent.
   - Implement BeautifulSoup parser isolated in `services/trending.py`.
   - Fetch and parse each visible repository detail page for description/topics/README excerpt without leaking selectors outside `services/trending.py`.
   - Persist refresh runs and repository records.
   - Add `GET /api/trending` and `POST /api/trending/refresh`.

5. LLM analysis
   - Implement OpenAI-compatible Chat Completions client.
   - Add batch repository analysis prompt and result persistence.
   - Include saved custom prompt instructions in the batch prompt when provided.
   - Make refresh orchestration re-analyze all repositories in the refreshed result set in one LLM call when valid LLM settings exist.
   - Persist and expose the AI summary for the whole refreshed repository set.
   - Keep failures visible without hiding raw trending data.
   - Add `POST /api/trending/analyze` for manual retry.

6. Statistics
   - Implement backend stats endpoint based on latest/current dataset.
   - Include repository count, language distribution, top-star repositories, and analysis-derived categories when present.

7. Scheduler
   - Add APScheduler startup/shutdown integration.
   - Schedule refresh at the configured time of day using settings.
   - Replace the job when settings change.

8. Frontend API client
   - Define typed DTOs once in `frontend/src/api/client.ts`.
   - Add fetch wrappers for settings, trending list, refresh, analyze, stats, and refresh history.
   - Surface backend errors in the UI.

9. Frontend pages
   - Build portal homepage with module navigation.
   - Build GitHub Trending page with filters, repository cards/table, statistics, refresh status, and manual analyze retry.
   - Show manual refresh waiting/progress state, current analysis timestamps, and a left-side history rail when history exists.
   - Build settings page for schedule time, max repositories, selected defaults, UI font size, LLM settings, and editable AI prompt text.
   - Use responsive layout suitable for desktop and mobile.

10. Docker and runtime integration
    - Add multi-stage Dockerfile.
    - Add docker-compose exposing `3030:3030` and persisting `/app/data`.
    - Verify frontend routes are served by FastAPI fallback.

11. Documentation and cleanup
    - Document local dev commands and Docker commands.
    - Ensure `.gitignore` covers local SQLite/data/env artifacts if needed.

## Validation Commands

Run the strongest available checks after implementation:

- Backend syntax/import check: `python -m compileall backend`
- Backend tests if added: `pytest`
- Frontend install/build: `npm.cmd install` then `npm.cmd run build` inside `frontend/`
- Docker config/build if dependencies are available: `docker compose build`
- Runtime smoke test: start app and check `http://127.0.0.1:3030/` plus `GET /api/health`

Network-dependent checks that fetch GitHub or call the LLM may require explicit approval because network access is restricted in this environment.

## Risk Points

- GitHub Trending HTML may change; parser tests should use stored sample HTML when possible.
- Automatic full-list LLM analysis can be slow or costly; UI must show in-progress/failure states.
- SQLite scheduler in a single process is fine for MVP but not safe for multi-worker scaling.
- LLM API key must not be displayed raw in settings responses or frontend state dumps.
- Docker build requires package downloads and may need network approval.

## Rollback Points

- If frontend scaffolding fails, keep backend API independent and defer UI styling.
- If LLM integration blocks, keep refresh and raw repository display working while surfacing analysis configuration/request errors.
- If Docker build cannot run locally due network restrictions, verify source-level build files and document the command that needs network access.
