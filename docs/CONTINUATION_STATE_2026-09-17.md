# Continuation State — 2026-09-17

## Purpose

This is a continuation/handoff record for the current engineering session. It is not a source-verification report and does not add, replace, or authorize any source.

## Repository state at handoff

- Repository: `jshoping002-png/tabdeal-futures-signal-bot`
- Branch: `main`
- Base HEAD before this record: `93b55a819da9556b0317ae51119aea0f60f554d0`
- Base commit message: `Make Bybit probe tests deterministic`
- The local working tree was previously verified clean.
- Normal CI on base SHA `93b55a819da9556b0317ae51119aea0f60f554d0` was GREEN (CI #586 / run `35266978732`).

## Project invariants

- The system is a deterministic, read-only signal/notification engine.
- No order placement/cancellation, position management, wallet/balance, leverage, sizing, SL/TP execution, transfers, private trading keys/endpoints, or auto-trading.
- Pipeline: `Source → Validation → PIT Snapshot → Series Integrity → Explicit Candle Alignment → Strategy Evaluation → LONG Isolation → SHORT Isolation → Conflict Gate → Risk Gate → Decision → Persistence → Outbox → Delivery Worker → Notification`.
- No guessing of undocumented provider behavior.
- PIT requires no data unavailable at/before `as_of`/reference time; timestamps must be timezone-aware UTC; closed candles only.
- Existing source reports 001–2040 are preserved. Their content/evidence is verified, but report verification is not equivalent to implementation or current live operational verification.
- Source lifecycle remains separate from readiness and explicit activation.

## Source catalog state

- Master registry: 29 source/families.
- Operational access catalog: 18 source families.
- All 18 operational families are currently `ADAPTER_BUILT`.
- Current counts: `ADAPTER_BUILT=18`, `LIVE_VERIFIED=0`, `PRODUCTION_READY=0`, `ACTIVE=0`.
- `strategy_authorized=False` and `trading_enabled=False`.
- For Bybit Futures Market Data, the next readiness gate is `LIVE_VERIFICATION` with blocker `live_operational_verification`.

## Bybit live-probe work completed

- A manual-only GitHub Actions workflow exists at `.github/workflows/bybit-live-probe.yml`.
- It uses only the public read-only Bybit V5 Kline endpoint and no credentials.
- Local probe was successfully executed by the user against `https://api.bybit.tr/v5/market/kline`.
- The successful local result had `ret_code=0`, 5 candle rows, 4 closed candles, and latest closed candle start `2026-09-17T20:00:00+00:00`.
- This proves successful access in the user's local environment, but does not by itself promote the source to `LIVE_VERIFIED`, `PRODUCTION_READY`, or `ACTIVE`.
- The manual GitHub workflow is not normal CI and does not persist operational verification evidence.
- CI #586 on SHA `93b55a819da9556b0317ae51119aea0f60f554d0` was GREEN after making probe tests deterministic.
- Two sequential correction commits were required for that fix (`f00a81f...` then `93b55a8...`). This was noted as a process deviation; do not create further correction commits unless required and revalidate fully.

## Architecture findings from the current investigation

- `docs/ARCHITECTURE.md` states that production readiness requires adapter implementation, integration tests, operational verification, and GREEN CI evidence.
- `docs/DATA_SOURCE_CONTRACT_V1.md` states that a provider is production-active only after endpoint, timestamp, availability, rate-limit, pagination, reconnect, symbol, timeframe, and failure semantics are explicitly verified.
- `MarketDataSource.snapshot(request) -> MarketSnapshot` is the core Phase 1 contract.
- `ingest()` is the fail-closed boundary and validates source identity, scope, and snapshot validation.
- `BybitKlineDataSource` directly implements `MarketDataSource`; no bridge from `NormalizedSnapshot` is required for Bybit Kline.
- Other source-family adapters may still use the separate `NormalizedSnapshot` boundary; do not generalize without inspection.

## Current Bybit Kline implementation under review

File: `src/tabdeal_signal/data_sources/bybit_kline.py`

Important current behavior:

- Adapter scope is exactly one symbol/category/timeframe.
- Uses documented Bybit V5 Kline path `/v5/market/kline`.
- Sends `end = int(reference_time.timestamp()*1000)` and `limit`.
- Requires timezone-aware UTC `reference_time`.
- Requires timezone-aware transport `received_at`.
- Rejects the response when `received_at > reference_time`.
- Validates `retCode`, result symbol/category, and list structure.
- Parses 7-string Kline fields.
- Derives `close_time` from the documented fixed-duration timeframe.
- Filters to `close_time < reference_time`.
- Rejects if no closed candle remains.
- Sorts candles deterministically and rejects duplicate open times.
- Requires contiguous candle series (`current.open_time == previous.close_time`).
- Produces immutable `MarketSnapshot` with deterministic `snapshot_id`.

## Important unresolved issue

The current implementation rejects any provider response received after `reference_time`:

`if received_at > reference_time: raise ValueError("provider response was received after reference_time")`

This must NOT be changed by assumption. The next investigation must determine the intended semantics from existing tests/contracts before deciding whether this is correct for live use, historical PIT use, or both.

A second item to verify is the exact closed-candle/timeframe contract around `_candle_close()` and the existing Bybit Kline tests. Do not infer provider timestamp semantics beyond official evidence.

## Last inspected documentation

- `docs/PRODUCTION_PERSISTENCE_CONTRACT_V1.md`: production persistence acceptance; not the Bybit live-verification contract.
- `docs/DATA_SOURCE_CONTRACT_V1.md`: authoritative Phase 1 source/ingestion boundary.
- `docs/ARCHITECTURE.md`: production readiness requires operational verification plus GREEN CI.
- `docs/source-operationalization-ledger-001-2040.md`: all 18 operational source families are `ADAPTER_BUILT`; none are live verified.
- `docs/source-verification-checkpoint-2040.md`: source verification history completed through 2040; next verification batch begins at 2041, but no new report should be created without explicit authorization.

## Exact next action

The next command that had been prepared but not yet executed is:

```bat
python -c "from pathlib import Path; import re; root=Path('tests'); [print(f'\n--- {p} ---') or print(p.read_text(encoding='utf-8')) for p in root.rglob('*.py') if re.search(r'BybitKlineDataSource|reference_time|closed candle|gapped candle|_candle_close', p.read_text(encoding='utf-8'), re.I)]"
```

Purpose: inspect existing tests before changing the `received_at > reference_time` behavior or any candle-time semantics.

## Resume rules

1. Start from the latest `main` SHA, not from an assumed local state.
2. Verify repository status and CI before making changes.
3. Continue from the unresolved Bybit Kline contract issue above.
4. Do not modify, add, delete, or replace source reports 001–2040.
5. Do not create report 2041+ unless explicitly authorized.
6. Do not promote any source lifecycle automatically.
7. Do not add trading/execution capability.
8. If a provider semantic is undocumented or cannot be proven, fail closed and leave it unresolved/runtime-configured rather than guessing.
9. For any code batch: inspect the whole batch, test it, correct before final commit where possible, then verify SHA/diff and CI on that exact SHA.
10. Keep runtime data and secrets out of Git.
