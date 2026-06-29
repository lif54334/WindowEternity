# Backend Development Guidelines

> Project-specific backend conventions for Window of Eternity.

## Overview

The backend is a Python FastAPI application under `backend/app`. It owns API validation, SQLite persistence, refresh orchestration, scheduled jobs, GitHub Trending HTML parsing, and OpenAI-compatible LLM calls.

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization, API boundaries, Docker gateway topology | Filled |
| [Database Guidelines](./database-guidelines.md) | SQLAlchemy/SQLite table ownership and query rules | Filled |
| [Error Handling](./error-handling.md) | Visible refresh, parser, settings, and LLM failures | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Backend validation and review requirements | Filled |
| [Logging Guidelines](./logging-guidelines.md) | Scheduler logging and secret-handling rules | Filled |

## Pre-Development Checklist

Before changing backend code:

1. Read this index.
2. Read [Directory Structure](./directory-structure.md) for API/service ownership boundaries.
3. Read [Database Guidelines](./database-guidelines.md) when touching models, persistence, settings, refresh history, or analysis rows.
4. Read [Error Handling](./error-handling.md) when touching GitHub fetch/parse, LLM calls, scheduler jobs, or user-visible status fields.
5. Read [Quality Guidelines](./quality-guidelines.md) before validation.
6. Read [Logging Guidelines](./logging-guidelines.md) before adding logs.
7. For cross-layer API changes, also read `../guides/cross-layer-thinking-guide.md` and the frontend type-safety spec.

## Quality Check

Backend changes should be checked with:

```powershell
python -m compileall backend/app
```

When dependencies and runtime are available, also smoke-test:

- `GET /api/health`
- `GET /api/settings`
- `GET /api/trending/history`

Network-dependent GitHub and LLM checks require explicit network access.

**Language**: All documentation should be written in **English**.
