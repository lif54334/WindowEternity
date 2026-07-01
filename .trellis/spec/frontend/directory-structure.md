# Directory Structure

## Overview

The frontend is a single React/Vite app under `frontend/`. It uses a small hand-rolled route shell in `src/App.tsx`, page components under `src/pages`, and one typed API boundary in `src/api/client.ts`.

## Directory Layout

```text
frontend/
  package.json
  vite.config.ts            # Vite dev server and /api proxy
  tsconfig.json             # strict TypeScript project config
  src/
    main.tsx                # React root mount
    App.tsx                 # route shell, topbar, font-size bootstrap
    styles.css              # shared CSS for portal and module UI
    api/
      client.ts             # DTO interfaces, ApiError, fetch wrappers
    pages/
      HomePage.tsx          # standalone portal launcher
      GitHubTrendingPage.tsx# dashboard, filters, history, stats, repository cards
      MarketPricesPage.tsx  # gold/silver CNY market price display
      SettingsPage.tsx      # scheduler, defaults, font-size, LLM settings
```

## Module Organization

- `App.tsx` owns route normalization and top-level layout selection.
- `HomePage.tsx` is standalone portal content and must not depend on the feature-shell/sidebar layout.
- GitHub Trending feature pages live in `pages/` until the module grows enough to justify a feature folder.
- Market price display lives in `pages/MarketPricesPage.tsx` and consumes only `getMarketPrices()` from the typed API client.
- API contracts live only in `src/api/client.ts`; page files import DTOs and client functions from there.
- Shared visual rules live in `src/styles.css`; do not create page-specific CSS files until repeated conflicts justify splitting.

## Naming Conventions

- React component files use PascalCase.
- API client functions use verb-first names such as `getSettings`, `refreshTrending`, and `getRefreshHistory`.
- DTO interfaces mirror backend response/request schema names where practical: `SettingsResponse`, `TrendingResponse`, `RefreshRunResponse`.
- Route string unions can stay local while there is no router library.

## Examples

- `src/api/client.ts` is the source of truth for frontend API payload types.
- `src/pages/GitHubTrendingPage.tsx` demonstrates page-local server state, refresh/analyze actions, history rendering, and statistics rendering.
- `src/App.tsx` demonstrates the current route shell and root font-size application.
