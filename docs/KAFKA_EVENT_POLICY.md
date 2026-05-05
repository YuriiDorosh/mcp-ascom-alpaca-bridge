# Kafka Event Policy

This document defines topic naming, schema/versioning expectations, and restart-safe consumer behavior for Alpaca Astro Center.

## Topic Naming Convention

Use lowercase kebab-case topic names with clear domain scope:

- `model-inference-request`
- `model-inference-result`
- `telescope-operation-events`

Rules:

- Keep topics stable; avoid renaming existing topics in-place.
- New bounded contexts should use `<domain>-<event-kind>` form.
- Environment variables mirror topic names in uppercase snake case (for example `TELESCOPE_OPERATION_TOPIC`).

## Event Schema and Compatibility Policy

Every emitted contract carries:

- `schema_version` (currently `v1`)
- `correlation_id` (for request/response tracing and dedupe grouping)

Compatibility rules:

- Additive fields are allowed in the same major schema version.
- Field removal or semantic changes require a new major version (for example `v2`) and dual-read migration period.
- Producers should not reuse or repurpose existing field names with different meanings.
- Consumers must ignore unknown fields when possible.

## Restart-Safe and Idempotent Consumer Strategy

Current baseline:

- Model inference result writes are idempotent by `request_id` (`update_one(..., upsert=True)`), so redelivered Kafka messages do not duplicate logical records.
- Telescope operation events use unique `event_id` and stable `correlation_id`.

Recommended strategy for telescope operation consumers (Phase 3+):

1. Persist a processed-event ledger keyed by `event_id`.
2. On consume:
   - check if `event_id` already processed,
   - if yes, skip side effects and commit offset,
   - if no, execute side effects and mark processed atomically.
3. Treat `correlation_id` as operation trace ID across retries and downstream logs.
4. Make side effects idempotent where possible (upserts, compare-and-set transitions, dedupe writes).
5. Commit offsets only after successful durable side effects.

## Error and Retry Guidance

- Transient infrastructure errors: retry with backoff.
- Permanent schema/validation errors: route to dead-letter handling and keep original payload.
- Consumer code should log `topic`, `event_id`, `correlation_id`, and `schema_version` for diagnostics.
