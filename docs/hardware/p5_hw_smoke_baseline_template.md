# P5 hardware smoke — baseline capture (operator template)

Fill this **after** a real **Seestar S30 Pro** LAN run (`P5-HW-SMOKE` / `make hardware-smoke-live-run`). Intended for concise hand-off: what worked, what differed from dry-run assumptions, follow-ups.

> **Needs physical telescope:** Alpaca reachable on **`http://<ip>:32323`**, backend `ALPACA_*` aligned with the device, charging and safe sky conditions respected.

---

## Run context

| Field | Value |
| ----- | ----- |
| Date (UTC/local) | |
| Telescope | Seestar S30 Pro |
| Firmware / companion app hints (optional) | |
| Operator | |
| Repo / backend commit SHA | |

## Network / Alpaca

| Field | Value |
| ----- | ----- |
| Telescope LAN IP (reserved lease?) | |
| `backend/.env` `ALPACA_ADDRESS` snapshot | |
| Quick probe (e.g. `curl`/Alpaca discovery) outcome | |

## Preflight tooling

- `make hardware-preflight-dry-run(-with-notes)` or CLI notes path (attach paths if saved):
-
- Hardware readiness snapshot (`requires_real_telescope_now` / gates):  

## Live smoke artifacts

- JSON report path (default `backend/artifacts/hardware-smoke-live-run.json`):
-
- Markdown notes path (`hardware-smoke-live-run.md`):  
-

## Behaviour summary

**Status / capabilities**

- Anything unexpected vs `GET /telescopes/status` or MCP bootstrap plans?

**Commands exercised (safely)**

- Slew — range, slew time, Abort/stop behaviour if tested:
-
- Sync — accepted / rejected notes:
-
- Tracking on/off — latch time, dome/tripod clearance:

## Anomalies / follow-ups

- Timeouts, 401/command token, Kafka/model noise, Compose vs host Alpaca quirks:
-

---

When this file has real data, optionally copy it beside your smoke JSON (`artifacts/` or `/docs/hardware/archive/…`) per team policy—**do not** commit secrets or private LAN details you do not want in git.
