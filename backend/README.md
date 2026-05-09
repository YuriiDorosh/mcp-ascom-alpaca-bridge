# Alpaca Astro Center Backend

Local-first FastAPI backend for ASCOM Alpaca telescope control with DDD architecture, Kafka messaging, and MongoDB persistence.

## Git workflow

Use **`feature/<topic>`** branches for normal work. **Batch related edits** (code, tests, docs for one logical step) into **fewer, larger pull requests** instead of micro-PRs for single-line doc tweaks—this keeps review and merge overhead low while the project is still pre-1.0. Merge into **`main`** when the chunk is coherent. Reserve **direct pushes to `main`** for **urgent hotfixes** only.

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
- `make test-backend-local` - run unit + integration pytest in one ephemeral container (parity with `ci.yml` pytest jobs; one Poetry install)
- `make ci-local` - run **`test-backend-local`** then **`model-service` `test-local`** (same two jobs as the hosted workflow when dispatched manually; slower but full-repo gate)
- `make frontend-up` - build and run the operator UI in **Docker** (nginx + static Vite build; port `FRONTEND_PORT`, default 5173 — see `docker_compose/frontend.yaml`)
- `make frontend-down` - stop the UI container
- `make app-dev-with-frontend` - same as `make app-dev` plus the **Docker** UI stack (API + Kafka + frontend)
- `make down-dev-with-frontend` - stop API + Kafka + **Docker** frontend together
- `make frontend-install` / `make frontend-dev` - optional **host** Node workflow (`npm install` / `npm run dev` in `../frontend`) for hot reload without Docker
- `make postman-smoke-local` - run Postman smoke collection via Newman (Docker, host network)
- `make postman-smoke-up` - start backend + Kafka + model-service and run Newman smoke checks
- `make postman-smoke-up-clean` - same as above, then stop stack (`down-dev-with-model`)
- `make hardware-smoke-dry-run` - run hardware preflight CLI checks (read-only by default) and write JSON report for `P5-HW-SMOKE` preparation
- `make hardware-validation-dry-run` - run validation-focused dry-run checks and write JSON report for `P5-HW-VALIDATION` preparation
- `make hardware-preflight-dry-run` - run smoke and validation JSON dry-runs in one command
- `make hardware-smoke-dry-run-with-notes` - run smoke dry-run and save both JSON report and markdown operator notes
- `make hardware-validation-dry-run-with-notes` - run validation dry-run and save both JSON report and markdown operator notes
- `make hardware-preflight-dry-run-with-notes` - run both smoke and validation dry-runs with markdown handoff notes
- `make hardware-smoke-live-run` - run `P5-HW-SMOKE` command-inclusive live smoke flow and save JSON+markdown artifacts
- `make hardware-validation-live-run` - run validation-focused CLI with command checks (`P5-HW-VALIDATION` track) and save `artifacts/hardware-validation-live-run.{json,md}`
- `make alpaca-lan-probe` - read-only `GET .../management/v1/configureddevices` against `ALPACA_ADDRESS` from `backend/.env` (no slew/sync/tracking; quick LAN + Alpaca reachability check)

### Seestar S30 Pro on LAN — suggested operator sequence

Use this order so you verify **reachability** and **read-only contracts** before anything that **slews** the mount (see `docs/TASKS.md` Phase 5 Hardware Gate).

1. Copy and edit `backend/.env` from `.env.example`. Set `ALPACA_ADDRESS` to `<telescope-lan-ip>:32323` and `ALPACA_ENABLED=true` when you want live Alpaca polling from the backend.
2. Start the stack (`make app-dev` or `make app-dev-with-model`).
3. **Read-only Alpaca probe (no motion):** `make alpaca-lan-probe` from `backend/` (uses `ALPACA_ADDRESS` / `ALPACA_PROTOCOL`).
4. **Read-only API preflight (no motion):** `make hardware-preflight-dry-run` or `make hardware-preflight-dry-run-with-notes`.
5. **Live command checks (requires safe sky/site, charged mount, clear obstacles):** `make hardware-smoke-live-run`; pass `COMMAND_TOKEN=…` when `COMMAND_AUTH_TOKEN` is set. Capture notes with `docs/hardware/p5_hw_smoke_baseline_template.md`.
6. **Validation track on hardware (auth/audit focus):** `make hardware-validation-live-run` after smoke baseline, same safety expectations.

