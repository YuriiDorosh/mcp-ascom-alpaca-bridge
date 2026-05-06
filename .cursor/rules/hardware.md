---
description: Telescope hardware, ASCOM Alpaca, safety gates, and when to assume real devices (e.g. Seestar)
globs:
  - backend/app/application/api/telescope/**/*.py
  - backend/app/infra/integrations/alpaca/**/*.py
alwaysApply: false
---

# Hardware & Telescope Integration

## Protocol

- Control is **ASCOM Alpaca over HTTP** — implemented via **`alpyca`** behind **`IAlpacaClient` / `IAlpacaTelescopeClient`** (`infra/integrations/alpaca/`).
- Host and telescope should be on the **same LAN** (see `docs/PROJECT_CONTEXT.md`).

## Default: No Hardware

- **`ALPACA_ENABLED=false`** is the **default** for local/CI — deterministic, no Alpaca calls.
- Integration tests use **mocked** telescope drivers / Kafka — **do not require** a physical mount or **Seestar S30 Pro** for normal development.
- Only enable live Alpaca when the **user explicitly** asks to validate real hardware.

## Capability & Safety

- **Capability flags** (`supports_slew`, `supports_sync`, `supports_tracking`) come from live Alpaca snapshot when probing is on; otherwise safe defaults — see status/capabilities endpoints and **`/telescopes/tools/mcp-manifest`**.
- **Moving hardware**: slew / sync / tracking endpoints; optional **`COMMAND_AUTH_TOKEN`** → client must send **`X-Command-Token`**. Command attempts are **audited** to MongoDB (`operations` collection) and surfaced via **`GET /telescopes/commands/audit`**.
- Map driver/domain failures to the correct HTTP status (e.g. **502** for Alpaca/driver issues) using existing exception types in `domain/exceptions/telescope.py`.

## Optional Features (Network / Downloads)

- **Catalog** (`CATALOG_LOOKUP_ENABLED`) — Sesame/CDS via astroquery; may need outbound network.
- **Ephemeris** (`EPHEMERIS_ENABLED`) — Skyfield + BSP kernel (`EPHEMERIS_KERNEL`).

## Model Runtime vs Telescope Hardware

- **GPU/CPU profile** (`MODEL_RUNTIME_PROFILE` in model-service: `cpu` | `amd` | `nvidia`) concerns **local LLM inference**, not the telescope mount.
- Do not conflate **model-service** runtime with **Alpaca** connectivity.

## User Devices (e.g. Seestar S30 Pro)

- Treat **Seestar** (or any consumer device) as **out of scope** until the user requests connection testing.
- When adding Seestar-specific notes, keep them in **docs** or **README** as **optional** integration assumptions — the core codebase stays **Alpaca-abstract**.

## Checklist Before Advising "Connect the Telescope"

- User asked for **live** validation.
- `ALPACA_ENABLED=true` and correct **`ALPACA_ADDRESS`**, device number, protocol.
- Operator understands **safety** (clear aperture, tracking, slew limits).
