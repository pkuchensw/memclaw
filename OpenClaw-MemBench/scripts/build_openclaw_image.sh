#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Default values
IMAGE_NAME="${1:-openclaw-membench:latest}"
DOCKERFILE="${2:-docker/Dockerfile.standalone}"

echo "========================================="
echo "Building OpenClaw-MemBench Docker Image"
echo "========================================="
echo "Image name: $IMAGE_NAME"
echo "Dockerfile: $DOCKERFILE"
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if docker daemon is running
if ! docker info &> /dev/null; then
    echo "Error: Docker daemon is not running"
    exit 1
fi

# Build the image
echo "Building Docker image..."
docker build \
  -f "$DOCKERFILE" \
  -t "$IMAGE_NAME" \
  .

echo ""
echo "========================================="
echo "Build completed successfully!"
echo "Image: $IMAGE_NAME"
echo "========================================="
echo ""
echo "To verify the installation, run:"
echo "  docker run --rm $IMAGE_NAME openclaw --version"
echo ""
echo "To run a benchmark task, use:"
echo "  bash scripts/run_openclaw_docker.sh <category> <max_tasks> <output>"
