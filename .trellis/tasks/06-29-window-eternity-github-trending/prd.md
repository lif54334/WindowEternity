# Window of Eternity project portal and GitHub Trending module

## Goal

Build the first usable version of "Window of Eternity" / "新世界的窗口": a locally deployed project portal served on port 3030, with one initial feature module for GitHub Trending collection, display, statistics, configuration, and LLM-assisted repository analysis.

The product is intended to become a collection of feature modules reachable under paths such as `http://127.0.0.1:3030/<module>`. The homepage should act as a launcher for current and future modules.

## Confirmed Facts

- The repository is effectively a new application. Aside from Trellis files, `.gitignore`, and `AGENTS.md`, there is no existing app code.
- The project uses Trellis, so implementation must wait until planning artifacts are reviewed and the task is started.
- Backend implementation must use Python. The backend stack will be FastAPI + SQLAlchemy + APScheduler + httpx + BeautifulSoup.
- The unified deployment target is Docker.
- Runtime port target is `3030`.
- Initial feature module: GitHub Trending collection from `https://github.com/trending`.
- Current source review confirms GitHub Trending exposes repository/developer views plus spoken-language and programming-language filters.
- The first version is a local single-user tool: no login, multi-user permission model, or public-network access protection is required in this task.
- The UI should be a separate React + Vite + TypeScript frontend app suitable for future expansion.
- The backend remains Python and exposes APIs consumed by the frontend.
- The first version will use SQLite for local persistence of configuration, trending snapshots, repository records, LLM analysis results, and refresh status.
- The first version will target OpenAI-compatible Chat Completions APIs, configured with `base_url`, `api_key`, and `model`.
- LLM analysis should be used to understand and summarize repositories for display.
- The intended analysis flow is: fetch the current GitHub Trending list, then fetch each visible repository detail page for richer repository introduction information, then submit the whole refreshed repository set to the configured AI in one analysis request.
- The UI should expose when a refreshed list and its AI analysis were produced.
- Analysis/refresh history should remain queryable and should be visible from the GitHub Trending module when history exists.
- Users need UI-level font size adjustment for readability.
- Users need an editable AI prompt field so they can add custom analysis instructions.
- Scheduled refresh should run at a configured time of day instead of a repeating minute interval.

## Requirements

### R1. Project Portal

- Provide a standalone homepage for "Window of Eternity" that introduces the project as a module collection and links to feature modules. The homepage must not use the feature-module sidebar/navigation layout.
- Include the initial GitHub Trending module as a navigable entry. Clicking the entry should enter the GitHub Trending feature interface, where display and configuration are available inside that feature.
- Keep routing compatible with future modules under `/XXX` style paths.

### R2. GitHub Trending Collection

- Fetch trending repository entries from GitHub Trending.
- Support `daily`, `weekly`, and `monthly` time ranges, defaulting to `daily`.
- Support programming-language filtering, defaulting to all languages.
- Exclude GitHub Trending Developers and Spoken Language filtering from the MVP.
- Capture enough data for useful display: repository owner/name, URL, description, primary language when available, stars/forks/today stars when available, and any visible metadata the source exposes.
- Support manual refresh from the UI.
- Support scheduled refresh based on configured update frequency.
- Settings UI must provide scheduled refresh controls.
- Preserve the latest fetched results so the UI can load without immediately scraping GitHub.

### R3. LLM Repository Analysis

- Allow configuring an LLM-compatible API endpoint, API key, model name, and related request settings needed by the backend.
- Use the configured LLM to generate human-readable analysis for trending repositories.
- Use the configured LLM to generate both per-repository Chinese introductions and an overall Chinese summary for the full refreshed trending set.
- LLM analysis must run automatically after scheduled and manual GitHub Trending refreshes when valid LLM configuration exists.
- Every refresh must re-analyze all repositories in the refreshed result set, not only new or changed repositories.
- Each refresh should process the visible GitHub Trending result set up to a configurable `max_repositories_per_refresh`, defaulting to `25`.
- Show LLM analysis alongside raw repository data.
- Show each repository's detail-page introduction information, when available, alongside the Trending card metadata and per-repository AI introduction.
- Show the AI summary for the full refreshed trending set.
- Handle missing or invalid LLM configuration visibly instead of silently pretending analysis succeeded.
- Keep manual LLM re-analysis available from the UI for retrying failures.
- Cached historical analysis may be retained for audit/history, but the current refreshed list should receive fresh analysis each refresh.
- Display the analysis timestamp for the current list and per-repository analysis when available.
- Show refresh/analysis history in the GitHub Trending module, preferably in a left-side history rail when history exists.

### R4. Statistics And Visualization

- Provide a statistics view or section for the current trending dataset.
- At minimum, summarize repository count, language distribution, star-related rankings, and notable repository categories or themes when analysis is available.

### R5. Configuration UI

- Provide a configuration screen for scheduled refresh time, maximum repositories per refresh, UI font size, manual refresh behavior visibility, LLM settings, and editable AI prompt instructions.
- Persist configuration locally for the deployed app.
- Avoid exposing secrets unnecessarily in normal display views.

### R6. Docker Deployment

- Provide a Docker-based local deployment path that serves the app on `http://127.0.0.1:3030/`.
- Backend must be Python-based.
- The frontend should be built as a separate modern frontend app and served together with the backend/runtime deployment on port `3030`.

## Acceptance Criteria

- [ ] Visiting `http://127.0.0.1:3030/` shows the project homepage with a link/card for the GitHub Trending module.
- [ ] Visiting the GitHub Trending route shows fetched trending repositories with raw metadata and descriptions.
- [ ] Each refreshed repository attempts to include richer detail-page information such as repository page description, topics, or README excerpt.
- [ ] The user can select `daily`, `weekly`, or `monthly` and optionally filter by programming language.
- [ ] The user can trigger a manual refresh from the UI and see success/failure state.
- [ ] The user sees an in-progress/waiting state during manual refresh.
- [ ] The backend can run a scheduled refresh at the configured time of day.
- [ ] Each refresh re-analyzes the refreshed repository list with the configured LLM when valid LLM settings exist.
- [ ] The configuration page can save scheduled refresh time, max repositories per refresh, UI font size, LLM API settings, and custom AI prompt text.
- [ ] The LLM analysis flow reports a visible configuration or request error when analysis cannot run.
- [ ] The statistics section summarizes the current dataset by language and popularity signals.
- [ ] The display includes a full-list AI summary for the current refreshed GitHub Trending result set when LLM analysis succeeds.
- [ ] The display shows refresh/analysis timestamps and exposes historical refresh runs when available.
- [ ] Docker deployment exposes the application on port `3030`.
- [ ] The implementation includes basic verification commands for backend and frontend behavior.

## Out Of Scope

- User accounts, login, role permissions, and public-network access protection.
- GitHub Trending Developers.
- GitHub Trending Spoken Language filtering.
- Fetching more than the current visible GitHub Trending result set in the MVP.

## Notes

- This is a complex cross-layer task. It must have `design.md` and `implement.md` before `task.py start`.
- Relevant thinking guide: `.trellis/spec/guides/cross-layer-thinking-guide.md`.
- Backend/frontend guideline files exist but are still template-level and do not impose a concrete framework.
- Source reviewed during planning: `https://github.com/trending`.



