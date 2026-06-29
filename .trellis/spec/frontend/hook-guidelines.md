# Hook Guidelines

## Overview

The current frontend uses React built-in hooks only. There are no shared custom hooks or server-state libraries yet.

## Custom Hook Patterns

- Do not introduce a custom hook for one-off page logic.
- Create a custom hook only when stateful behavior is reused by at least two components or when a page component becomes hard to audit.
- Custom hooks must use the `use*` naming convention and return typed values/actions.

## Data Fetching

- Page components call typed client functions from `src/api/client.ts` inside `useEffect` and async event handlers.
- Keep `loading`, `busyAction`, `message`, and `error` state page-local unless multiple pages need the same state.
- Use `Promise.all` when the dashboard needs trending data, stats, and history together.
- Convert `ApiError` into user-visible messages at the page boundary.

## Naming Conventions

- Use `load*` for initial/reload fetch flows, e.g. `loadData` and `loadSettings`.
- Use `handle*` for event handlers, e.g. `handleRefresh`, `handleAnalyze`, and `handleSubmit`.
- Use `busyAction`-style discriminated state when one page can run multiple mutually exclusive async actions.

## Common Mistakes

- Do not add React Query/SWR without a clear cross-page caching need.
- Do not leave async errors only in the console; show them in page `error` state.
- Do not update server-derived state in multiple separate local shapes when one API response already contains the needed fields.
