#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CATEGORY="${1:-01_Recent_Constraint_Tracking}"
MAX_TASKS="${2:-1}"
OUTPUT="${3:-outputs/openclaw_docker_summary.json}"

python eval/run_batch.py \
  --runtime openclaw-docker \
  --category "$CATEGORY" \
  --max-tasks "$MAX_TASKS" \
  --output "$OUTPUT"
