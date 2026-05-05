# Alpaca Astro Center - Implementation Tasks

> **Branching convention:** merge work through **`feature/<short-topic>` branches** and GitHub PRs rather than committing everything directly onto `main`, unless fixing an urgent breakage.

## Phase 1 - Template Adaptation and Cleanup

- [x] Create `docs/` baseline and ensure all new project docs are in English.
- [x] Update project naming strings from chat-template branding to `Alpaca Astro Center`.
- [x] Review `backend/README.md` and mark chat-specific sections for replacement.
- [x] Identify all modules under `backend/app` that implement chat/message logic.
- [x] Remove or deprecate legacy chat API routes from FastAPI router registration.
- [x] Remove chat websocket endpoints that are tied to chat rooms/messages.
- [x] Remove leftover websocket/chat legacy manager abstractions from infra/application core.
- [x] Remove chat-specific Pydantic schemas and DTOs from API layer.
- [x] Remove chat/message command handlers from application logic.
- [x] Remove chat/message query handlers from application logic.
- [x] Remove chat/message domain entities and value objects.
- [x] Remove chat/message domain events and event handlers.
- [x] Remove chat/message repository interfaces from infra ports.
- [x] Remove chat/message Mongo repository adapters.
- [x] Introduce new bounded-context package for telescope domain (`telescope`).
- [x] Create initial `Telescope` domain entity (identity, capabilities, connection state).
- [x] Create initial value objects for coordinates and telescope status snapshots.
- [x] Define domain events for telescope lifecycle transitions (`TelescopeConnectionStateChangedEvent`, `TelescopeTrackingChangedEvent`).
- [x] Define command contracts for telescope control intents (`SlewToIcrsCommand`, `SyncMountToIcrsCommand`, `SetTelescopeTrackingCommand`).
- [x] Define query contracts for telescope status retrieval intents.
- [x] Define `ITelescopeRepository` interface.
- [x] Define `IAlpacaClient` interface as an external port.
- [x] Define `ICoordinateTransformService` interface as a domain-support port.
- [x] Define `IEphemerisService` and `ICatalogResolveService` port stubs (implementations wired later).
- [x] Update DI container registrations in composition root to remove chat dependencies.
- [x] Register placeholder/stub telescope services to validate app startup.
- [x] Ensure app lifespan still initializes Kafka and core dependencies safely.
- [x] Add/adjust health and readiness endpoints for the repurposed backend.
- [x] Run static import checks and remove dead imports after cleanup.
- [x] Ensure tests no longer reference removed chat modules.
- [x] Add migration notes in docs for template-to-telescope transition (`docs/MIGRATION_NOTES.md`).

## Phase 2 - Alpyca and Astropy Integration

