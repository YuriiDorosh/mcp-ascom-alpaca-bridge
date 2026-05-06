---
description: DDD layers, mediator, DI, ports/adapters, API and Kafka boundaries for backend and model-service
globs: "**/app/**/*.py"
alwaysApply: false
---

# Architecture

## Core Pattern

- **Domain-Driven Design (DDD)** with **CQRS-style** split: **commands** (writes) vs **queries** (reads).
- **Mediator** dispatches commands/queries to handlers (`logic/mediator/`, `logic/commands/`, `logic/queries/`).
- **Manual dependency injection** via **Punq** in **`logic/init.py`** (composition root) — register concrete adapters explicitly; no hidden service locators.

## Backend Package Layout (`backend/app/`)

| Area | Responsibility |
|------|----------------|
| `domain/` | Entities, value objects, domain events, **ports** (`domain/ports/*.py`) — interfaces only |
| `logic/` | Command/query handlers, mediator registration, **init_container** wiring |
| `infra/` | Adapters: Mongo repos, `KafkaMessageBroker`, Alpaca (`alpyca`), Astropy, Skyfield, Astroquery |
| `application/` | FastAPI routers, Pydantic API schemas, lifespan (Kafka consumers) |
| `settings/` | `Config` (Pydantic Settings) |

## Ports & Adapters

- **External I/O** belongs behind **ports** in `domain/ports/`: e.g. `IAlpacaTelescopeClient`, `ICoordinateTransformService`, `ICatalogResolveService`, `IEphemerisService`, `BaseMessageBroker`, repository bases.
- **Infra** implements those ports; **handlers** depend on ports/types registered in DI, not on concrete classes.

## API Layer Rules

- **FastAPI** routes stay thin: parse/validate → **mediator.handle_command / handle_query** → map **domain exceptions** to HTTP errors (4xx/5xx) consistently.
- Pydantic schemas live in `application/api/telescope/schemas.py` (and siblings); keep **HTTP DTOs** separate from **domain** types unless intentionally shared.

## Kafka

- Contracts in `infra/message_brokers/contracts.py` — include **`schema_version`** and **`correlation_id`** on events (see `docs/KAFKA_EVENT_POLICY.md`).
- Producers: command handlers and model enqueue paths; consumers: `application/api/lifespan.py` (e.g. model inference results) — maintain **idempotent** writes where redelivery is possible.

## Model Service (`model-service/app/`)

- Smaller surface: **`Config`**, **`KafkaInferenceWorker`**, **`contracts`** aligned with backend inference payloads, **`runtime`** (mock today).
- Not a second domain layer — keep it as **inference worker + HTTP health/metadata**.

## Testing Strategy

- **Unit**: domain, pure transforms, handlers with fakes.
- **Integration**: FastAPI `TestClient` with **mediator/DI patched** or mocked brokers — **no real telescope** required when `ALPACA_ENABLED=false`.

## Invariants (Do Not Break)

- Preserve **command/query separation** and mediator dispatch.
- Preserve **explicit DI** in `logic/init.py`.
- Keep **telescope control** and **model inference** concerns separated (backend vs `model-service`).
- Prefer **additive** Kafka contract changes within the same major `schema_version`; follow `docs/KAFKA_EVENT_POLICY.md` for breaking changes.

## Docs Map

- **`docs/PROJECT_CONTEXT.md`** — mission, terminology, stack, invariants.
- **`docs/PLAN.md`** — phased roadmap (MCP, model service, frontend).
- **`docs/TASKS.md`** — granular checklist + branching note.
- **`docs/MIGRATION_NOTES.md`** — template → telescope migration context.
