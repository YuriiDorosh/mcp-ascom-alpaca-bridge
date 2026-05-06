# Alpaca Astro Center - Project Context

## Project Mission

Alpaca Astro Center is a local, AI-powered backend platform for controlling ASCOM Alpaca-compatible telescopes.  
The project repurposes an existing FastAPI + Kafka + DDD template into a telescope control platform that users can self-host on their own machines.

Primary goal:
- Replace closed telescope control experiences (such as Seestar app workflows) with an open, extensible, local-first backend.

Core operating model:
- User clones the repository.
- User starts services with Docker.
- The host machine and telescope must be on the same local network.
- The backend communicates with the telescope through the ASCOM Alpaca HTTP protocol.

## Product Scope (Current)

- Backend-first architecture.
- API and domain foundations for telescope operations.
- Event-driven integration between main backend and a dedicated local model microservice.
- Frontend integration planned later (React).

## Technology Stack

### Core Backend
- FastAPI
- Uvicorn
- Pydantic

### Persistence
- MongoDB
- `motor` for async MongoDB access

### Messaging
- Kafka
- `aiokafka` for async producer/consumer flows

### Astronomy and Telescope Libraries
- `alpyca` for ASCOM Alpaca REST communication
- `astropy` for coordinate transformation math
- `skyfield` for Solar System object positions
- `astroquery` for resolving targets from SIMBAD/VizieR

### AI and MCP Layer
- Official Python MCP SDK
- Local LLM runtime (user-selected profile)
- Main backend acts as MCP server and exposes telescope control tools

## Local AI Model Microservice Concept

The local model runtime is a separate FastAPI microservice. It is not embedded directly into the main backend process.
Phase 4 foundation now includes a dedicated `model-service/` skeleton with Kafka request/result wiring and a deterministic mock runtime.

### Why separate service
- Isolates model runtime dependencies from telescope control core.
- Supports different hardware profiles without coupling to main API lifecycle.
- Keeps DDD domain boundaries clean in the main backend.

### Integration pattern
- Main backend and model service communicate asynchronously via Kafka events/topics.
- Main backend owns telescope domain state and persistence (MongoDB).
- Model service focuses on inference/orchestration responses for MCP tool workflows.

### Hardware/runtime profiles
- NVIDIA profile
- AMD profile
- CPU-only profile

Runtime profile selection must be documented for users with resource guidance:
- VRAM/RAM requirements
- expected performance tier
- appropriate `make` command / compose profile

## Domain Dictionary

### RA/Dec (Right Ascension / Declination)
Equatorial coordinate system used to describe fixed sky positions relative to the celestial sphere.  
Similar to longitude/latitude in space, but projected on the celestial equator.

### Alt/Az (Altitude / Azimuth)
Observer-based horizontal coordinate system:
- Altitude: angle above horizon
- Azimuth: compass direction around horizon

Telescope mounts often require Alt/Az-aware conversion from catalog RA/Dec for real-world pointing.

### ASCOM Alpaca API
A network REST protocol standard for astronomical device control (telescopes, focusers, cameras, etc.).  
In this project, Alpaca endpoints are used to send movement, state, and capability commands to telescope hardware.

### MCP (Model Context Protocol)
A protocol for exposing structured tools to LLMs.  
In this project, the backend acts as an MCP server to provide safe telescope-control tools to a local model runtime.

## Architecture Standards

## DDD Layering
- `domain`: entities, value objects, domain events, invariants
- `logic`/application layer: commands, queries, handlers, use-case orchestration
- `infra`: adapters (Mongo repositories, Kafka broker adapters, external clients)
- `application` API layer: FastAPI routes, websocket endpoints, lifecycle wiring

### CQRS + Mediator
- Commands handle write-side intent.
- Queries handle read-side retrieval.
- Mediator dispatches commands, queries, and events to handlers.

### Manual Dependency Injection
- Composition root registers concrete implementations explicitly.
- Dependencies are wired at startup, avoiding hidden global state.

### Domain Events via BaseEntity
- Domain entities emit events from state transitions.
- Events enable decoupled integration workflows (Kafka publication, websocket notifications, downstream processing).

## Architecture Invariants

The following must remain stable during refactor from chat template to telescope platform:
- Preserve DDD boundaries and clear domain ownership.
- Preserve command/query separation and mediator dispatch model.
- Preserve explicit DI registration patterns.
- Keep external dependencies behind interfaces/ports.
- Keep telescope control local-first and network-safe.
- Keep model inference concerns isolated in the dedicated microservice.

## Near-Term Refactor Direction

- Remove legacy chat/message domain logic from `backend/app`.
- Introduce telescope-focused bounded contexts and interfaces.
- Define Kafka contracts between main backend and model microservice.
- Keep MongoDB ownership in main backend domain services.

## Future Context Expansion (v2.0+)

After frontend delivery and stabilization, weather-awareness can be added to MCP context assembly so AI tool-calling can consider local observing conditions.

Potential providers:
- OpenWeather
- Other weather APIs or local observatory weather feeds

Potential MCP context fields:
- cloud cover
- wind speed / gusts
- humidity
- visibility
- precipitation probability

Intended outcome:
- safer and more adaptive telescope-control suggestions from AI agents (especially for movement and session planning under uncertain weather).
