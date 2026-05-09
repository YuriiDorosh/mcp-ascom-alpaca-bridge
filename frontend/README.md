# Alpaca Astro Center — operator UI (MVP)

Vite + React SPA for local telescope control against the FastAPI backend.

## Docker (recommended)

From the **`backend/`** directory (uses `backend/.env`):

```bash
make app-dev-with-frontend
# or: make app-dev && make frontend-up
```

Open **http://localhost:5173** (or `http://localhost:${FRONTEND_PORT}`). The UI container is nginx serving a static build; the **browser** calls `VITE_API_BASE` (default `http://127.0.0.1:8000`). Change `VITE_API_BASE` / `FRONTEND_PORT` in `backend/.env`, then rebuild: `make frontend-down && make frontend-up`.

Stop stack: `make down-dev-with-frontend` (or `make frontend-down` if API stays up).

## Prerequisites (host Node — optional)

- Node.js 20+ (or 18 LTS) with npm — only for `npm run dev` hot reload without Docker
- Backend with CORS allowing the UI origin (`http://localhost:5173` is included by default when `CORS_ALLOWED_ORIGINS` is unset)

## Host dev (hot reload)

```bash
cd frontend
cp .env.example .env   # optional
npm install
npm run dev
```

## Safety

Command buttons call real Alpaca-backed endpoints when `ALPACA_ENABLED=true`. Use only on a safe test sky / with hardware precautions.

## Build (manual)

```bash
npm run build
```

`Dockerfile` runs this during `docker compose build`.
