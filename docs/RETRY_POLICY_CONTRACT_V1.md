# Retry Policy Contract V1

## Status

DESIGNED — Reliability boundary for notification delivery.

## Objective

Define retry decisions independently from strategy, risk, persistence, and notification-provider code. This contract supplies the missing retry-policy boundary identified by the Outbox and provider contracts.

## Scope

Retry policy applies only to delivery attempts whose provider result is explicitly `RETRYABLE`. It does not turn `BLOCKED` or ambiguous outcomes into successful delivery.

## Required policy inputs

A policy evaluation MUST receive explicit delivery state sufficient to make a deterministic retry decision, including the current attempt state and the provider outcome. Any additional scheduling/age information must be explicitly supplied by the caller rather than inferred from wall-clock state.

## Policy output

The policy MUST return an explicit decision equivalent to one of:

- retry is permitted;
- retry is not permitted / terminal failure.

A future implementation may expose richer reason codes, but it MUST remain deterministic and explicit.

## Safety rules

- `DELIVERED` and `DUPLICATE` are terminal success outcomes and require no retry.
- `BLOCKED` is not retried by default.
- `RETRYABLE` is the only provider outcome eligible for retry evaluation.
- Missing, malformed, or ambiguous retry state fails closed to no retry.
- Retry evaluation must not alter the original decision or signal identity.
- Retry attempts must reuse the same logical notification identity and must remain idempotent.

## Backoff and limits

Retry count limits, backoff algorithm, delay values, jitter, maximum elapsed delivery window, and scheduling mechanism are intentionally not invented in V1. They MUST be selected explicitly before a production retry implementation is enabled.

## Restart and concurrency

A worker restart MUST NOT reset logical identity or permit duplicate logical notifications. Retry state must be compatible with the existing Outbox lease/ownership contract so a stale worker cannot perform an unauthorized state transition.

## Queue independence

The retry policy does not require a queue/broker. Scheduling may be performed by the delivery worker or a separately selected transport, but that choice requires its own infrastructure decision.

## Security

Retry logs and failure records MUST NOT contain provider credentials, authorization headers, tokens, or other secrets.

## Non-goals

- strategy/risk calculations;
- database vendor/schema;
- notification provider behavior;
- queue/broker technology;
- order execution or auto-trading.

## Acceptance

Before production activation, tests MUST cover outcome classification, fail-closed behavior, deterministic repeated evaluation, idempotent identity reuse, restart/concurrency interaction, and regression behavior. No production retry default is considered defined until the numeric/temporal policy values are explicitly approved.
