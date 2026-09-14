# CI quality gates

## Current baseline

The CI workflow currently installs the package and runs the test suite with `pytest -q`.

## Required gates before production use

The following checks should be added and made mandatory before treating the signal pipeline as production-ready:

1. **Syntax/import validation**
   - Compile the package and test sources.
   - Import the public package entry points.

2. **Lint and formatting**
   - Run a pinned formatter/linter configuration.
   - Fail on violations rather than reporting advisory output only.

3. **Static typing**
   - Run a pinned type checker against production modules and tests.
   - Define the accepted strictness level explicitly.

4. **Coverage**
   - Publish coverage for unit and integration tests.
   - Enforce a documented minimum threshold.
   - Include persistence, outbox lifecycle, worker, and replay paths.

5. **Security and dependency checks**
   - Pin or lock tool versions.
   - Scan dependencies and repository configuration.
   - Ensure secrets are never emitted in logs, fixtures, or notification payloads.

6. **Deterministic replay and recovery tests**
   - Verify no look-ahead/PIT invariants.
   - Verify idempotent persistence and event identity.
   - Verify lease expiry, retry, and dead-letter behavior.
   - Verify a retry never creates a second decision or outbox event.

7. **Operational integration tests**
   - Exercise the notification transport boundary with a fake or controlled endpoint.
   - Keep network I/O outside persistence transactions.
   - Verify failures are observable and isolated per event.

## Scope boundary

These gates apply only to signal generation, validation, persistence, risk evaluation, replayability, and notification delivery. They must not introduce order submission, exchange trading calls, or automatic trading behavior.

Until the required gates are implemented, executed, and reviewed, production readiness remains **NOT VERIFIED**.