Until step 5, **no physical interaction** with the Seestar beyond normal power/network is strictly required for tooling; steps 5–6 intentionally move the mount and must be run only when observation safety is satisfied.

### Operator UI (React MVP)

**Docker (recommended):** from `backend/` with `.env` configured, run `make app-dev-with-frontend` (or start the API first, then `make frontend-up`). Open `http://localhost:${FRONTEND_PORT:-5173}`. Set `VITE_API_BASE` in `.env` to where the **browser** reaches the API (usually `http://127.0.0.1:8000`). Rebuild the image after changing `VITE_API_BASE`.

**Host Node (hot reload):** install Node 20+, `make frontend-install`, `make frontend-dev`. See `frontend/README.md`.

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
  - includes static `manifest`, runtime `effective_manifest`, `hardware_readiness`, `hardware_smoke_plan`, `hardware_validation_plan`, and `hardware_overview` for one-call agent initialization.
- MCP execution plan (runtime-safe step sequence with capability-gated command tools): `GET http://localhost:8000/telescopes/tools/mcp-execution-plan`
  - supports `?mode=async|sync` to switch between polling flow and single-call inference flow.
  - supports `?include_disabled_commands=false` to return only currently runnable telescope command steps.
  - response includes `applied_filters` to confirm the active filtering mode used to build the plan.
  - response includes `stats.baseline_steps`, `stats.returned_steps`, and `stats.filtered_out_steps` to make filtering impact explicit.
  - response includes `hardware_smoke_plan`, `hardware_validation_plan`, and `hardware_overview` for machine-readable `P5` preflight/validation steps.
- Hardware readiness trigger (`Seestar` not required yet + next real-device task): `GET http://localhost:8000/telescopes/hardware/readiness`
- Hardware smoke plan template (machine-readable P5-HW-SMOKE checklist): `GET http://localhost:8000/telescopes/hardware/smoke-plan`
- Hardware validation plan template (machine-readable P5-HW-VALIDATION checklist): `GET http://localhost:8000/telescopes/hardware/validation-plan`
- Hardware overview bundle (readiness + both plans in one call): `GET http://localhost:8000/telescopes/hardware/overview`
  - both responses include `schema_version` for forward-compatible contract evolution.
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
   - `make test-backend-local` — backend unit + integration only (fast)
   - `make ci-local` — backend `test-backend-local` **plus** `model-service` `make test-local` (matches both pytest jobs from `.github/workflows/ci.yml` when you run the workflow manually)
   - GitHub Actions (`.github/workflows/ci.yml`) uses the same pytest selection when you **manually dispatch** the workflow (automatic runs on push/PR are off pre-release to save runner minutes)
   - or separately: `make test-unit-local` / `make test-integration-local`; full backend tree: `make test-local`

The project is intentionally testable without telescope hardware while `ALPACA_ENABLED=false`.

## Hardware CLI Preflight

