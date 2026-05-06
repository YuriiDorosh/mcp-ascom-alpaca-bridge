---
description: MongoDB collections, env vars, and data semantics for Alpaca Astro Center backend
globs: backend/**/*.py
alwaysApply: false
---

# Database (MongoDB)

## Driver & Config

- **motor** (async MongoDB client); connection settings from `backend/app/settings/config.py` / env:
  - `MONGO_DB_CONNECTION_URI` → `mongodb_connection_uri`
  - `MONGODB_DATABASE` → default `alpaca_astro_center`
  - `MONGODB_TELESCOPE_COLLECTION` → default `telescopes`
  - `MONGODB_OPERATION_COLLECTION` → default `operations`

Docker Compose typically uses URIs like `mongodb://user:pass@mongodb:27017` — see `backend/.env.example`.

## Collections (Conceptual)

### `telescopes` (primary telescope domain)

- Accessed via **telescope repository** implementations under `infra/repositories/telescope/`.
- Holds **Telescope** aggregate/state persisted as documents (oids, connection/tracking fields, etc.).

### `operations` (mixed operational records)

Used as a **logical store** for:

- **Model inference results** (request id, status, output/error, finished_at) — written when Kafka **model-inference-result** messages are consumed; idempotent upsert patterns apply (see `application/api/lifespan.py` and `docs/KAFKA_EVENT_POLICY.md`).
- **Command audit** rows (`record_type: command_audit` or equivalent convention used in code) for **hardware-affecting** telescope commands — query via `ListCommandAuditQuery` / `GET /telescopes/commands/audit`.

When adding new record types to **`operations`**, use a **clear `record_type` discriminator** (or separate collection if the domain grows) and document it in code/repository layer.

## Queries to Respect

- Inference reads use **`request_id`** as the natural key for idempotency and status polling.
- Command audit listings support **filters** (`operation`, `status`, `source`) + **limit** — mirror in any new admin/reporting endpoints.

## Do Not

- Do not bypass repositories from API handlers — go through **mediator → query/command handlers → repository ports**.
- Do not commit real `.env` files; secrets stay local (`.gitignore` covers `.env` at repo root and under `backend/` / `model-service/`).
