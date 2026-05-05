# Alpaca Astro Center Backend

Local-first FastAPI backend for ASCOM Alpaca telescope control with DDD architecture, Kafka messaging, and MongoDB persistence.

## Git branching

Prefer short-lived **`feature/<topic>` branches** merged into `main` via GitHub pull requests instead of committing directly on `main`, so telescope and infra changes stay reviewable before release.

## Requirements

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [GNU Make](https://www.gnu.org/software/make/)

## How to Use

1. **Clone the repository:**

   ```bash
   git clone https://github.com/YuriiDorosh/mcp-ascom-alpaca-bridge.git
   cd mcp-ascom-alpaca-bridge/backend
   cp .env.example .env

2. Adjust `.env` values for your environment if needed.


### Implemented Commands

- `make app-dev` - build and start backend + Kafka stack in detached mode
- `make app-dev-logs` - stream logs for the development app compose file
- `make storages` - start MongoDB services
- `make ui` - start Mongo Express UI
- `make down-dev` - stop app-dev + Kafka stack
- `make down` - stop all compose stacks
- `make purge` - stop infra stacks and remove volumes
- `make shell` - open interactive shell in `main-app` container
- `make test` / `make test-all` - run full pytest suite inside running `main-app`
- `make test-unit` - run unit tests only (`tests/unit`)
- `make test-integration` - run integration tests only (`tests/integration`)
- `make test-local` - run full suite in ephemeral Python 3.12 container (no running app container needed)
- `make test-unit-local` - run unit tests in ephemeral Python 3.12 container
- `make test-integration-local` - run integration tests in ephemeral Python 3.12 container

## Recommended Local Startup Order

```bash
make storages
make app-dev
```

Then verify:

- API docs: <http://localhost:8000/api/docs>
- Kafka UI: <http://localhost:8090>
- Telescope status JSON: `GET http://localhost:8000/telescopes/status`
- Telescope capability flags (MCP-safe gating surface): `GET http://localhost:8000/telescopes/capabilities`
- RA/Dec → Alt/Az (ICRS → local horizontal): `POST http://localhost:8000/telescopes/coordinates/radec-to-altaz`
- slew / sync / tracking (Alpaca HTTP; requires `ALPACA_ENABLED`): `POST /telescopes/commands/slew-icrs`, `POST /telescopes/commands/sync-icrs`, `POST /telescopes/commands/tracking`
- optional command auth guard: set `COMMAND_AUTH_TOKEN` and send `X-Command-Token` header for `/telescopes/commands/*`
- optional object name → ICRS (Sesame/CDS via Astropy): `GET /telescopes/catalog/icrs` (requires `CATALOG_LOOKUP_ENABLED`)
- optional Solar System body → ICRS (Skyfield): `GET /telescopes/ephemeris/icrs` (requires `EPHEMERIS_ENABLED`)
- telescope control ops are published to Kafka topic `TELESCOPE_OPERATION_TOPIC` (default `telescope-operation-events`)
- Kafka contracts include `schema_version` and `correlation_id` fields for event evolution and traceability.
- Mongo Express (if `make ui` was started): <http://localhost:28081>

## Kafka Startup Troubleshooting

If `make app-dev` fails with `container ... kafka ... exited (1)`:

1. Check Kafka logs:
   ```bash
   docker compose -f docker_compose/app.dev.yaml -f docker_compose/kafka.yaml --env-file .env logs kafka
   ```
2. Ensure Docker daemon is running and healthy.
3. Ensure ports `29092`, `22181`, and `8090` are free.
4. Restart stack:
   ```bash
   make down-dev
   make app-dev
   ```

## Kafka Contracts and Consumer Safety

- Event contract and versioning policy: `docs/KAFKA_EVENT_POLICY.md`
- Includes topic naming conventions, schema evolution rules, and restart-safe/idempotent consumer guidance.
- Model inference result consumer now skips exact duplicate payloads (same status/output/error/finished_at per `request_id`) before Mongo write.

## Testing Guide

Current backend test layout:

- `tests/unit` - deterministic logic tests (domain events, coordinate math, handlers).
- `tests/integration` - API/adapter integration tests with mocked Alpaca/broker dependencies (hardware-free).

Recommended flows:

1. If `main-app` is running (`make app-dev`):
   - `make test-unit`
   - `make test-integration`
   - `make test-all`
2. If app container is not running (CI-like local run):
   - `make test-unit-local`
   - `make test-integration-local`
   - `make test-local`

The project is intentionally testable without telescope hardware while `ALPACA_ENABLED=false`.
