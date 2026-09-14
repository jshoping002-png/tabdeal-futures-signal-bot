# Queue / Broker Boundary

## Status

DESIGNED — optional infrastructure boundary; no queue/broker technology is selected.

## Objective

Define the boundary that applies if the production delivery architecture introduces asynchronous queue/broker transport. This document does not require a broker where the Outbox + worker model is sufficient.

## Architectural position

The queue/broker, when used, sits between durable Outbox state and a delivery worker. It is transport infrastructure, not part of decision, strategy, risk, persistence semantics, or notification-provider semantics.

`Decision → Persistence/Outbox → Queue/Broker (optional) → Delivery Worker → Notification Provider`

## Required guarantees

If introduced, the queue/broker integration MUST preserve:

- the Outbox event identity and logical idempotency key;
- at-least-once-safe processing through idempotent delivery;
- compatibility with exclusive lease ownership;
- restart safety;
- no loss of a durably persisted notification intent because of transient transport failure;
- fail-closed behavior when delivery ownership or message identity cannot be established.

The integration MUST NOT make a second logical notification event from redelivery.

## Delivery semantics

Exact acknowledgement, visibility, consumer-group, ordering, retention, dead-letter, and timeout behavior are not selected here. They require an explicit implementation contract for the chosen technology.

A queue/broker MUST NOT be treated as the source of truth for logical decision persistence; durable Outbox state remains authoritative.

## Retry relationship

Queue redelivery and application retry are separate concerns. A queue's native redelivery behavior MUST NOT silently redefine the application's retry policy. The explicit retry contract remains authoritative.

## Security

Broker credentials and connection material are runtime secrets only and MUST NOT appear in source, fixtures, logs, or persisted business records.

## Non-goals

- mandatory broker deployment;
- vendor selection;
- queue configuration defaults;
- retry counts/backoff;
- notification-provider behavior;
- trading execution.

## Acceptance

A queue/broker implementation is optional. If selected, it requires integration tests for identity preservation, duplicate/redelivery safety, lease interaction, restart recovery, transport failure, and secret-safe logging before production activation.
