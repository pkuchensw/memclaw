#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DOCKER_IMAGE="${OPENCLAW_DOCKER_IMAGE:-openclaw-membench:latest}"

echo "========================================="
echo "OpenClaw-MemBench Docker Setup Test"
echo "========================================="
echo ""

# Test 1: Check Docker is running
echo "[Test 1/6] Checking Docker daemon..."
if ! docker info > /dev/null 2>&1; then
    echo "✗ FAIL: Docker daemon is not running"
    exit 1
fi
echo "✓ Docker daemon is running"
echo ""

# Test 2: Check if image exists
echo "[Test 2/6] Checking Docker image: $DOCKER_IMAGE"
if ! docker image inspect "$DOCKER_IMAGE" > /dev/null 2>&1; then
    echo "✗ Image not found. Building..."
    bash scripts/build_openclaw_image.sh "$DOCKER_IMAGE"
else
    echo "✓ Docker image exists"
fi
echo ""

# Test 3: Test OpenClaw CLI inside container
echo "[Test 3/6] Testing OpenClaw CLI inside container..."
if ! docker run --rm "$DOCKER_IMAGE" openclaw --version; then
    echo "✗ FAIL: OpenClaw CLI test failed"
    exit 1
fi
echo "✓ OpenClaw CLI works"
echo ""

# Test 4: Test Python environment
echo "[Test 4/6] Testing Python environment..."
if ! docker run --rm "$DOCKER_IMAGE" python3 -c "import yaml, rich, dotenv, requests; print('Python OK')"; then
    echo "✗ FAIL: Python environment test failed"
    exit 1
fi
echo "✓ Python environment OK"
echo ""

# Test 5: Test dry-run (if project files are available)
echo "[Test 5/6] Testing task parsing (dry-run)..."
if [ -f "eval/run_batch.py" ]; then
    python3 eval/run_batch.py --dry-run --max-tasks 1 > /dev/null 2>&1 && echo "✓ Task parsing works" || echo "⚠ Task parsing failed (check Python dependencies)"
else
    echo "⚠ Skipped (run_batch.py not found)"
fi
echo ""

# Test 6: Check API configuration
echo "[Test 6/6] Checking API configuration..."
if [ -f ".env" ]; then
    if grep -q "OPENCLAW_API_KEY=" .env && ! grep -q "OPENCLAW_API_KEY=your-api-key" .env; then
        echo "✓ API key is configured"
    else
        echo "⚠ API key not configured or using default value"
        echo "  Please edit .env and set your API key"
    fi
else
    echo "⚠ .env file not found"
    echo "  Please create .env from .env.example"
fi
echo ""

echo "========================================="
echo "Docker setup test completed!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Ensure your .env file has valid API credentials"
echo "  2. Run a smoke test:"
echo "     bash scripts/run_openclaw_docker.sh 01_Recent_Constraint_Tracking 1"
echo ""
