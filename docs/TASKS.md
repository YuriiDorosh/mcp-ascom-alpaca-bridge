# Alpaca Astro Center - Implementation Tasks

## Phase 1 - Template Adaptation and Cleanup

- [x] Create `docs/` baseline and ensure all new project docs are in English.
- [x] Update project naming strings from chat-template branding to `Alpaca Astro Center`.
- [x] Review `backend/README.md` and mark chat-specific sections for replacement.
- [x] Identify all modules under `backend/app` that implement chat/message logic.
- [x] Remove or deprecate legacy chat API routes from FastAPI router registration.
- [x] Remove chat websocket endpoints that are tied to chat rooms/messages.
- [x] Remove chat-specific Pydantic schemas and DTOs from API layer.
- [x] Remove chat/message command handlers from application logic.
- [x] Remove chat/message query handlers from application logic.
- [x] Remove chat/message domain entities and value objects.
- [x] Remove chat/message domain events and event handlers.
- [x] Remove chat/message repository interfaces from infra ports.
- [x] Remove chat/message Mongo repository adapters.
- [x] Introduce new bounded-context package for telescope domain (`telescope`).
- [x] Create initial `Telescope` domain entity (identity, capabilities, connection state).
- [ ] Create initial value objects for coordinates and telescope status snapshots.
- [ ] Define domain events for telescope lifecycle transitions.
- [ ] Define command contracts for telescope control intents.
- [x] Define query contracts for telescope status retrieval intents.
- [x] Define `ITelescopeRepository` interface.
- [ ] Define `IAlpacaClient` interface as an external port.
- [ ] Define `ICoordinateTransformService` interface as a domain-support port.
- [x] Update DI container registrations in composition root to remove chat dependencies.
- [x] Register placeholder/stub telescope services to validate app startup.
- [x] Ensure app lifespan still initializes Kafka and core dependencies safely.
- [x] Add/adjust health and readiness endpoints for the repurposed backend.
- [x] Run static import checks and remove dead imports after cleanup.
- [x] Ensure tests no longer reference removed chat modules.
- [ ] Add migration notes in docs for template-to-telescope transition.

## Phase 2 - Alpyca and Astropy Integration

- [ ] Add required dependencies: `alpyca`, `astropy`, `skyfield`, `astroquery`.
- [ ] Verify dependency pinning/version policy in `pyproject.toml`.
- [ ] Create infra adapter implementing `IAlpacaClient` with `alpyca`.
- [ ] Add Alpaca configuration model (host, port, device number, timeouts).
- [ ] Implement telescope connection/capability discovery use-case.
- [ ] Implement query handler for telescope status via `IAlpacaClient`.
- [ ] Implement command handler for slew-to-coordinates flow.
- [ ] Implement command handler for sync flow (where supported).
- [ ] Implement command handler for tracking on/off.
- [ ] Create `ICoordinateTransformService` implementation using `astropy`.
- [ ] Implement RA/Dec to Alt/Az conversion utility with observer location/time inputs.
- [ ] Add deterministic tests for coordinate transforms with fixed timestamps.
- [ ] Create `IEphemerisService` interface for Solar System targets.
- [ ] Add initial `skyfield` implementation for planetary target coordinates.
- [ ] Create target-resolution abstraction for SIMBAD/VizieR lookups.
- [ ] Add initial `astroquery` adapter with timeout/error handling strategy.
- [ ] Define domain-level error taxonomy for telescope and coordinate failures.
- [ ] Ensure command handlers map adapter errors to domain-safe errors.
- [ ] Publish telescope operation events to Kafka from domain event handlers.
- [x] Define initial Kafka event schema placeholders for model-service interaction.
- [x] Create interface contracts for inference request/result events.
- [ ] Add integration tests for Alpaca adapter against simulator or mocked endpoints.
- [ ] Add integration tests for Kafka publication from telescope operations.
- [ ] Document assumptions for hardware-unavailable development mode.
- [ ] Add TODO references for Phase 4 MCP tool wiring dependencies.

## Notes for Upcoming Phases

- The local model runtime will be a separate FastAPI microservice.
- Main backend and model microservice will communicate through Kafka.
- Model runtime profiles must support NVIDIA, AMD, and CPU-only environments.
