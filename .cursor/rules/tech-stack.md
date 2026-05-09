---
description: Tech stack, repo layout, Docker/Make workflow, and model-service split for Alpaca Astro Center
alwaysApply: true
---

# Tech Stack & Repository Layout

## What This Repo Is

**Alpaca Astro Center** — local-first stack: main **FastAPI** backend (telescope domain + APIs), **MongoDB**, **Kafka**, optional **model microservice** (`model-service/`), **React** operator UI (`frontend/`, Docker + Vite). Docs live in `docs/` (authoritative product/architecture context: `PROJECT_CONTEXT.md`, `PLAN.md`, `TASKS.md`, `KAFKA_EVENT_POLICY.md`, `MIGRATION_NOTES.md`).

## Top-Level Structure

| Path | Role |
|------|------|
| `backend/` | Main app: Python package under `backend/app/`, Poetry, Dockerfile, `docker_compose/`, `Makefile`, tests |
| `model-service/` | Separate FastAPI service: Kafka consumer/producer for model inference (mock runtime today; GPU profiles later) |
| `docs/` | English project docs — roadmap, tasks, Kafka policy, migration notes |
| `frontend/` | Vite + React operator MVP; **Docker:** `frontend/Dockerfile`, `backend/docker_compose/frontend.yaml`, `make frontend-up` from `backend/` |

## Backend Stack

- **Python 3.12**, **Poetry** (`backend/pyproject.toml`, `poetry.lock`)
- **FastAPI** + **Uvicorn**, **Pydantic** / **pydantic-settings** for config
- **MongoDB** via **motor** (async)
- **Kafka** via **aiokafka** (`KafkaMessageBroker` adapter)
- **Astronomy / telescope**: `alpyca`, `astropy`, `skyfield`, `astroquery`
- **Tests**: `pytest`, `pytest-asyncio`; `tests/unit` vs `tests/integration`

## Model Service Stack

- **FastAPI** + **aiokafka** + **orjson**; own `pyproject.toml`
- Runtime profiles (typed config): `cpu` | `amd` | `nvidia` (`MODEL_RUNTIME_PROFILE`)
- **Docker**: `model-service/Dockerfile`; wired from `backend/docker_compose/model-service.yaml`

## Docker & Make (Prefer for Full Stack)

- From **`backend/`**: `make app-dev` (main app + Kafka), `make app-dev-with-model` (+ model-service), `make storages` (MongoDB), `make test-local` / `test-*-local` (pytest in ephemeral Python container)
- **Compose env**: primary file is **`backend/.env`** (from `backend/.env.example`) — Kafka URL, Mongo URI, model topics, `MODEL_SERVICE_PORT`, etc.
- **`model-service/.env`**: used mainly for **local Poetry** runs inside `model-service/` (Pydantic `env_file`); **Compose injects** model-service env from **`backend/.env`**, not automatically from `model-service/.env` (see `model-service/README.md`).

## Key Ports (defaults)

- Main API / Swagger: `http://localhost:8000` (`API_PORT`), docs at `/api/docs`
- Model service health: `http://localhost:8010` (`MODEL_SERVICE_PORT`)
- Kafka UI / broker ports: see `backend/README.md`

## Inference Flow (High Level)

- Backend enqueues **`ModelInferenceRequestContract`** to Kafka → **model-service** consumes → publishes **`ModelInferenceResultContract`** → backend consumer persists to MongoDB.
- HTTP helpers: enqueue, get result, wait, status, enqueue-and-wait — see telescope routes under `/telescopes/model/inference/*`.

## Git Workflow (Project Convention)

- Work on **`feature/<short-topic>`** branches. Prefer **batched PRs**: combine related files (implementation + tests + docs) for one milestone or feature slice, and **merge less often**—avoid one PR per minimal change. See the blockquote at the top of **`docs/TASKS.md`**. Direct `main` commits only for **urgent hotfixes**.

## When Adding Dependencies

- Pin in **Poetry**; run lock/install in a **consistent Python 3.12** environment (Dockerized Poetry if local host lacks build tools for native wheels).