- Quick Alpaca-only reachability (host network, uses `ALPACA_ADDRESS` / `ALPACA_PROTOCOL` from `backend/.env`): `make alpaca-lan-probe` or `python backend/scripts/alpaca_lan_probe.py` from `backend/` with the same `.env`. Override for a one-off check: `ALPACA_ADDRESS=192.168.x.x:32323 docker run ...` as in the Makefile target.
- Script: `backend/scripts/hardware_smoke_runner.py`
- Default behavior is read-only (`hardware/readiness`, `hardware/smoke-plan`, `hardware/validation-plan`, `hardware/overview`, `mcp-bootstrap`, `mcp-execution-plan`, `status`, `capabilities`, `commands/audit`).
- MCP aggregate checks enforce both checklist triggers, nested `hardware_overview` contract fields, and trigger consistency between top-level plans and overview payloads.
- Output report: `backend/artifacts/hardware-smoke-dry-run.json`
- Validation-only report: `backend/artifacts/hardware-validation-dry-run.json` via `--validation-only`
- Optional operator note output: pass `--notes-path artifacts/hardware-smoke-notes.md` (or validation variant) to save a markdown run summary for preflight handoff.
- Command checks safety gate: `--include-commands` is blocked when readiness reports `requires_real_telescope_now=false`; use `--allow-command-checks-when-not-ready` only for intentional override scenarios.
- Make wrappers: `make hardware-smoke-dry-run-with-notes` and `make hardware-validation-dry-run-with-notes` generate standard markdown handoff files in `backend/artifacts/`.
- Bundle wrapper: `make hardware-preflight-dry-run` runs both JSON-only smoke and validation dry-runs in sequence.
- Bundle wrapper: `make hardware-preflight-dry-run-with-notes` runs both note-producing flows in sequence for one-command preflight capture.
- Live smoke wrapper: `make hardware-smoke-live-run` targets `P5-HW-SMOKE`, enables command checks, and writes `artifacts/hardware-smoke-live-run.json` + `artifacts/hardware-smoke-live-run.md`.
- Live validation wrapper: `make hardware-validation-live-run` runs the CLI with `--validation-only` plus the same command-check flags as smoke live, writing `artifacts/hardware-validation-live-run.json` + `.md` (omit `hardware/smoke-plan` GET; still asserts smoke plan inside overview/bootstrap so contracts stay coherent).
- Operator qualitative baseline handoff outline (filled after a **real Seestar run**): `docs/hardware/p5_hw_smoke_baseline_template.md` (keep LAN secrets out of git when copying).
- Make targets run the CLI with host UID/GID mapping so generated reports remain editable/removable without root permission issues, and pre-clean stale report files before each run.
- Optional real-command checks are gated behind `--include-commands` and should be used only when intentionally running smoke or validation live targets on **real hardware** (`P5-HW-SMOKE` / `P5-HW-VALIDATION`).

## Troubleshooting / Known Issues

### Seestar: IP conflicts and stale ARP on Linux

On some LAN setups the Seestar’s DHCP lease can change, or another device can briefly use the same IPv4 address your notes still refer to as “the telescope”. Your machine may then keep an **incorrect neighbor (ARP) entry**: traffic to the “right” IP reaches the **wrong MAC**, so tools report `Connection timed out`, `nc`/`curl` hang, or `ping` shows **100% packet loss** even though the IP string in `ALPACA_ADDRESS` matches what the router UI showed earlier. The Alpaca API on port **32323** is especially easy to mistake for a “dead” device when this happens.

#### 1. Diagnosis (Linux)

Compare the kernel’s idea of the telescope IP with the **real** Seestar MAC from your router’s client list or the Seestar app.

```bash
ip neigh show <TELESCOPE_IP>
```

If the **lladdr** (MAC) in the output does **not** match the Seestar hardware MAC, you likely have a stale or conflicting neighbor entry—fix it before re-testing Alpaca.

To see which interface reaches your LAN default gateway (use that name in the flush command below):

```bash
ip route get 192.168.31.1
```

#### 2. Quick fix (flush ARP cache for the interface)

Clear neighbors on the Wi‑Fi or Ethernet interface your PC uses on the home LAN (examples: `wlp7s0`, `wlan0`, `enpXs0`):

```bash
sudo ip neigh flush dev <your_network_interface>
```

Then retry connectivity:

```bash
ping -c 3 <TELESCOPE_IP>
nc -zv -w2 <TELESCOPE_IP> 32323
curl -m 3 -s "http://<TELESCOPE_IP>:32323/management/v1/configureddevices"
```

#### 3. Permanent fix (recommended)

**Reserve a static DHCP lease** on your router: bind the Seestar’s **MAC address** to a fixed **LAN IP** so the address does not float and other clients cannot legitimately take the same lease. After any IP change, update `ALPACA_ADDRESS` in `backend/.env` to match the reserved address.

## Postman Starter Kit

- Import-ready templates are available in `backend/postman/`:
  - `alpaca-astro-center.postman_collection.json`
  - `alpaca-astro-center.smoke.postman_collection.json`
  - `alpaca-astro-center.local.postman_environment.json`
- See `backend/postman/README.md` for quick-start and variable usage.
