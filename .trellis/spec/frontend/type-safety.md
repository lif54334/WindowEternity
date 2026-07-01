# Type Safety

## Overview

The frontend is a React + Vite + TypeScript app. API payload types are centralized in `frontend/src/api/client.ts` and page components consume those exported types.

## Type Organization

- Shared API DTOs live in `src/api/client.ts`.
- Page-local route prop types can stay in the page file when they are not reused across modules.
- `SinceValue` is the frontend representation of the backend `daily | weekly | monthly` contract.

## Validation

Runtime validation is currently performed by the backend Pydantic schemas. The frontend should still normalize blank optional fields before sending settings or refresh requests.

## Scenario: API Client Contract

### 1. Scope / Trigger

- Trigger: any new backend API response consumed by React.

### 2. Signatures

- Add one exported TypeScript interface per backend response/request body.
- Add one client function per endpoint.

### 3. Contracts

- Settings responses expose `has_llm_api_key`, never `llm_api_key`.
- Settings DTOs include `refresh_time_of_day`, `font_size_percent`, and `llm_custom_prompt`; page code must consume them through `SettingsResponse` / `SettingsUpdate`.
- Trending responses expose enriched repository fields (`detail_description`, `topics`, `readme_excerpt`) and full-list AI summary fields on `latest_run` (`ai_summary_status`, `ai_summary`, `ai_summary_error`).
- Refresh history uses `RefreshHistoryResponse` from `getRefreshHistory`; components must not fetch `/api/trending/history` directly.
- Historical run viewing passes `run_id` through the typed `getTrending` and `getTrendingStats` client functions instead of assembling query strings in page components.
- Refresh and analyze calls send blank language as `null`.
- Page components should not cast raw JSON payload fields inline.
- Market price responses use `MarketPricesResponse` / `MetalPriceResponse` from `getMarketPrices()`; components must not call external quote providers or `/api/market-prices` directly.

### 4. Validation & Error Matrix

- Non-2xx response -> `ApiError(status, message)`.
- JSON error body with string `detail` -> use that message.
- Non-JSON error body -> use default status message.

### 5. Good/Base/Bad Cases

- Good: component calls `refreshTrending(since, language)` and renders typed `TrendingResponse`, including per-repository enrichment and `latest_run.ai_summary`.
- Base: component handles empty `repositories` array.
- Bad: component does `fetch('/api/trending')` and casts response locally.

### 6. Tests Required

- `npm.cmd run build` must pass TypeScript checking.
- UI checks should confirm font size changes apply through the root CSS variable, history records render from typed API data, historical run clicks load via `run_id`, stats render language distribution without category or ranking distributions, and `/market-prices` renders typed gold/silver price cards.
- UI smoke should confirm `/`, `/github-trending`, `/github-trending/settings`, and `/market-prices` render after Vite build is served by FastAPI.

### 7. Wrong vs Correct

#### Wrong

```typescript
const data = await fetch('/api/settings').then((r) => r.json()) as any;
```

#### Correct

```typescript
const settings = await getSettings();
```

## Forbidden Patterns

- Do not use `any` for API payloads.
- Do not duplicate backend response field names in page-local ad hoc types.
- Do not store or display the raw LLM API key after save.
- Do not duplicate refresh history or settings DTO fields inside page-local types.
- Do not reintroduce `category_distribution` or `top_repositories` into `TrendingStatsResponse` unless the backend API contract is intentionally changed again.
