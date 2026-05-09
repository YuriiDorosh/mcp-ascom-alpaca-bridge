# Alpaca Astro Center - Implementation Tasks

> **Branching convention:** merge work through **`feature/<short-topic>` branches** and GitHub PRs rather than committing everything directly onto `main`, unless fixing an urgent breakage.

## Phase 1 - Template Adaptation and Cleanup

- [x] Create `docs/` baseline and ensure all new project docs are in English.
- [x] Update project naming strings from chat-template branding to `Alpaca Astro Center`.
- [x] Review `backend/README.md` and mark chat-specific sections for replacement.
- [x] Identify all modules under `backend/app` that implement chat/message logic.
- [x] Remove or deprecate legacy chat API routes from FastAPI router registration.
- [x] Remove chat websocket endpoints that are tied to chat rooms/messages.
- [x] Remove leftover websocket/chat legacy manager abstractions from infra/application core.
- [x] Remove chat-specific Pydantic schemas and DTOs from API layer.
- [x] Remove chat/message command handlers from application logic.
- [x] Remove chat/message query handlers from application logic.
- [x] Remove chat/message domain entities and value objects.
- [x] Remove chat/message domain events and event handlers.
- [x] Remove chat/message repository interfaces from infra ports.
- [x] Remove chat/message Mongo repository adapters.
- [x] Introduce new bounded-context package for telescope domain (`telescope`).
- [x] Create initial `Telescope` domain entity (identity, capabilities, connection state).
- [x] Create initial value objects for coordinates and telescope status snapshots.
- [x] Define domain events for telescope lifecycle transitions (`TelescopeConnectionStateChangedEvent`, `TelescopeTrackingChangedEvent`).
- [x] Define command contracts for telescope control intents (`SlewToIcrsCommand`, `SyncMountToIcrsCommand`, `SetTelescopeTrackingCommand`).
- [x] Define query contracts for telescope status retrieval intents.
- [x] Define `ITelescopeRepository` interface.
- [x] Define `IAlpacaClient` interface as an external port.
- [x] Define `ICoordinateTransformService` interface as a domain-support port.
- [x] Define `IEphemerisService` and `ICatalogResolveService` port stubs (implementations wired later).
- [x] Update DI container registrations in composition root to remove chat dependencies.
- [x] Register placeholder/stub telescope services to validate app startup.
- [x] Ensure app lifespan still initializes Kafka and core dependencies safely.
- [x] Add/adjust health and readiness endpoints for the repurposed backend.
- [x] Run static import checks and remove dead imports after cleanup.
- [x] Ensure tests no longer reference removed chat modules.
- [x] Add migration notes in docs for template-to-telescope transition (`docs/MIGRATION_NOTES.md`).

## Phase 2 - Alpyca and Astropy Integration

- [x] Add required dependencies: `alpyca`, `astropy`, `skyfield`, `astroquery`.
- [x] Verify dependency pinning/version policy in `pyproject.toml`.
- [x] Create infra adapter implementing `IAlpacaClient` with `alpyca` (`AlpycaTelescopeClient` snapshot probe).
- [x] Add Alpaca configuration model (host, port, device number, timeouts).
- [x] Implement lightweight Alpaca connectivity snapshot (pollable discovery path for LAN Alpaca servers).
- [x] Extend telescope status query payload with optional Alpaca snapshot when probing is enabled.
- [x] Implement command handler for slew-to-coordinates flow (Alpyca `SlewToCoordinates`, HTTP `/telescopes/commands/slew-icrs`).
- [x] Implement command handler for sync flow (checks `CanSync`, HTTP `/telescopes/commands/sync-icrs`).
- [x] Implement command handler for tracking on/off (HTTP `/telescopes/commands/tracking`).
- [x] Create `ICoordinateTransformService` implementation using `astropy`.
- [x] Implement RA/Dec to Alt/Az conversion utility with observer location/time inputs (HTTP `/telescopes/coordinates/radec-to-altaz`).
- [x] Add deterministic tests for coordinate transforms with fixed timestamps.
- [x] Create `IEphemerisService` interface for Solar System targets (`domain/ports/ephemeris.py`).
- [x] Add initial `skyfield` implementation for planetary target coordinates (DI-backed `SkyfieldEphemerisService` + `GET /telescopes/ephemeris/icrs`).
- [x] Create target-resolution abstraction for SIMBAD/VizieR lookups (`domain/ports/catalog_resolve.py`).
- [x] Add initial catalog object-name adapter with timeouts (`SesameBackedCatalogResolveService` using `SkyCoord.from_name`, `asyncio.wait_for`; HTTP `/telescopes/catalog/icrs`, env `CATALOG_LOOKUP_ENABLED`).
- [x] Define starter domain telescope/coordinate/ephemeris error types (`AlpacaDriverException`, `CoordinateTransformException`, etc.).
- [x] Ensure telescope command/catalog paths map Alpaca/driver and lookup failures via domain exceptions (`AlpacaDriverException`, `UnresolvedObjectNameException`, etc.) to HTTP statuses in the FastAPI boundary.
- [x] Publish telescope operation events to Kafka from command handlers (topic `telescope-operation-events`, configurable via `TELESCOPE_OPERATION_TOPIC`).
- [x] Define initial Kafka event schema placeholders for model-service interaction.
- [x] Create interface contracts for inference request/result events.
- [x] Add integration tests for Alpaca adapter against mocked endpoints (`tests/integration/test_alpyca_adapter_mocked.py`).
- [x] Add integration tests for Kafka publication from telescope operations (`tests/integration/test_telescope_operation_events_api.py` with mocked broker).
- [x] Document assumptions for hardware-unavailable development mode (`ALPACA_ENABLED` / `CATALOG_LOOKUP_ENABLED` default off for portable stacks — see `backend/README.md` and `backend/.env.example`).
- [x] Add TODO references for Phase 4 MCP tool wiring dependencies (see Phase 4 dependency notes below).

