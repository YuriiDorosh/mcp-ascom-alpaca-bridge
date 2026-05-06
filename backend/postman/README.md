# Postman Starter Kit

This folder provides a ready-to-import Postman setup for Alpaca Astro Center backend APIs.

## Files

- `alpaca-astro-center.postman_collection.json` - request collection with grouped endpoints.
- `alpaca-astro-center.local.postman_environment.json` - local environment variables (`base_url`, tokens, and IDs).

## Quick Start

1. Start backend stack (recommended):
   - `cd backend`
   - `make app-dev-with-model`
2. Open Postman and import:
   - collection JSON
   - environment JSON
3. Select the imported environment.
4. (Optional) set `command_token` if your `COMMAND_AUTH_TOKEN` is enabled.
5. Run requests from top to bottom:
   - `Model / Enqueue Inference` first (stores `request_id` automatically),
   - then use `request_id`-based status/result/wait endpoints.

## Notes

- Command endpoints (`/telescopes/commands/*`) already include `X-Command-Token: {{command_token}}`.
- If command auth is disabled, leave `command_token` empty.
- This starter kit is designed for local-first development and integration testing.
