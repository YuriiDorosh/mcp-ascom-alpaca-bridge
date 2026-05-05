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
- `make test` - run pytest inside `main-app` container

## Recommended Local Startup Order

```bash
make storages
make app-dev
```

Then verify:

- API docs: <http://localhost:8000/api/docs>
- Kafka UI: <http://localhost:8090>
- Telescope status JSON: `GET http://localhost:8000/telescopes/status`
- RA/Dec → Alt/Az (ICRS → local horizontal): `POST http://localhost:8000/telescopes/coordinates/radec-to-altaz`
- slew / sync / tracking (Alpaca HTTP; requires `ALPACA_ENABLED`): `POST /telescopes/commands/slew-icrs`, `POST /telescopes/commands/sync-icrs`, `POST /telescopes/commands/tracking`
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
