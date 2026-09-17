# Bybit read-only adapter

## Current implementation

`BybitOrderbookDataSource` is the first provider adapter implemented behind the project `ReadOnlyDataSource` boundary. It reads only Bybit's public V5 REST Orderbook endpoint and normalizes a single response into `NormalizedSnapshot`.

The adapter intentionally exposes no order, execution, position, leverage, sizing, wallet, or private-account method.

## Verified behaviors in this batch

- public endpoint path: `/v5/market/orderbook`;
- documented Bybit categories: `spot`, `linear`, `inverse`, `option`;
- documented orderbook limits are enforced at construction;
- response symbol, timestamps, update ID, cross sequence, and bid/ask schema are validated;
- bid and ask ordering is checked against the documented ordering;
- system and matching-engine timestamps are preserved as UTC metadata;
- `as_of` rejects responses received after the point-in-time boundary;
- transport, JSON, schema, provider, and rate-limit failures become explicit non-VALID quality states;
- rate-limit code `10006` is classified as `rate_limited`;
- transport is injectable for deterministic tests;
- no execution methods are present.

## Activation status

Implementation does **not** mean production activation. Registry/source status remains separate from this code path. Live endpoint availability, timeout/rate-limit behavior against the real service, reconnect/operational behavior, controlled-environment evidence, and production-readiness acceptance are still required before activation.

## Evidence

The adapter's schema/provenance references the official Bybit documentation repository snapshot `75994fda16e052aaad6e3fade82fd1f6fd90288e`, specifically the V5 Orderbook documentation.
