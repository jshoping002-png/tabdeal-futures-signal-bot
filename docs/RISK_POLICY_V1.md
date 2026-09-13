# Risk Policy V1 — Signal Safety Only

## Status

DESIGNED — explicit signal-safety policy for Phase 9.

## Objective

The Risk Gate is a delivery-safety boundary for already-qualified strategy signals. It does not manage financial exposure and does not execute trades.

## Policy

A side is risk-eligible only when the upstream decision is already `SIGNAL` and the decision context is valid under the existing domain contract.

Risk V1 adds **no financial risk thresholds**. It does not define leverage, risk percentage, liquidation distance, stop-loss, take-profit, funding limits, position sizing, confidence, or score.

Risk V1 adds **no market-state limits** and **no symbol-specific or timeframe-specific restrictions**. The strategy contract remains the authority for the supported 4H/1H/15m decision structure.

## Mandatory block conditions

The Risk Gate must not permit a signal when:

1. the supplied decision context is invalid;
2. the side decision is not a valid `SideDecision`;
3. the side decision is already `BLOCKED` (the existing gate preserves the upstream block);
4. a future or otherwise invalid temporal boundary is detected by the existing context contract;
5. required upstream point-in-time/data validation is absent or invalid.

Existing `DecisionContext` and `MarketSnapshot` contracts already enforce UTC, snapshot identity, reference-time ordering, closed-candle availability, deterministic ordering, and basic candle validity. Risk V1 does not duplicate financial/data rules that belong to earlier pipeline boundaries.

## Stale data

Risk V1 treats stale or incomplete market state as ineligible when the upstream snapshot cannot prove point-in-time availability or cannot supply the data required by the strategy. Risk V1 does not invent a wall-clock freshness threshold.

## Configuration

`DecisionContext.config_version` identifies the deterministic configuration used for the decision. An empty or invalid configuration version is invalid under the existing domain contract and therefore cannot produce a permitted signal.

Risk policy behavior is versioned as **Risk Policy V1**. A future policy revision must be introduced as a new explicit contract rather than silently changing V1 semantics.

## Determinism

For the same valid context and side decision, Risk V1 always returns the same result and reason code. No clock, randomness, external state, or fallback is consulted.

## Reason codes

- `RISK_POLICY_ACCEPTED`
- `RISK_POLICY_INVALID_CONTEXT`
- `RISK_POLICY_INVALID_DECISION`
- `RISK_POLICY_UPSTREAM_BLOCKED`

## Explicit non-goals

- exchange order execution;
- automatic buy/sell;
- position opening/closing;
- leverage management;
- stop-loss/take-profit calculation;
- liquidation management;
- funding-rate filtering;
- position sizing;
- score/confidence filtering.

## Acceptance

Implementation requires unit, boundary, failure, determinism, and regression coverage. CI must pass before promotion to the next logical phase.