## Notes for Upcoming Phases

- The local model runtime will be a separate FastAPI microservice.
- Main backend and model microservice will communicate through Kafka.
- Model runtime profiles must support NVIDIA, AMD, and CPU-only environments.

## Phase 3 Kickoff Checklist

- [x] Add explicit contract metadata (`schema_version`, `correlation_id`) to Kafka message contracts used by inference and telescope operation events.
- [x] Document topic naming/versioning policy and backward-compatibility rules for future event schema changes (`docs/KAFKA_EVENT_POLICY.md`).
- [x] Define restart-safe processing and idempotency strategy for telescope operation consumers (`docs/KAFKA_EVENT_POLICY.md`, consumer ledger + offset discipline guidance).
- [x] Add idempotent duplicate-guard in model-inference result consumer before Mongo writes (`application/api/lifespan.py`) with unit coverage.

## Phase 4 Dependency Notes (TODO references)

- TODO(P4-MCP-TOOLS): Expose telescope command/query capabilities as MCP tools with explicit capability flags (`supports_slew`, `supports_sync`, `supports_tracking`) to prevent unsafe tool execution paths. [DONE-foundation: capability flags surfaced via `/telescopes/status` + `/telescopes/capabilities`]
- TODO(P4-MCP-AUTH): Define local-network trust/auth strategy for MCP actions that can move hardware (token/session model + audit trail). [DONE-foundation: optional `COMMAND_AUTH_TOKEN` + `X-Command-Token` guard on `/telescopes/commands/*`, command audit writes to operations collection, and audit read endpoint `/telescopes/commands/audit`]
- TODO(P4-MCP-AUTH): Add audit-query filters (`operation`, `status`, `source`) to simplify least-privilege MCP agent review flows. [DONE-hardening: `/telescopes/commands/audit` now supports `limit`, `operation`, `status`, `source`]
- TODO(P4-MCP-CONTEXT): Wire catalog + ephemeris + live telescope status into MCP context assembly so tool-calling agents can reason over target/object/position state before command dispatch. [DONE-foundation: `/telescopes/context/mcp` aggregates status/capabilities + optional catalog/ephemeris payloads]
- TODO(P4-MODEL-SVC): Bootstrap dedicated local model FastAPI microservice with Kafka request/result loop and deterministic mock runtime before heavy-model profiles. [DONE-foundation: added `model-service/` skeleton with `/health`, Kafka consumer/producer loop, shared v1 request/result fields, and unit test]
- TODO(P4-MODEL-SVC): Integrate model-service into local Docker/Make workflow for one-command backend+Kafka+model bring-up. [DONE-foundation: added `model-service/Dockerfile`, compose overlay `backend/docker_compose/model-service.yaml`, and `make app-dev-with-model` lifecycle commands]
- TODO(P4-MODEL-SVC): Ensure model-service publishes explicit failed inference contracts (`status=failed`, `error_message`) without stopping worker loop. [DONE-hardening: added defensive worker error boundary and unit coverage for completed/failed result contract generation]
- TODO(P4-MCP-TOOLS): Publish machine-readable MCP tool manifest endpoint with command capability/auth requirements for safe tool dispatch planning. [DONE-hardening: added `GET /telescopes/tools/mcp-manifest` with explicit tool metadata and integration tests]
- TODO(P4-MODEL-SVC): Add backend-side inference wait API with timeout/poll parameters to reduce client-side polling complexity over async Kafka completion. [DONE-hardening: added `GET /telescopes/model/inference/{request_id}/wait` with timeout handling and integration tests]
- TODO(P4-MODEL-SVC): Add single-call enqueue+wait inference API for MCP/client simplicity while preserving timeout controls. [DONE-hardening: added `POST /telescopes/model/inference/enqueue-and-wait` with timeout/poll params and integration tests]
- TODO(P4-MODEL-SVC): Formalize runtime profile contract (`cpu`/`amd`/`nvidia`) and expose profile metadata endpoint for operational checks before heavy-model rollout. [DONE-foundation: added typed profile validation in config, `GET /runtime/profiles`, and endpoint/config tests]
- TODO(P4-MODEL-SVC): Document Docker vs local `model-service/.env` usage and load optional `.env` for Poetry runs via Pydantic Settings. [DONE-hardening: extended `model-service/README.md`, added repo-root `.gitignore` entry for `.env`, wired `env_file` in `model-service` Config]
- TODO(P4-MODEL-SVC): Provide inference status endpoint returning `pending/completed/failed` without 404 churn while Kafka result is in-flight. [DONE-hardening: added `GET /telescopes/model/inference/{request_id}/status` with integration coverage]
- TODO(P4-DX-POSTMAN): Provide import-ready Postman collection/environment templates for backend API exploration and third-party client development. [DONE-foundation: added `backend/postman/` starter kit with collection, local environment, and README]
- TODO(P4-DX-POSTMAN): Add collection-runner smoke suite for one-click API sanity checks after local stack startup. [DONE-hardening: added `backend/postman/alpaca-astro-center.smoke.postman_collection.json` with ordered requests and basic assertions]
- TODO(P4-DX-POSTMAN): Add CLI smoke runner command so API sanity checks can run in Dockerized CI-like flow without opening Postman UI. [DONE-hardening: added `make postman-smoke-local` using Newman container and documented `BASE_URL` override]
- TODO(P4-CI-GITHUB): Add GitHub Actions workflow that runs backend Dockerized pytest targets on push/PR so regressions surface before merge. [DONE: `.github/workflows/ci.yml` gates backend/model jobs with `dorny/paths-filter`; `workflow_dispatch` runs both suites; pytest uses Poetry on the ubuntu runner]
- TODO(P4-CI-GITHUB-MODEL-SVC): Run model-service pytest in GitHub Actions when the microservice tree changes. [DONE: `ci.yml` `model-pytest` job + `model-service/Makefile` `test-local` for Docker-parity locally]
- TODO(P4-CI-POETRY-CACHE): Cache Poetry dependencies on GitHub-hosted runners so repeated CI stays fast and cheap. [DONE: `actions/cache` on `~/.cache/pypoetry`, keyed per `backend/poetry.lock` or `model-service/poetry.lock`, with restore scheduled before Poetry install so cached wheels are available early; `setup-python` still avoids `cache: poetry` because that mode expects `poetry` on PATH ahead of time]
- TODO(P4-CI-ACTIONS-VERS): Keep GitHub Actions action majors aligned with runner images (checkout/setup-python/cache, paths-filter). [DONE: `actions/checkout@v6`, `actions/setup-python@v6`, `actions/cache@v5`, `dorny/paths-filter@v4` in `.github/workflows/ci.yml`; job `name` fields; top-level `POETRY_NO_INTERACTION`]
- TODO(P4-CI-DEPENDABOT): Enable Dependabot for GitHub Actions so action updates surface as automated PRs. [DONE: `.github/dependabot.yml` weekly `package-ecosystem: github-actions` at repo root]
- TODO(P4-CI-MANUAL-ONLY): Suspend automatic CI on push/PR until first release to reduce GitHub Actions runner cost; keep on-demand `workflow_dispatch`. [DONE: `.github/workflows/ci.yml` triggers only `workflow_dispatch`; use `make test-backend-local` / model-service tests locally]
- TODO(P4-DX-POSTMAN): Add one-command stack bring-up + smoke runner targets for faster local validation loops. [DONE-hardening: added `make postman-smoke-up` and `make postman-smoke-up-clean` targets]
- TODO(P4-MCP-TOOLS): Extend MCP manifest to include model inference tool surface so agents can orchestrate async model flows from one capability map. [DONE-hardening: `/telescopes/tools/mcp-manifest` now includes enqueue/status/wait/enqueue-and-wait model tools]
- TODO(P4-MCP-TOOLS): Add MCP planning guide endpoint documenting recommended model inference tool order and timeout bounds for safer agent orchestration. [DONE-hardening: added `GET /telescopes/tools/mcp-planning-guide` with structured flow and integration test]
- TODO(P4-MCP-TOOLS): Add one-call MCP bootstrap endpoint that aggregates manifest and planning guide for faster agent startup. [DONE-hardening: added `GET /telescopes/tools/mcp-bootstrap` with integration coverage]
- TODO(P4-MCP-TOOLS): Add effective MCP manifest endpoint with runtime `enabled`/`disabled_reason` flags so agents can skip unsupported command tools before dispatch. [DONE-hardening: added `GET /telescopes/tools/mcp-manifest/effective` with integration tests]
- TODO(P4-MCP-TOOLS): Extend MCP bootstrap payload to include runtime effective manifest so clients can initialize static and dynamic tool availability in one call. [DONE-hardening: `/telescopes/tools/mcp-bootstrap` now returns both `manifest` and `effective_manifest`]
- TODO(P4-MCP-TOOLS): Harden MCP bootstrap with infra-failure fallback test so `effective_manifest` remains safe when telescope status is unavailable. [DONE-hardening: added integration coverage for bootstrap fallback with command tools disabled]
- TODO(P4-MCP-TOOLS): Lock `effective_manifest` disabled-reason contract with integration assertions for both enabled and disabled tools. [DONE-hardening: added explicit `disabled_reason` null/non-null checks in effective manifest integration tests]
- TODO(P4-DX-POSTMAN): Add payload contract assertions for `mcp-bootstrap` in smoke collection to detect regressions in `effective_manifest` structure. [DONE-hardening: smoke tests now assert `effective_manifest.tools` presence and non-empty array]
- TODO(P4-DX-POSTMAN): Add payload contract assertions for `mcp-manifest/effective` in smoke collection to verify `enabled` and `disabled_reason` fields remain stable. [DONE-hardening: smoke tests now assert `enabled` and `disabled_reason` keys in effective manifest tools]
- TODO(P4-DX-POSTMAN): Extend Postman starter and smoke collections to cover newly added MCP planning/bootstrap endpoints for complete discovery flow checks. [DONE-hardening: added `mcp-planning-guide` and `mcp-bootstrap` requests to starter + smoke collections]
- TODO(P4-DX-POSTMAN): Extend Postman starter and smoke collections to include `mcp-manifest/effective` checks for runtime availability visibility in client validation loops. [DONE-hardening: added effective-manifest requests to starter + smoke collections]
- TODO(P4-DX-OPS): Add machine-readable hardware readiness endpoint so operators can see whether real telescope is required now and what trigger task starts HIL checks. [DONE-hardening: added `GET /telescopes/hardware/readiness` + integration test]
- TODO(P4-DX-POSTMAN): Add `hardware/readiness` endpoint coverage to starter and smoke Postman collections so Seestar trigger visibility is part of routine validation. [DONE-hardening: added hardware readiness request + smoke assertions for trigger task]
- TODO(P4-MCP-TOOLS): Include `hardware_readiness` inside MCP bootstrap payload so tool clients can initialize readiness and trigger-task context in one request. [DONE-hardening: `/telescopes/tools/mcp-bootstrap` now includes `hardware_readiness`]
- TODO(P4-MCP-TOOLS): Add runtime-safe MCP execution-plan endpoint that maps recommended tool order and capability-gated command steps for backend-side orchestration. [DONE-hardening: added `GET /telescopes/tools/mcp-execution-plan` with integration fallback coverage]
- TODO(P4-DX-POSTMAN): Extend Postman starter/smoke collections with `mcp-execution-plan` request and contract assertions for `steps` and `skip_reason` fields. [DONE-hardening: added starter + smoke coverage for `GET /telescopes/tools/mcp-execution-plan`]
- TODO(P4-MCP-TOOLS): Support execution-plan mode profiles (`async` polling vs `sync` enqueue-and-wait) so MCP clients can request orchestration shape explicitly. [DONE-hardening: `GET /telescopes/tools/mcp-execution-plan?mode=async|sync` with integration coverage]
- TODO(P4-DX-POSTMAN): Add `mcp-execution-plan?mode=sync` smoke coverage to lock single-call inference flow contract in collection runner checks. [DONE-hardening: added starter request and smoke assertions for sync execution-plan mode]
- TODO(P4-MCP-TOOLS): Add `include_disabled_commands` execution-plan filter so clients can request a pre-filtered runnable command sequence from capability-gated plans. [DONE-hardening: `GET /telescopes/tools/mcp-execution-plan?include_disabled_commands=false` with integration coverage]
- TODO(P4-DX-POSTMAN): Add runnable-only execution-plan smoke coverage (`include_disabled_commands=false`) to lock filtered command-step behavior in collection runner checks. [DONE-hardening: added starter request and smoke assertions for runnable command filtering]
- TODO(P4-MCP-TOOLS): Include `applied_filters` in execution-plan response so clients can confirm active filtering knobs from API payload alone. [DONE-hardening: `mcp-execution-plan` now returns `applied_filters.include_disabled_commands`]
- TODO(P4-DX-POSTMAN): Add smoke assertions for `mcp-execution-plan` `applied_filters` contract so default and runnable-only filter states are validated in collection runs. [DONE-hardening: smoke checks now assert `applied_filters.include_disabled_commands` for both default and filtered requests]
- TODO(P4-MCP-TOOLS): Include execution-plan `stats` (`baseline_steps`, `returned_steps`) so clients can detect how strongly filters altered orchestration output. [DONE-hardening: `mcp-execution-plan` now returns `stats.baseline_steps/returned_steps` with integration assertions]
- TODO(P4-DX-POSTMAN): Add smoke assertions for execution-plan `stats` so filtered/unfiltered step-count behavior is validated in collection runner flows. [DONE-hardening: smoke checks now assert `stats.baseline_steps`/`stats.returned_steps` for default and filtered requests]
- TODO(P4-MCP-TOOLS): Add `stats.filtered_out_steps` in execution-plan response so clients can consume filter impact as a direct scalar metric. [DONE-hardening: `mcp-execution-plan` now returns `stats.filtered_out_steps` with integration assertions]
- TODO(P4-DX-POSTMAN): Add smoke assertions for execution-plan `stats.filtered_out_steps` so direct filter-impact metric stays locked in Postman runner regressions. [DONE-hardening: smoke checks now assert `stats.filtered_out_steps` for both default and runnable-only execution-plan requests]
- TODO(P4-DX-OPS): Add machine-readable hardware smoke plan endpoint so operators and MCP clients can fetch the exact P5-HW-SMOKE checklist before connecting Seestar. [DONE-hardening: added `GET /telescopes/hardware/smoke-plan` with integration test and README docs]
- TODO(P4-MCP-TOOLS): Include `hardware_smoke_plan` in MCP bootstrap so agents can initialize real-hardware checklist context in the same call as readiness and manifests. [DONE-hardening: `/telescopes/tools/mcp-bootstrap` now returns `hardware_smoke_plan` with integration assertions]
- TODO(P4-DX-POSTMAN): Extend starter/smoke Postman collections for `hardware/smoke-plan` and bootstrap `hardware_smoke_plan` assertions to keep Seestar preflight contract stable in runner checks. [DONE-hardening: added starter endpoint, smoke request, and bootstrap payload assertions for `hardware_smoke_plan`]
- TODO(P4-MCP-TOOLS): Include `hardware_smoke_plan` in `mcp-execution-plan` so agents can fetch orchestration steps and real-hardware preflight checklist in one response. [DONE-hardening: `/telescopes/tools/mcp-execution-plan` now returns `hardware_smoke_plan` with integration assertions]
- TODO(P4-DX-POSTMAN): Add `mcp-execution-plan` smoke assertions for `hardware_smoke_plan` so preflight checklist contract is locked in default and sync runner flows. [DONE-hardening: smoke checks now assert `hardware_smoke_plan` for default and sync execution-plan requests]
- TODO(P4-DX-POSTMAN): Extend `mcp-execution-plan` `hardware_smoke_plan` smoke assertions to runnable-only mode so all execution-plan variants lock the same preflight contract. [DONE-hardening: smoke checks now assert `hardware_smoke_plan` for default, sync, and runnable execution-plan requests]
- TODO(P4-DX-POSTMAN): Assert `hardware_smoke_plan.steps[*]` schema fields (`step`, `action`, `expected_result`) in smoke flows so Seestar preflight step contracts remain stable. [DONE-hardening: smoke checks now assert step-level fields in bootstrap-linked and direct hardware smoke-plan responses]
- TODO(P4-DX-POSTMAN): Assert `hardware_smoke_plan.steps[*]` schema fields in `mcp-execution-plan` smoke flows (default/sync/runnable) so execution-plan variants also lock step-level preflight structure. [DONE-hardening: smoke checks now assert `step`/`action`/`expected_result` in execution-plan hardware smoke payloads for all supported modes]
- TODO(P4-DX-OPS): Add `schema_version` to hardware readiness/smoke-plan contracts so machine-readable payloads can evolve without ambiguous client parsing. [DONE-hardening: `hardware/readiness` and `hardware/smoke-plan` now return `schema_version=v1` with integration and smoke assertions]
- TODO(P4-DX-OPS): Add a local CLI dry-run for `P5-HW-SMOKE` preflight to validate readiness/plan/status/capabilities/audit flow and persist machine-readable check results. [DONE-hardening: added `backend/scripts/hardware_smoke_runner.py`, `make hardware-smoke-dry-run`, and README guidance]
- TODO(P4-DX-OPS): Extend local CLI dry-run to verify MCP aggregate payloads contain both hardware checklists so preflight tools catch bootstrap/execution regressions early. [DONE-hardening: runner now validates `mcp-bootstrap` and `mcp-execution-plan` checklist contracts in dry-run flows]
- TODO(P4-DX-OPS): Add unit tests for hardware smoke CLI runner to lock contract validators and strict failure exit behavior for CI-safe maintenance. [DONE-hardening: added `tests/unit/test_hardware_smoke_runner.py` coverage for validators, check error mapping, and strict exit code]
- TODO(P4-DX-OPS): Add machine-readable `P5-HW-VALIDATION` checklist endpoint and Postman coverage so safety-validation steps are available before live hardware phase starts. [DONE-hardening: added `GET /telescopes/hardware/validation-plan`, integration test, starter/smoke Postman requests, and README docs]
- TODO(P4-MCP-TOOLS): Include `hardware_validation_plan` in MCP bootstrap/execution-plan payloads so MCP clients can consume both P5 checklists without extra round-trips. [DONE-hardening: `mcp-bootstrap` and `mcp-execution-plan` now return `hardware_validation_plan` with integration and smoke assertions]
- TODO(P4-DX-OPS): Add hardware overview endpoint that aggregates readiness + smoke/validation plans so operators can fetch all P5 preflight context in one request. [DONE-hardening: added `GET /telescopes/hardware/overview` with integration test, starter/smoke Postman coverage, and README docs]
- TODO(P4-DX-OPS): Extend local CLI dry-run to validate `hardware/overview` aggregate contract so one-call preflight payload regressions are caught before P5 runs. [DONE-hardening: runner now checks `hardware.overview` and unit tests lock the validator contract]
- TODO(P4-DX-OPS): Run hardware dry-run Make targets with host UID/GID mapping so generated `artifacts/*.json` reports do not become root-owned and block local cleanup. [DONE-hardening: targets now pre-clean stale report files and execute runner with host UID/GID via Docker `--user $(id -u):$(id -g)`]
- TODO(P4-MCP-TOOLS): Include `hardware_overview` in MCP bootstrap/execution-plan payloads so clients can consume both granular and one-call hardware preflight contracts without extra endpoint fetches. [DONE-hardening: `mcp-bootstrap` and `mcp-execution-plan` now return `hardware_overview` with integration and smoke assertions]
- TODO(P4-DX-OPS): Extend CLI MCP aggregate validators to assert nested `hardware_overview` contract so dry-run preflight catches one-call bundle regressions beyond top-level trigger IDs. [DONE-hardening: `hardware_smoke_runner.py` now validates `hardware_overview` inside both `mcp-bootstrap` and `mcp-execution-plan` with unit coverage]
- TODO(P4-DX-POSTMAN): Add step-level smoke assertions for nested `hardware_overview` in MCP bootstrap/execution-plan variants so one-call bundle schema regressions are caught in runner flows. [DONE-hardening: smoke + integration checks now validate `hardware_overview` trigger IDs and step fields/length in bootstrap and execution-plan payloads]
- TODO(P4-DX-OPS): Assert trigger consistency between top-level MCP checklist fields and nested `hardware_overview` payload so aggregate responses cannot silently drift across duplicated contracts. [DONE-hardening: dry-run CLI now cross-checks trigger IDs between top-level plans and `hardware_overview` with mismatch-focused unit tests]
- TODO(P4-DX-OPS): Add integration consistency test that `hardware/overview` matches individual readiness/smoke/validation endpoints to prevent drift between aggregate and source contracts. [DONE-hardening: `test_hardware_overview_endpoint.py` now compares overview payload sections against direct endpoint responses]
- TODO(P4-DX-OPS): Add optional markdown notes output for dry-run CLI so operators can save a human-readable preflight handoff summary alongside JSON reports. [DONE-hardening: `hardware_smoke_runner.py` now supports `--notes-path` and unit coverage for generated notes content]
- TODO(P4-DX-OPS): Add Make shortcuts that generate both JSON report and markdown handoff notes for smoke/validation dry-runs to reduce operator CLI flag overhead. [DONE-hardening: added `hardware-smoke-dry-run-with-notes` and `hardware-validation-dry-run-with-notes` targets with artifact pre-clean and UID/GID-safe output]
- TODO(P4-DX-OPS): Add a single bundled Make target that runs both note-producing smoke and validation dry-runs in one command for faster operator loops. [DONE-hardening: added `hardware-preflight-dry-run-with-notes` chaining smoke+validation notes targets]
- TODO(P4-DX-OPS): Add a single bundled Make target that runs both JSON-only smoke and validation dry-runs so operators can capture baseline reports without notes in one command. [DONE-hardening: added `hardware-preflight-dry-run` chaining JSON-only smoke+validation targets]
- TODO(P4-DX-OPS): Gate CLI command-check execution by hardware readiness to prevent accidental live command calls before the explicit Seestar trigger phase. [DONE-hardening: `hardware_smoke_runner.py` now blocks `--include-commands` when readiness is false unless explicit `--allow-command-checks-when-not-ready` override is set, with unit coverage]

