# Alpaca Astro Center

Local-first **FastAPI** backend for ASCOM Alpaca telescope control, optional **Kafka** + **model microservice**, and a minimal **React** operator UI. See **`docs/PROJECT_CONTEXT.md`**, **`docs/PLAN.md`**, and **`docs/TASKS.md`** for architecture and roadmap.

## Requirements

- [Docker](https://www.docker.com/get-started) & Docker Compose v2
- [GNU Make](https://www.gnu.org/software/make/)
- Optional: Node.js 20+ if you run the UI with `npm run dev` instead of Docker (see `frontend/README.md`)

## Quick start (Docker)

```bash
git clone https://github.com/YuriiDorosh/mcp-ascom-alpaca-bridge.git
cd mcp-ascom-alpaca-bridge
cp backend/.env.example backend/.env   # edit Mongo/Kafka/Alpaca as needed
make help
make dev                                # API + Kafka, then UI (nginx)
```

- **API / Swagger:** http://localhost:8000/api/docs  
- **Operator UI:** http://localhost:5173 (or `FRONTEND_PORT` in `frontend/.env`)

Stop stacks:

```bash
make dev-down
```

With the local model worker:

```bash
make dev-with-model
make dev-with-model-down
```

## Repository layout

| Path | Role |
|------|------|
| `backend/` | Main app, Compose for API + Kafka, `Makefile`, tests |
| `frontend/` | Vite + React UI, its own `docker-compose.yaml` |
| `model-service/` | Inference microservice (Kafka loop) |
| `docs/` | Product docs, task checklist, Kafka policy |

## Tests

From `backend/` (no running Compose required for local pytest):

```bash
make ci-local          # backend + model-service pytest in Docker
make test-backend-local
```

## Hardware (Seestar / Alpaca)

Connecting a **Seestar S30 Pro** or running live slew commands is **optional** for development. When you are ready for hardware-in-the-loop checks, follow **`docs/TASKS.md` (Phase 5 Hardware Gate)** and `backend/README.md` (LAN, port **32323**, preflight Make targets).
