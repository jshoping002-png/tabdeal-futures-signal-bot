# Notification Provider Contract V1

## Status

DESIGNED — Notification Delivery boundary following Phase 12 Outbox / Notification Intent.

## Objective

Define the technology-neutral boundary between the delivery worker and an external notification provider without coupling decision logic or Outbox storage to a transport.

## Input

The provider receives one `NotificationRequest` containing exactly one immutable `OutboxMessage`. Provider adapters MUST preserve the event identity and notification intent supplied by the request.

## Result

The provider returns the existing transport-neutral `NotificationResult` with one explicit outcome:

- `DELIVERED` — provider accepted the notification as delivered;
- `DUPLICATE` — provider establishes that the logical notification was already delivered;
- `RETRYABLE` — delivery did not complete and may be attempted again only under the separately defined retry policy;
- `BLOCKED` — delivery must not be treated as successful and must not be retried unless a future explicit policy permits it.

The provider MUST NOT invent a new outcome at the provider boundary.

## Identity and duplicate safety

Provider delivery MUST use the logical event/idempotency identity supplied by the Outbox message. A provider adapter MUST NOT create a second logical notification because a worker or provider call is repeated.

Provider-specific delivery identifiers may be retained as transport metadata only; they MUST NOT replace the system's logical event identity.

## Failure-closed behavior

Malformed requests, missing required provider configuration, unavailable transport, ambiguous delivery state, or unverified provider responses MUST NOT be reported as `DELIVERED`.

Provider adapters MUST NOT modify the decision, direction, reason code, snapshot identity, or signal identity.

## Security

Provider credentials are runtime configuration/secrets only. They MUST NOT be committed to Git, embedded in fixtures, or emitted in logs, snapshots, exception text, or persisted decision data.

## Telegram boundary

Telegram is a provider adapter under this contract. Its API method, authentication mechanism, chat configuration, rate limits, formatting, timeout values, and provider-specific error mapping require an explicit Telegram/provider implementation contract before implementation. No Telegram-specific behavior is inferred here.

## Retry boundary

This contract does not define retry counts, backoff, scheduling, or lease duration. Those belong to `RETRY_POLICY_CONTRACT_V1.md` and the delivery worker.

## Non-goals

- strategy or risk decisions;
- Outbox persistence or schema;
- database selection;
- queue/broker selection;
- exchange order execution or auto-trading.

## Acceptance

Provider adapters require contract tests for identity preservation, outcome mapping, duplicate safety, malformed configuration, failure-closed behavior, and secret/log safety before production use.
