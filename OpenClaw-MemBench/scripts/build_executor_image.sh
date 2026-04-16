#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

IMAGE_NAME="${1:-openclaw-membench-executor:latest}"

docker build -f docker/Dockerfile.executor -t "$IMAGE_NAME" .
echo "Built image: $IMAGE_NAME"
