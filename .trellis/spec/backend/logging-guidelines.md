# Logging Guidelines

## Overview

The backend currently uses the standard Python `logging` module. Logging is minimal and should support operational diagnosis without leaking secrets.

## Log Levels

- `debug`: detailed development-only diagnostics, especially around parser or API response shape checks.
- `info`: successful lifecycle events only when they help operations, such as scheduler startup or job replacement.
- `warning`: recoverable external-boundary problems where the user-visible status is also persisted.
- `error` / `exception`: unexpected failures, especially scheduled refresh failures that escape normal refresh status handling.

## Structured Logging

There is no structured logging framework yet. Keep messages stable and include useful identifiers such as refresh run id, `since`, and language when available. Do not add broad print statements.

## What To Log

- Scheduled refresh exceptions with stack trace via `logger.exception`.
- Parser/fetch failures when the failure is not already obvious from the persisted refresh run.
- LLM request failures at the boundary, without request headers or API keys.
- Scheduler job replacement decisions when debugging scheduling behavior.

## What Not To Log

- `llm_api_key` or Authorization headers.
- Full LLM prompts or full LLM responses by default; they can contain user-provided instructions and repository text.
- Full GitHub HTML pages.
- SQLite database URLs if they could include credentials in a future non-SQLite configuration.
