# Frontend Development Guidelines

> Project-specific frontend conventions for Window of Eternity.

## Overview

The frontend is a React + Vite + TypeScript app under `frontend/`. It renders a portal homepage plus the GitHub Trending module, consumes FastAPI through typed client functions, and keeps server data in page-local state.

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | App shell, pages, API client, styling layout | Filled |
| [Component Guidelines](./component-guidelines.md) | Page/component composition and styling conventions | Filled |
| [Hook Guidelines](./hook-guidelines.md) | Current built-in hook patterns and data fetching rules | Filled |
| [State Management](./state-management.md) | Local UI state, server state, URL route state, font-size preference | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Frontend validation and review requirements | Filled |
| [Type Safety](./type-safety.md) | Shared API DTO and client contract rules | Filled |

## Pre-Development Checklist

Before changing frontend code:

1. Read this index.
2. Read [Directory Structure](./directory-structure.md) before adding pages, shared files, or module areas.
3. Read [Type Safety](./type-safety.md) before changing API payloads or client calls.
4. Read [State Management](./state-management.md) before adding route, settings, refresh, or history state.
5. Read [Component Guidelines](./component-guidelines.md) before changing UI layout.
6. Read [Quality Guidelines](./quality-guidelines.md) before validation.
7. For cross-layer API changes, also read `../guides/cross-layer-thinking-guide.md` and the backend directory/database specs.

## Quality Check

Frontend changes should be checked with:

```powershell
cd frontend
npm.cmd run build
```

For UI-affecting changes, smoke-test these routes after serving the build or running Vite:

- `/`
- `/github-trending`
- `/github-trending/settings`

**Language**: All documentation should be written in **English**.
