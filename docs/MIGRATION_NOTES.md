# Template to Telescope Migration Notes

This note summarizes how the original chat-oriented template was reshaped into the telescope-control backend.

## Scope of Migration

- Removed chat/message domain, API endpoints, schemas, repositories, and related tests.
- Kept DDD boundaries, mediator pipeline, manual DI (`punq`), Kafka broker abstraction, and Mongo integration patterns.
- Introduced a telescope-first domain with:
  - status query and optional live Alpaca probe,
  - command endpoints for slew/sync/tracking,
  - coordinate conversions (Astropy),
  - catalog resolution and ephemeris slices,
  - operation-event publication to Kafka.

## Naming and Runtime

- Backend package name changed to `alpaca-astro-center-backend`.
- Compose files aligned with current make targets and modern Compose format (no top-level `version`).
- `.env.example` now includes optional hardware/network features:
  - `ALPACA_*` for telescope control,
  - `CATALOG_*` for Sesame/CDS name lookups,
  - `EPHEMERIS_*` for Skyfield body positions.

## Safe Development Without Hardware

- Default configuration is hardware-off (`ALPACA_ENABLED=false`), so local development and CI remain deterministic.
- Integration tests for Alpaca adapter and operation-event publication run against mocked drivers/brokers.
- Real telescope integration can be postponed until command semantics and event flows are stable.

## Follow-up Migration Work

- Domain lifecycle events are now defined for telescope state/tracking transitions; downstream event handlers can map them to broker/websocket outputs.
- Phase 4 MCP tool wiring is tracked via TODO references in `docs/TASKS.md`.
