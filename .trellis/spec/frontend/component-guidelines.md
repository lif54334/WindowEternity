# Component Guidelines

## Overview

Components are plain React function components. The current app favors page-level composition with small local helper components inside the page file when those helpers are not reused elsewhere.

## Component Structure

- Export one default page component per page file.
- Keep page-local helpers below the page component when they are only used by that page, as in `Metric`, `HistoryRail`, and `RepositoryItem`.
- Keep route navigation explicit through typed callback props until a router library is introduced.
- Keep API side effects in page-level async handlers and `useEffect`; presentational helpers should receive already-shaped data.

## Props Conventions

- Define explicit `interface` props for exported components.
- Inline prop object types are acceptable for small page-local helpers.
- Reuse exported API DTOs from `src/api/client.ts` instead of redefining repository, settings, stats, or history shapes in component files.

## Styling Patterns

- Styling is centralized in `src/styles.css` using semantic class names.
- Keep cards and panels at 8px border radius, matching the existing UI.
- Use `--app-font-scale` for global font-size changes; do not hardcode alternate page-level font scaling.
- Prefer responsive CSS grids and flex wrapping for toolbar, metrics, repository cards, settings form, and history rail.

## Accessibility

- Preserve route-level semantic containers: `main`, `section`, `header`, `aside`, and `nav` where already used.
- Keep `aria-label` on navigation, filter toolbar, history rail, topic rows, and statistics sections when labels are not otherwise clear.
- Use `aria-live`/`role="status"` for long-running refresh overlays.
- Buttons that trigger async work must expose disabled/busy states.

## Common Mistakes

- Do not put portal homepage content inside the GitHub Trending feature shell.
- Do not duplicate repository/stat/history card types in component files.
- Do not fetch raw endpoints directly from components; call `src/api/client.ts` functions.
- Do not display or retain the raw LLM API key after save.
