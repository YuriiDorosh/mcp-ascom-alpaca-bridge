# Alpaca Astro Center Model Service

Local FastAPI microservice that consumes inference requests from Kafka and publishes inference results back to Kafka.

## Current Scope

- Focused on Phase 4 skeleton wiring.
- Uses a deterministic mock runtime (no heavy local model loaded yet).
- Keeps request/result contract compatibility with main backend (`schema_version`, `request_id`, `correlation_id`).

## Environment

Copy `.env.example` to `.env` and adjust values if needed.

## Run Locally

```bash
cd model-service
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

## API

- `GET /health` - service health probe

## Kafka Flow

1. Consume from `MODEL_INFERENCE_REQUEST_TOPIC` (default `model-inference-request`)
2. Build mock result text from prompt
3. Publish to `MODEL_INFERENCE_RESULT_TOPIC` (default `model-inference-result`)

If runtime inference fails for a request, worker publishes `status=failed` with `error_message`, while keeping `request_id`/`correlation_id` for backend traceability.
