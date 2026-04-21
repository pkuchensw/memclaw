# Workspace for Task 02: PDF Selective Extraction

Capability target: Recent Constraint Tracking.

This task validates whether the agent can keep the newest allowlist + schema constraints while handling noise/interruption.

Required outputs in results/:
- paper_digest.json
- paper_digest.csv
- result.json
- summary.md
- manifest.csv

Key checks:
- only allowlist PDFs are processed
- schema has no extra fields
- JSON/CSV row parity is preserved