- [x] Add required dependencies: `alpyca`, `astropy`, `skyfield`, `astroquery`.
- [x] Verify dependency pinning/version policy in `pyproject.toml`.
- [x] Create infra adapter implementing `IAlpacaClient` with `alpyca` (`AlpycaTelescopeClient` snapshot probe).
- [x] Add Alpaca configuration model (host, port, device number, timeouts).
- [x] Implement lightweight Alpaca connectivity snapshot (pollable discovery path for LAN Alpaca servers).
- [x] Extend telescope status query payload with optional Alpaca snapshot when probing is enabled.
- [x] Implement command handler for slew-to-coordinates flow (Alpyca `SlewToCoordinates`, HTTP `/telescopes/commands/slew-icrs`).
- [x] Implement command handler for sync flow (checks `CanSync`, HTTP `/telescopes/commands/sync-icrs`).
- [x] Implement command handler for tracking on/off (HTTP `/telescopes/commands/tracking`).
- [x] Create `ICoordinateTransformService` implementation using `astropy`.
- [x] Implement RA/Dec to Alt/Az conversion utility with observer location/time inputs (HTTP `/telescopes/coordinates/radec-to-altaz`).
- [x] Add deterministic tests for coordinate transforms with fixed timestamps.
- [x] Create `IEphemerisService` interface for Solar System targets (`domain/ports/ephemeris.py`).
- [x] Add initial `skyfield` implementation for planetary target coordinates (DI-backed `SkyfieldEphemerisService` + `GET /telescopes/ephemeris/icrs`).
- [x] Create target-resolution abstraction for SIMBAD/VizieR lookups (`domain/ports/catalog_resolve.py`).
- [x] Add initial catalog object-name adapter with timeouts (`SesameBackedCatalogResolveService` using `SkyCoord.from_name`, `asyncio.wait_for`; HTTP `/telescopes/catalog/icrs`, env `CATALOG_LOOKUP_ENABLED`).
- [x] Define starter domain telescope/coordinate/ephemeris error types (`AlpacaDriverException`, `CoordinateTransformException`, etc.).
- [x] Ensure telescope command/catalog paths map Alpaca/driver and lookup failures via domain exceptions (`AlpacaDriverException`, `UnresolvedObjectNameException`, etc.) to HTTP statuses in the FastAPI boundary.
- [x] Publish telescope operation events to Kafka from command handlers (topic `telescope-operation-events`, configurable via `TELESCOPE_OPERATION_TOPIC`).
- [x] Define initial Kafka event schema placeholders for model-service interaction.
- [x] Create interface contracts for inference request/result events.
- [x] Add integration tests for Alpaca adapter against mocked endpoints (`tests/integration/test_alpyca_adapter_mocked.py`).
- [x] Add integration tests for Kafka publication from telescope operations (`tests/integration/test_telescope_operation_events_api.py` with mocked broker).
- [x] Document assumptions for hardware-unavailable development mode (`ALPACA_ENABLED` / `CATALOG_LOOKUP_ENABLED` default off for portable stacks — see `backend/README.md` and `backend/.env.example`).
- [x] Add TODO references for Phase 4 MCP tool wiring dependencies (see Phase 4 dependency notes below).

## Notes for Upcoming Phases

- The local model runtime will be a separate FastAPI microservice.
- Main backend and model microservice will communicate through Kafka.
- Model runtime profiles must support NVIDIA, AMD, and CPU-only environments.

## Phase 3 Kickoff Checklist

- [x] Add explicit contract metadata (`schema_version`, `correlation_id`) to Kafka message contracts used by inference and telescope operation events.
- [x] Document topic naming/versioning policy and backward-compatibility rules for future event schema changes (`docs/KAFKA_EVENT_POLICY.md`).
- [x] Define restart-safe processing and idempotency strategy for telescope operation consumers (`docs/KAFKA_EVENT_POLICY.md`, consumer ledger + offset discipline guidance).
- [x] Add idempotent duplicate-guard in model-inference result consumer before Mongo writes (`application/api/lifespan.py`) with unit coverage.

## Phase 4 Dependency Notes (TODO references)

- TODO(P4-MCP-TOOLS): Expose telescope command/query capabilities as MCP tools with explicit capability flags (`supports_slew`, `supports_sync`, `supports_tracking`) to prevent unsafe tool execution paths. [DONE-foundation: capability flags surfaced via `/telescopes/status` + `/telescopes/capabilities`]
- TODO(P4-MCP-AUTH): Define local-network trust/auth strategy for MCP actions that can move hardware (token/session model + audit trail). [DONE-foundation: optional `COMMAND_AUTH_TOKEN` + `X-Command-Token` guard on `/telescopes/commands/*`, command audit writes to operations collection, and audit read endpoint `/telescopes/commands/audit`]
- TODO(P4-MCP-CONTEXT): Wire catalog + ephemeris + live telescope status into MCP context assembly so tool-calling agents can reason over target/object/position state before command dispatch. [DONE-foundation: `/telescopes/context/mcp` aggregates status/capabilities + optional catalog/ephemeris payloads]