## Phase 6+ Candidate Backlog (Post-Frontend / v2.0)

- TODO(P6-WEATHER-MCP): Add provider-agnostic weather integration (OpenWeather or alternative) and inject weather context into MCP planning payloads.
- TODO(P6-WEATHER-SAFETY): Use weather signals (clouds, wind, humidity, visibility, precipitation risk) as advisory guardrails for AI telescope recommendations before command dispatch.

## Phase 5 Hardware Gate (Seestar Trigger)

> **Operator trigger:** before starting tasks in this section, charge and prepare the real telescope (`Seestar S30 Pro`) for live LAN validation.
> **Requires physical Seestar:** `P5-HW-SMOKE`, `P5-HW-VALIDATION`, and the live Make targets (`make hardware-smoke-live-run`, `make hardware-validation-live-run`) only make sense with the S30 Pro powered, joined to your LAN with a stable reserved IP, and Alpaca reachable on port **32323** (see `backend/README.md` if connectivity flakes). Purely software tasks elsewhere in `TASKS.md` do not need the mount on the bench.

- TODO(P5-HW-SMOKE-PREP): Add dedicated Make entrypoint for command-inclusive live smoke run so operators can execute P5-HW-SMOKE with one standard command and consistent artifacts. [DONE-prep: added `make hardware-smoke-live-run` with command checks, token passthrough, and report/notes outputs]
- TODO(P5-HW-VALIDATION-LIVE-PREP): Add matching Make entrypoint for command-inclusive validation live runs so operators can capture `P5-HW-VALIDATION` artifacts symmetrically after smoke baseline. [DONE-prep: added `make hardware-validation-live-run` plus validation-aware markdown follow-up wording in `hardware_smoke_runner.py`]
- TODO(P5-HW-DOCKER-ALPACA-ENV): Pass Alpaca, command-auth, Kafka topic, catalog, and ephemeris settings from host `.env` into the `main-app` Compose service so containerized runs match local hardware configuration. [DONE-dx: `app.yaml` and `app.dev.yaml` now forward the relevant variables with safe defaults]
- TODO(P5-HW-COMMAND-AUTH-BLANK): Treat a blank or whitespace-only `COMMAND_AUTH_TOKEN` as “auth disabled” so operators are not surprised by `401` when `.env` contains an empty assignment. [DONE-dx: `_require_command_auth` returns early when the configured token is empty after strip]
- TODO(P5-HW-DX-SEESTAR-NET): Document Seestar LAN IP drift and stale Linux ARP behavior for operators hitting Alpaca timeouts despite a “known good” IP string. [DONE-dx: `backend/README.md` troubleshooting section with `ip neigh` / flush / DHCP reservation guidance]
- TODO(P5-HW-DX-ALPACA-LAN-PROBE): Add read-only LAN probe (Alpaca `management/v1/configureddevices`) and Make wrapper so operators can verify reachability before live smoke without sending motion commands. [DONE-dx: `backend/scripts/alpaca_lan_probe.py`, `make alpaca-lan-probe`, unit tests]
- TODO(P5-HW-DX-README-OPERATOR-SEQUENCE): Document ordered Seestar LAN steps (probe → dry-run → live smoke → validation) so operators do not skip read-only checks. [DONE-dx: `backend/README.md` subsection «Seestar S30 Pro on LAN — suggested operator sequence»; `docs/PLAN.md` note distinguishing TASKS HIL gate vs UI Phase 5]
- TODO(P5-HW-DX-BASELINE-HANDOFF): Provide a short Markdown template operators can reuse to capture Phase 5 live smoke / validation qualitative notes alongside CLI JSON artifacts. [DONE-dx: `docs/hardware/p5_hw_smoke_baseline_template.md` mirrors `P5-HW-SMOKE`/`hardware-smoke-live-run` artifact intent; duplicate or trim before committing any LAN-sensitive content]
- TODO(P5-HW-STATUS-CONNECTION): Align REST `connection_state` with Alpaca live `Connected` when live polling succeeds so MCP and operators see the same linkage story as `alpaca_live`. [DONE-dx: `GetTelescopeStatusQueryHandler` overlays `connected`/`disconnected` from the live snapshot while Alpaca probing is enabled; unreachable Alpaca clears the surfaced state to `disconnected`; unit coverage in `tests/unit/test_telescope_status_capabilities.py`]
- TODO(P5-HW-STATUS-TRACKING): Align REST `tracking_enabled` with live Alpaca `Tracking` when the scope is connected so status matches driver reality. [DONE-dx: `GetTelescopeStatusQueryHandler` uses live tracking when reachable+connected; forces false when reachable but not connected; preserves Mongo value when Alpaca is off or unreachable; unit coverage alongside connection_state tests]
- TODO(P5-HW-SMOKE-RUNNER-STATUS-LIVE): Extend hardware smoke/validation/live CLI checks so `/telescopes/status` cross-fields stay consistent whenever `alpaca_live` is present (same contract operators see vs JSON tools). [DONE-dx: `hardware_smoke_runner._assert_status` requires `tracking_enabled` and asserts connection/tracking overlay rules when `alpaca_live.reachable` / `connected` / `tracking` are known; rules live in shared `backend/scripts/telescope_status_contract.py` with `tests/unit/test_telescope_status_contract.py` and integration payloads revalidated against the same contract]
- TODO(P4-DX-POSTMAN): Mirror `/telescopes/status` overlay invariants (vs `alpaca_live`) in the Newman smoke collection so CLI and Postman preflight regressions surface together when Alpaca probing is enabled. [DONE-postman-smoke: `alpaca-astro-center.smoke.postman_collection.json` telescope-status step asserts `tracking_enabled` plus conditional alignment with `alpaca_live`, parity with `backend/scripts/telescope_status_contract.py`]
- TODO(P4-TEST-STATUS-WIRING): Add FastAPI integration coverage for `GET /telescopes/status` wired through `Mediator` plus `GetTelescopeStatusQueryHandler` with mocked Alpaca so schema + overlay behavior stay pinned beyond unit-level handler tests. [DONE: `tests/integration/test_telescope_status_endpoint.py` covers live-connected overlay plus no-live-probe persisted fields, unreachable-Alpaca connection reset, and reachable-but-not-connected tracking behavior through the REST stack]
- TODO(P5-HW-SMOKE): Run first hardware-in-the-loop Alpaca smoke checks (`status/capabilities/slew/sync/tracking`) against Seestar on local network and capture baseline behavior notes. [PARTIAL-2026-05-09: `GET /telescopes/status` shows `alpaca_live` reachable with slew/sync/tracking capability flags; full command-inclusive smoke run + filed narrative notes still open—use `docs/hardware/p5_hw_smoke_baseline_template.md` plus `artifacts/hardware-smoke-live-run.{json,md}`]
- TODO(P5-HW-VALIDATION): Validate command safety path on real hardware (auth guard, capability gating, audit trail writes) and document any hardware-specific constraints.
