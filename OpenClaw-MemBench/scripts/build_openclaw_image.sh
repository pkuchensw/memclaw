#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

IMAGE_NAME="${1:-openclaw-membench-openclaw:latest}"
BASE_IMAGE="${2:-wildclawbench-ubuntu:v0.4}"

docker build \
  -f docker/Dockerfile.openclaw \
  --build-arg BASE_IMAGE="$BASE_IMAGE" \
  -t "$IMAGE_NAME" \
  .

echo "Built OpenClaw image: $IMAGE_NAME (base=$BASE_IMAGE)"
