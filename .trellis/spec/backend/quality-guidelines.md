# Quality Guidelines

## Overview

Backend code should keep external integration boundaries narrow, preserve visible failure semantics, and keep API contracts centralized in Pydantic schemas.

## Forbidden Patterns

- GitHub HTML selector logic outside `backend/app/services/trending.py`.
- Route modules directly mutating ORM rows for refresh, repository, or analysis workflows.
- Returning raw `llm_api_key` in any schema, log, or API response.
- Treating missing LLM configuration as a successful analysis.
- Scheduling refreshes from `refresh_interval_minutes`; use `refresh_time_of_day` for this MVP.
- Using Windows backslashes inside SQLite SQLAlchemy URLs.

## Required Patterns

- Route modules should stay thin: dependency injection, request schema, service call, response schema.
- API request/response shapes live in `backend/app/schemas.py`.
- Settings persistence is owned by `services/settings.py`.
- Refresh orchestration, run status, repository upsert, statistics, and history projections are owned by `services/refresh.py`.
- LLM request formatting and response parsing are owned by `services/llm.py`.
- Database sessions come from `get_db` in request handlers and `SessionLocal` in scheduler/background work.

## Testing Requirements

Minimum backend check:

```powershell
python -m compileall backend/app
```

For behavioral work, add or run smoke checks for:

- `/api/health`
- `/api/settings`
- `/api/trending/history`
- refresh behavior with missing LLM settings
- parser behavior against stored sample HTML before changing selectors

## Code Review Checklist

- Does each new API field exist in `schemas.py`, the ORM model when persisted, and `frontend/src/api/client.ts` when consumed by React?
- Are raw repository results still visible when analysis fails?
- Are scheduler changes safe for one backend process and explicit about the single-process limitation?
- Are external failures persisted in a user-visible field?
- Are secrets masked or omitted from responses and logs?
