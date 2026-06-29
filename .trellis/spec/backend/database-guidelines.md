# Database Guidelines

## Overview

The backend uses SQLAlchemy ORM with SQLite for the MVP. Schema initialization is centralized in `backend/app/db.py` with `Base.metadata.create_all`. Add migrations only when schema evolution becomes necessary beyond local MVP development.

## Query Patterns

- Use `Session` injected by `get_db` for API requests.
- Use `SessionLocal` for scheduler jobs and background orchestration.
- Commit after coherent state changes: settings update, refresh run completion, or per-repository LLM analysis persistence.
- Keep repository upsert logic in `services/refresh.py`; routes must not modify ORM rows directly.

## Schema Contracts

- `settings` is a singleton row with id `1` and owns user configuration: `auto_refresh_enabled`, compatibility `refresh_interval_minutes`, cron-style `refresh_time_of_day` (`HH:MM`), default filters, `max_repositories_per_refresh`, `font_size_percent`, LLM endpoint/model/timeout/API key, and `llm_custom_prompt`.
- `repositories` is unique by `(owner, name)` and stores latest visible metadata plus nullable detail-page enrichment fields (`detail_description`, `topics`, `readme_excerpt`).
- `refresh_runs` records every refresh attempt and owns user-visible status plus the batch AI summary (`ai_summary_status`, `ai_summary`, `ai_summary_error`). It is also the source for refresh/analysis history UI records ordered by newest run id.
- `analysis_results` is append-only per run/repository so each refresh can re-analyze all current repositories; per-repository rows come from the batch LLM response, while the overall summary belongs to `refresh_runs`.

## Common Mistakes

- Do not derive SQLite paths with Windows backslashes inside the SQLAlchemy URL. Use POSIX formatting: `sqlite:///{path.as_posix()}`.
- Do not return raw API keys from settings queries.
- Do not schedule auto refresh from `refresh_interval_minutes`; use `refresh_time_of_day` and keep the interval field only for compatibility until it is removed by an explicit migration.
- Do not treat an empty GitHub parse as a successful empty refresh; that usually means the external HTML contract changed.
