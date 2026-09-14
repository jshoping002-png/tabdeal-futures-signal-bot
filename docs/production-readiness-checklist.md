# Production Readiness Checklist

This checklist applies to the signal-generation and signal-notification system only. It does **not** authorize order submission, trading, or exchange execution.

## Verified in repository

- [x] Decision persistence contract is documented.
- [x] SQLite decision and signal-outbox persistence exists.
- [x] Idempotency collision handling is covered.
- [x] `BLOCKED` decisions do not create outbox records.
- [x] `SIGNAL` decisions create outbox records atomically with the decision.
- [x] Outbox lifecycle states are documented.
- [x] Claimed records have lease-based processing state.
- [x] Expired processing leases can be returned to `RETRY`.
- [x] `SENT` records are not reclaimed by the claim query.
- [x] Malformed claimed records can be quarantined when an internal row identifier exists.
- [x] Notification formatting is deterministic and secret-free.
- [x] CI executes compilation and the test suite.

## Not yet verified for production

- [ ] Durable production deployment and restart recovery have been exercised.
- [ ] Real transport delivery, timeout, retry, and dead-letter behavior have been exercised in an approved environment.
- [ ] Production metrics and alerting are collecting the required outbox signals.
- [ ] Structured logs and correlation identifiers are available in the deployed service.
- [ ] Backup, restore, and SQLite corruption-recovery procedures have been tested.
- [ ] Concurrency and multi-worker behavior have been tested under production-like load.
- [ ] Dependency locking and reproducible installation have been established.
- [ ] Security review of secrets handling and operational access is complete.
- [ ] End-to-end incident drills and rollback procedures have been completed.

## Release gate

The system must not be described as production-ready until the unchecked items above have evidence from a controlled environment. CI success alone is not sufficient evidence for operational readiness.

## Safety boundary

The repository must remain limited to signal generation, validation, persistence, risk evaluation, and notification delivery. It must not add order execution, position management, trading endpoints, or exchange execution paths.
