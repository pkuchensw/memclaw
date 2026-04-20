# Source Conflict Resolution Report: CSV vs Database Snapshot

## Executive Summary
Resolved temporal divergence between static CSV export and live database snapshot. Database snapshot (2024-01-20) accepted as authoritative; CSV (2024-01-15) flagged as historical baseline.

## Conflict Details
- **Entity**: user_count metric
- **CSV Claim**: 1,500 users (export date: 2024-01-15)
- **Database Claim**: 1,580 users (snapshot date: 2024-01-20)
- **Variance**: +80 users (+5.3%)

## Arbitration Methodology
Following OpenClaw conflict_arbitration skill:
1. **Recency Priority**: Database snapshot is 5 days newer
2. **Trust Calibration**: Runtime logs corroborate DB state
3. **Reject Stale Data**: CSV export does not capture intervening changes

## Evidence Priority Hierarchy
1. Runtime logs (executable, timestamped)
2. Database snapshots (runtime state, recoverable)
3. Static exports (potential staleness, reference only)

## Resolution
- **Authoritative Value**: 1,580 users (database snapshot)
- **Historical Reference**: 1,500 users (CSV export)
- **Confidence Level**: High (cross-validated)

## Determinism Notes
All timestamps in ISO 8601 UTC. Evidence table constructed per strict schema for machine verification.
