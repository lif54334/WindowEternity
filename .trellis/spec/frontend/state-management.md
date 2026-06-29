# State Management

## Overview

Frontend state is currently page-local React state plus browser URL path state. There is no global state library. Server-owned data is loaded through typed API client functions and stored in the page that renders it.

## State Categories

- Route state: `App.tsx` normalizes `window.location.pathname` into the local `Route` union and updates browser history with `pushState`.
- Settings state: `SettingsPage.tsx` loads `SettingsResponse`, edits a `SettingsUpdate` form object, and sends normalized values through `saveSettings`.
- Trending dashboard state: `GitHubTrendingPage.tsx` owns filters, `TrendingResponse`, `TrendingStatsResponse`, refresh history, loading state, busy action state, and visible errors.
- Font-size preference: backend settings persist `font_size_percent`; `App.tsx` and `SettingsPage.tsx` apply it to `--app-font-scale`.
- Server state: FastAPI/SQLite remain the source of truth for settings, refresh runs, repositories, analyses, and statistics.

## When To Use Global State

Do not add global state for the current app shape. Consider it only if:

- multiple independent feature modules need the same client-side state;
- route handling grows beyond the current three static routes;
- settings must be edited or observed from several pages at once.

## Server State

- Load server data through `src/api/client.ts` functions.
- The dashboard should refresh trending data, stats, and history together after manual refresh or manual analyze.
- Blank language filters should be sent as `null` for refresh/analyze requests and omitted from query strings for GET requests.
- Do not cache stale analysis locally after a refresh response returns newer repository/run data.

## Common Mistakes

- Do not create a frontend-only source of truth for settings that can diverge from SQLite.
- Do not store raw `llm_api_key` in React state beyond the password input needed for save.
- Do not duplicate history or stats data by deriving separate arrays that are not refreshed after server mutations.
- Do not bypass `applyFontSize`; font scaling must stay centralized on `--app-font-scale`.
