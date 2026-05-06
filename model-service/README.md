# Alpaca Astro Center Model Service

Local FastAPI microservice that consumes inference requests from Kafka and publishes inference results back to Kafka.

## Current Scope

- Focused on Phase 4 skeleton wiring.
- Uses a deterministic mock runtime (no heavy local model loaded yet).
- Keeps request/result contract compatibility with main backend (`schema_version`, `request_id`, `correlation_id`).

## Environment

Copy `.env.example` to `.env` and adjust values if needed. The file is gitignored and stays on your machine only.

## Run with Docker (recommended for full stack)

The model service is built and run together with the main backend and Kafka from the `backend/` tree:

```bash
cd ../backend
cp .env.example .env   # once; edit KAFKA_URL, MODEL_*, etc.
make app-dev-with-model
```

Compose reads environment from **`backend/.env`**, not from `model-service/.env`. Variables under `environment:` in `backend/docker_compose/model-service.yaml` are injected into the container (Kafka URL, topics, runtime profile, port mapping).

After startup: `GET http://localhost:8010/health` and `GET http://localhost:8010/runtime/profiles`.

## Run Locally (Poetry, without Compose)

Use this when developing the model service in isolation; then `model-service/.env` **is** loaded for local runs (via Pydantic settings / shell env):

```bash
cd model-service
cp .env.example .env
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

## API

- `GET /health` - service health probe
- `GET /runtime/profiles` - active runtime profile and supported profile list

## Kafka Flow

1. Consume from `MODEL_INFERENCE_REQUEST_TOPIC` (default `model-inference-request`)
2. Build mock result text from prompt
3. Publish to `MODEL_INFERENCE_RESULT_TOPIC` (default `model-inference-result`)

If runtime inference fails for a request, worker publishes `status=failed` with `error_message`, while keeping `request_id`/`correlation_id` for backend traceability.

## Runtime Profiles

Current supported `MODEL_RUNTIME_PROFILE` values:

- `cpu`
- `amd`
- `nvidia`
