# Read-Only Data Adapter Implementation Plan

This plan covers the first real provider adapter for the signal-generation system. It does **not** authorize order submission, trading, position management, or exchange execution.

## Scope

The first adapter must implement only the `ReadOnlyDataSource` contract and return a `NormalizedSnapshot`. It may read public market or reference data, but it must not expose trading capabilities.

## Required behavior

1. **Read-only boundary**
   - Expose `fetch_snapshot(as_of=None)` only.
   - Do not implement `place_order`, `execute_trade`, `cancel_order`, or position-management methods.

2. **Time and replay semantics**
   - Preserve `observed_at`, `received_at`, `effective_at`, and `available_at` when known.
   - Reject naive timestamps.
   - Never use data that was unavailable after the decision time in point-in-time evaluation.
   - Keep raw payloads separate from normalized values.

3. **Quality handling**
   - Normalize provider failures into explicit quality states such as `UNAVAILABLE`, `STALE`, `INCOMPLETE`, `GAPPED`, or `INVALID`.
   - Do not silently convert missing or stale data into valid data.
   - Preserve provider and schema provenance.

4. **Operational behavior**
   - Apply bounded timeouts.
   - Classify rate-limit, timeout, transport, schema, and authentication failures separately.
   - Avoid logging tokens, credentials, or authorization headers.
   - Make retry behavior explicit and bounded; retries must not create duplicate decisions.

5. **Determinism and testing**
   - Support injected clock/time and transport dependencies.
   - Test successful normalization, malformed payloads, missing fields, stale data, gaps, provider errors, rate limits, and deterministic replay.
   - Test that the adapter has no order-execution surface.

## Acceptance evidence

The adapter is not production-ready until the repository contains tests and controlled-environment evidence for:

- successful reads and normalization;
- timeout and rate-limit behavior;
- stale, incomplete, gapped, and invalid data;
- point-in-time filtering;
- replay determinism;
- bounded retries and failure classification;
- secret-free logs;
- restart and deployment behavior.

## Implementation order

1. Define provider-neutral error and response envelopes.
2. Define an injectable read-only transport boundary.
3. Implement one provider adapter behind that boundary.
4. Add deterministic fixtures and contract tests.
5. Add freshness, gap, and point-in-time validators.
6. Add operational metrics and structured audit fields.
7. Validate in a controlled environment before changing the production-readiness checklist.

## Safety boundary

This adapter is strictly for data ingestion and normalization. The project must remain limited to signal generation, validation, persistence, risk evaluation, and notification delivery. No trading endpoint or order-execution path may be added.
