# Postman Starter Kit

This folder provides a ready-to-import Postman setup for Alpaca Astro Center backend APIs.

## Files

- `alpaca-astro-center.postman_collection.json` - request collection with grouped endpoints.
- `alpaca-astro-center.smoke.postman_collection.json` - ordered smoke-run collection with lightweight assertions.
- `alpaca-astro-center.local.postman_environment.json` - local environment variables (`base_url`, tokens, and IDs).
- The collections include MCP discovery endpoints: `mcp-manifest`, `mcp-planning-guide`, and `mcp-bootstrap`.

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
6. For quick stack sanity checks, run the dedicated smoke collection:
   - `alpaca-astro-center.smoke.postman_collection.json`
   - use Collection Runner in Postman (all requests are pre-ordered and include basic 200-status assertions).
7. CLI alternative (without opening Postman UI):
   - `cd backend`
   - `make postman-smoke-local`
   - optional base URL override: `BASE_URL=http://127.0.0.1:8000 make postman-smoke-local`
8. One-command stack bring-up + smoke run:
   - `make postman-smoke-up` (keeps stack running)
   - `make postman-smoke-up-clean` (runs smoke and tears stack down)

## Notes

- Command endpoints (`/telescopes/commands/*`) already include `X-Command-Token: {{command_token}}`.
- If command auth is disabled, leave `command_token` empty.
- This starter kit is designed for local-first development and integration testing.
