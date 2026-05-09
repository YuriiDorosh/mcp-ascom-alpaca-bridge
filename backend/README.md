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

The UI lives in **`../frontend/`** with its own **`Makefile`** and **`docker-compose.yaml`**. From the **repository root**, run **`make help`** for orchestration (e.g. `make dev`, `make dev-down`, `make logs`, `make up-backend` / `down-frontend`, `make ps`). Details: `frontend/README.md`.

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
- Operator WebSocket (browser ↔ backend, periodic `telescope_status` JSON): `ws://127.0.0.1:8000/telescopes/ws/operator` (use `wss://` when the API is served over HTTPS)
- Live-view / FOV contract (still or stream URL when integrated; placeholder until camera path is wired): `GET http://localhost:8000/telescopes/operator/live-view`
  - set optional `OPERATOR_LIVE_VIEW_IMAGE_URL` (http/https) to expose a LAN still/MJPEG URL to the operator UI without code changes
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

## Operator camera preview (`OPERATOR_LIVE_VIEW_IMAGE_URL`)

The SPA can only show “what the camera sees” if you configure a **fixed `http://` or `https://` URL** that already returns image data: a single still (`image/jpeg`, `image/png`, …) or a Motion-JPEG stream (`multipart/x-mixed-replace` is common). The backend **does not auto-discover** your telescope’s camera. It reads `OPERATOR_LIVE_VIEW_IMAGE_URL` from `backend/.env`, validates the scheme, and returns that string as `image_url` from `GET /telescopes/operator/live-view` so the browser can render `<img src="...">`.

**Do I need an HTTP endpoint on the telescope right now?**

- **You need some LAN-reachable HTTP(S) picture URL** if you want this feature to work today. Often that is **on the device** (built-in IP camera behaviour) or **not exposed at all** by the vendor.
- **Alpaca on port `32323`** (Seestar LAN control) is for **driver-style commands and status**, not guaranteed to expose a trivial “live JPEG at `/foo`”. A preview path may be undocumented, behind the vendor app only, or absent.
- If you **cannot find** a URL that loads in a browser tab (or returns image headers with `curl -sSI`), leave the variable unset; the UI stays on the placeholder until you have a URL or until a dedicated integration (see `P5-UI-LIVEVIEW-SEESTAR` in `docs/TASKS.md`) implements a supported capture path.

**How to sanity-check a candidate URL**

1. From the same PC/LAN, open it in a normal browser tab, or run:
   ```bash
   curl -sSI "http://YOUR_HOST:PORT/your/path"
   ```
   and look for an image-friendly `Content-Type` or a streaming MJPEG content type.
2. If the stream **requires login, cookies, or a proprietary protocol** only the vendor app understands, a plain `<img>` will usually **fail** until you add a proxy or a different integration.

**Workarounds people use before native Seestar video is wired**

- A **separate IP camera** or NVR on the LAN with a known snapshot/MJPEG URL.
- An **`ffmpeg` (or similar) restream** on your network that exposes `http://…` MJPEG or repeated stills—point `OPERATOR_LIVE_VIEW_IMAGE_URL` at that URL.

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

### Seestar / LAN telescope: lost connection, timeouts, and Linux ARP cache (MAC conflicts)

This section covers “everything on Linux times out” scenarios: **Alpaca HTTP** (port **32323**), **RTSP** / `ffplay`, or any other TCP client from the same machine—**even when** the telescope stays online in the **router admin UI** and remains usable from the **vendor mobile app**.

#### Symptoms

- Connections **time out**: `curl`, `nc`, browser, or your backend with `ALPACA_ENABLED=true` cannot reach the scope.
- **`ping` fails** or shows **100% packet loss** toward the telescope IP.
- **RTSP viewers** (e.g. `ffplay rtsp://…`) or other stream tools **cannot connect**.
- The **router still lists** the telescope at that IP and the **mobile app** still reaches the device—so the problem is not “Wi‑Fi died” but often **how your Linux host routes L2 to that IP**.

#### Cause (stale or wrong ARP / neighbor entry)

The router may have correctly assigned the telescope’s IPv4 address, but **Linux still maps that IP to an old MAC** (a previously connected device that released the address, a clone, or a bad cache line). Packets leave your PC toward the **wrong Ethernet address**, so APIs, RTSP, and `ping` fail from Linux even though other paths (phone on Wi‑Fi, different ARP state) still work.

DHCP lease churn, hotplugging another gadget that briefly conflicted, or sleep/resume on the laptop can all trigger this.

#### Diagnosis (Linux)

1. Read the **correct telescope MAC** from the **router DHCP client list** or the vendor app / device label.
2. Compare with the kernel neighbor table:

```bash
ip neigh show <TELESCOPE_IP>
```

If **lladdr** does **not** match the real telescope MAC, treat the entry as **stale/wrong** before re-testing Alpaca, RTSP, or preview URLs.

Pick the **interface** you use on the home LAN (Wi‑Fi examples: `wlp7s0`, `wlan0`; Ethernet: `enpXs0`). You can derive it from the route to your gateway (replace with your router IP):

```bash
ip route get 192.168.31.1
```

#### Solutions

1. **Quick fix — flush the neighbor (ARP) cache on that interface**

   ```bash
   sudo ip neigh flush dev <your_network_interface>
   ```

   Examples: `wlp7s0`, `wlan0`, `enp3s0`.

2. **Local fix — pin the correct MAC for that IP (until reboot or table change)**

   Forces Linux to send L2 frames to the telescope you expect (useful right after a collision, or when flush alone is not enough):

   ```bash
   sudo ip neigh replace <TELESCOPE_IP> lladdr <TELESCOPE_MAC> dev <your_network_interface> nud permanent
   ```

   Replace `<TELESCOPE_MAC>` with the colon-separated MAC from the router (e.g. `aa:bb:cc:dd:ee:ff`). This is **not** a substitute for a router-side reservation: it is host-local and can be lost on reboot or significant network changes—use it to **unblock debugging** and confirm ARP was the issue.

3. **Global fix (recommended) — static DHCP reservation on the router**

   In the router admin panel, create a **DHCP static lease**: bind the telescope’s **MAC** to a single **LAN IP** so the address does not float and another device cannot legitimately claim the same lease. After any IP change, update `ALPACA_ADDRESS` in `backend/.env` (and any preview/RTSP bookmarks) to match.

#### After any fix — quick re-check

```bash
ping -c 3 <TELESCOPE_IP>
nc -zv -w2 <TELESCOPE_IP> 32323
curl -m 3 -s "http://<TELESCOPE_IP>:32323/management/v1/configureddevices"
```

For RTSP, retry your `ffplay`/player command once `ip neigh show` shows the **correct** lladdr.

## Postman Starter Kit

- Import-ready templates are available in `backend/postman/`:
  - `alpaca-astro-center.postman_collection.json`
  - `alpaca-astro-center.smoke.postman_collection.json`
  - `alpaca-astro-center.local.postman_environment.json`
- See `backend/postman/README.md` for quick-start and variable usage.
