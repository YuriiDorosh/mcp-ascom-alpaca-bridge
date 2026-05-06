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
- `make app-dev-with-model` - build and start backend + Kafka + local model-service in detached mode
- `make app-dev-logs` - stream logs for the development app compose file
- `make app-dev-with-model-logs` - stream logs for backend + Kafka + model-service stack
- `make storages` - start MongoDB services
- `make ui` - start Mongo Express UI
- `make down-dev` - stop app-dev + Kafka stack
- `make down-dev-with-model` - stop backend + Kafka + model-service stack
- `make down` - stop all compose stacks
- `make purge` - stop infra stacks and remove volumes
- `make shell` - open interactive shell in `main-app` container
- `make test` / `make test-all` - run full pytest suite inside running `main-app`
- `make test-unit` - run unit tests only (`tests/unit`)
- `make test-integration` - run integration tests only (`tests/integration`)
- `make test-local` - run full suite in ephemeral Python 3.12 container (no running app container needed)
- `make test-unit-local` - run unit tests in ephemeral Python 3.12 container
- `make test-integration-local` - run integration tests in ephemeral Python 3.12 container
- `make postman-smoke-local` - run Postman smoke collection via Newman (Docker, host network)
- `make postman-smoke-up` - start backend + Kafka + model-service and run Newman smoke checks
- `make postman-smoke-up-clean` - same as above, then stop stack (`down-dev-with-model`)

## Recommended Local Startup Order

```bash
make storages
make app-dev-with-model
```

Then verify:

- API docs: <http://localhost:8000/api/docs>
- Kafka UI: <http://localhost:8090>
- Model service health: `GET http://localhost:8010/health`
- Telescope status JSON: `GET http://localhost:8000/telescopes/status`
- Telescope capability flags (MCP-safe gating surface): `GET http://localhost:8000/telescopes/capabilities`
- MCP tool manifest (tool definitions + capability/auth requirements): `GET http://localhost:8000/telescopes/tools/mcp-manifest`
  - now includes both telescope tools and model inference tools for MCP planning.
- Effective MCP manifest (runtime-ready tool availability with `enabled` flags): `GET http://localhost:8000/telescopes/tools/mcp-manifest/effective`
- MCP planning guide (recommended inference tool orchestration + timeout policy): `GET http://localhost:8000/telescopes/tools/mcp-planning-guide`
- MCP bootstrap bundle (manifest + planning guide in one call): `GET http://localhost:8000/telescopes/tools/mcp-bootstrap`
  - includes static `manifest`, runtime `effective_manifest`, and `hardware_readiness` for one-call agent initialization.
- MCP execution plan (runtime-safe step sequence with capability-gated command tools): `GET http://localhost:8000/telescopes/tools/mcp-execution-plan`
  - supports `?mode=async|sync` to switch between polling flow and single-call inference flow.
  - supports `?include_disabled_commands=false` to return only currently runnable telescope command steps.
  - response includes `applied_filters` to confirm the active filtering mode used to build the plan.
  - response includes `stats.baseline_steps` and `stats.returned_steps` to make filtering impact explicit.
- Hardware readiness trigger (`Seestar` not required yet + next real-device task): `GET http://localhost:8000/telescopes/hardware/readiness`
- MCP-ready context snapshot (status + capabilities + optional catalog/ephemeris): `GET http://localhost:8000/telescopes/context/mcp`
- RA/Dec → Alt/Az (ICRS → local horizontal): `POST http://localhost:8000/telescopes/coordinates/radec-to-altaz`
- slew / sync / tracking (Alpaca HTTP; requires `ALPACA_ENABLED`): `POST /telescopes/commands/slew-icrs`, `POST /telescopes/commands/sync-icrs`, `POST /telescopes/commands/tracking`
- optional command auth guard: set `COMMAND_AUTH_TOKEN` and send `X-Command-Token` header for `/telescopes/commands/*`
- telescope hardware commands write command-audit records into `MONGODB_OPERATION_COLLECTION` for local traceability
- command-audit read API with optional filters: `GET /telescopes/commands/audit?limit=50&operation=slew-icrs&status=ok&source=main-backend`
- optional object name → ICRS (Sesame/CDS via Astropy): `GET /telescopes/catalog/icrs` (requires `CATALOG_LOOKUP_ENABLED`)
- optional Solar System body → ICRS (Skyfield): `GET /telescopes/ephemeris/icrs` (requires `EPHEMERIS_ENABLED`)
- inference result wait endpoint (long-poll with timeout): `GET /telescopes/model/inference/{request_id}/wait?timeout_seconds=15&poll_interval_seconds=0.5`
- inference enqueue-and-wait endpoint (single call enqueue + wait): `POST /telescopes/model/inference/enqueue-and-wait?timeout_seconds=15&poll_interval_seconds=0.5`
- inference status endpoint (no 404 while pending): `GET /telescopes/model/inference/{request_id}/status`
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
- Local model-service compose overlay: `docker_compose/model-service.yaml` (mock runtime now; heavy GPU/CPU model profiles follow in next steps).

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

## Postman Starter Kit

- Import-ready templates are available in `backend/postman/`:
  - `alpaca-astro-center.postman_collection.json`
  - `alpaca-astro-center.smoke.postman_collection.json`
  - `alpaca-astro-center.local.postman_environment.json`
- See `backend/postman/README.md` for quick-start and variable usage.
