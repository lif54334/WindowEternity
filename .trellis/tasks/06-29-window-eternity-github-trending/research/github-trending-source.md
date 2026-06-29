# GitHub Trending source notes

Source checked: https://github.com/trending
Checked on: 2026-06-29

## Observations

- The GitHub Trending page presents a Trending repositories view with the description "See what the GitHub community is most excited about today."
- The page includes separate Repositories and Developers navigation.
- The page includes a Spoken Language filter.
- The page includes a programming Language filter.
- The first-version scraper should treat GitHub Trending HTML as an external, unstable source and isolate parsing logic behind a backend service boundary.

## Planning impact

- First-version product scope should explicitly decide which filters are required: time period, programming language, spoken language, or only default current trending.
- The UI/API contract should expose the selected scope so saved snapshots can be traced back to their GitHub Trending query.
