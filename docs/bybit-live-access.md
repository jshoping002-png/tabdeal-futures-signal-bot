# Bybit Live Access

## Purpose

This document defines the controlled path for a real, read-only connectivity check against the Bybit V5 public Kline API.

The probe is separate from normal deterministic CI. It performs an actual outbound HTTPS request to the public Bybit endpoint and therefore depends on external network availability.

## Command

After installing the package:

```bash
python scripts/bybit_live_probe.py \
  --symbol BTCUSDT \
  --category linear \
  --timeframe 60 \
  --limit 5 \
  --timeout 5
```

No API key, trading credential, account credential, order endpoint, or private endpoint is used.

## What a successful probe proves

A successful probe demonstrates that the execution environment can reach the Bybit public Kline endpoint, obtain an HTTP/JSON response, and validate the basic response envelope (success code, requested symbol/category and non-empty Kline list).

It does **not** by itself prove production readiness, PIT correctness for decision use, long-term availability, rate-limit capacity, reconnect behavior, historical completeness, or strategy authorization.

## GitHub Actions

The workflow `.github/workflows/bybit-live-probe.yml` is manually triggered with `workflow_dispatch`. It is intentionally not part of normal CI so deterministic unit tests do not depend on the live network.

## Operational status

The existence of this probe does not activate Bybit in the operational source registry. Production activation still requires the repository's source-level operational checks and explicit approval.
