# Alpaca Astro Center — operator UI (MVP)

Vite + React SPA. **Compose and Make targets live here** (not under `backend/`).

## Docker (recommended)

From **`frontend/`** (or copy **`frontend/.env.example`** → **`frontend/.env`** from the repo root before **`make dev`**):

```bash
cp .env.example .env   # FRONTEND_PORT, VITE_API_BASE — defaults match API at http://127.0.0.1:8000
make up
```

Open **http://localhost:5173** (or `FRONTEND_PORT` from `.env`).  
After changing **`VITE_API_BASE`**, rebuild: `make down && make up`.

The SPA can load **hardware readiness / overview** (`GET /telescopes/hardware/*`) and scope status without moving the mount — useful for the same checks you run from Postman/CLI before a live Seestar run.

Use **Connect** under *Operator WebSocket* for pushed `telescope_status` updates (same payload shape as `GET /telescopes/status`). Use **Live view** to fetch `GET /telescopes/operator/live-view`; when the backend fills in `image_url`, the UI shows the frame (placeholder until Seestar/Alpaca camera integration lands).

**MCP bootstrap & planning** load `/telescopes/tools/mcp-bootstrap` and `/telescopes/tools/mcp-planning-guide`. **MCP context** calls `/telescopes/context/mcp` with optional SIMBAD designation and ephemeris body. **ICRS → Alt/Az** uses `/telescopes/coordinates/radec-to-altaz` with observer latitude/longitude/elevation — set real site coordinates for meaningful horizons.

Stop: `make down`.

## Full stack from repo root

From the **project root** (parent of `backend/` and `frontend/`): use **`backend/.env`** and **`frontend/.env`** (see root **`README.md`** quick start), then:

```bash
make help           # list all root targets
make dev            # API + Kafka, then UI
make dev-down       # stop UI, then API + Kafka
make logs           # follow logs from backend + frontend (interleaved)
make ps             # container status for both compose projects
```

With model-service:

```bash
make dev-with-model
make dev-with-model-down
make logs-with-model
make ps-with-model
```

## Host Node (hot reload, no Docker UI)

```bash
make install
make dev
```

Requires Node 20+. Backend must allow CORS for `http://localhost:5173` (default when backend `CORS_ALLOWED_ORIGINS` is unset).

## Safety

Command buttons call real Alpaca-backed endpoints when `ALPACA_ENABLED=true` on the backend. Use only with a safe sky and mount precautions.

## Layout

| File | Role |
|------|------|
| `docker-compose.yaml` | nginx UI service, build `context: .` |
| `Dockerfile` | multi-stage build + nginx |
| `Makefile` | `up` / `down` / `logs` / `build` / `install` / `dev` |
