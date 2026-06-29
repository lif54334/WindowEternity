# Error Handling

## Overview

Backend errors must remain visible to the frontend and to refresh history. GitHub HTML, repository detail pages, and LLM providers are external unstable boundaries; failures there should not be hidden as successful empty states.

## Error Types

- `TrendingFetchError` in `services/trending.py`: raised when GitHub Trending HTML cannot be fetched.
- `TrendingParseError` in `services/trending.py`: raised when GitHub Trending HTML cannot be normalized into repository cards.
- `LlmConfigError` in `services/llm.py`: raised when required LLM settings are incomplete.
- `LlmRequestError` in `services/llm.py`: raised when the Chat Completions request or response shape fails.
- FastAPI/Pydantic validation errors: used for invalid request fields such as `since`, `refresh_time_of_day`, and `font_size_percent`.

## Error Handling Patterns

- `services/refresh.py` owns refresh status transitions. Routes should call the service and return typed response schemas instead of catching and reshaping refresh failures locally.
- A failed GitHub fetch or parser break creates a `refresh_runs` row with `status="failed"` and `error_message`.
- Missing LLM config does not fail the raw repository refresh. It marks `refresh_runs.ai_summary_status` and per-repository analysis rows as `config_error`.
- LLM request failures keep raw repository data visible and write the provider/request error to `ai_summary_error` and per-repository `error_message`.
- Repository detail-page fetch failures are non-fatal. Keep the Trending card data and leave detail fields empty.
- Scheduled refresh jobs log unexpected exceptions, but the refresh service should still persist user-visible status whenever it can create a run.

## API Error Responses

- Use FastAPI/Pydantic validation for field-level request validation.
- Use response models from `schemas.py` for normal responses.
- For refresh/analyze workflows, prefer persisted status fields over ad hoc HTTP error bodies so history remains queryable.
- Settings responses must never return raw `llm_api_key`.

## Common Mistakes

- Do not return a successful empty Trending list when the parser found no cards; that usually means GitHub markup changed.
- Do not swallow LLM errors without writing `ai_summary_error` or `analysis_results.error_message`.
- Do not let route modules duplicate refresh transaction handling.
- Do not log or return API keys.
