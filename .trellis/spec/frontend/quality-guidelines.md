# Quality Guidelines

## Overview

Frontend quality depends on TypeScript correctness, centralized API contracts, visible async states, and route-level smoke checks.

## Forbidden Patterns

- `any` for API request or response payloads.
- Raw `fetch('/api/...')` in page components.
- Page-local duplicated DTOs for settings, trending repositories, stats, refresh runs, or analysis rows.
- Hidden async work without a loading/busy/error state.
- Rendering raw saved LLM API keys.
- Adding portal homepage content to the feature-shell layout.

## Required Patterns

- Add or update DTOs and client functions in `src/api/client.ts` before consuming new backend fields.
- Keep page components consuming typed client functions.
- Keep settings save normalization aligned with backend Pydantic blank-to-null behavior.
- Preserve manual refresh waiting/progress state when changing refresh UI.
- Preserve responsive layouts for the topbar, toolbar, metric grid, split dashboard, history rail, repository items, and settings form.

## Testing Requirements

Minimum frontend check:

```powershell
cd frontend
npm.cmd run build
```

For UI changes, smoke-test:

- `/`
- `/github-trending`
- `/github-trending/settings`
- manual refresh busy state when network access is available
- font-size slider applying `--app-font-scale`

## Code Review Checklist

- Does every consumed backend field come from `src/api/client.ts`?
- Are loading, busy, success, and failure states visible?
- Are history and stats reloaded after refresh/analyze actions?
- Are text labels and buttons readable at 80% and 140% font scale?
- Does the page still work on mobile-width layouts?
- Are Chinese UI strings encoded correctly in source and in the built page?
