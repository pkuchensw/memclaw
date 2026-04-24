#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Show usage information
show_usage() {
    cat << EOF
Usage: bash scripts/run_openclaw_docker.sh [CATEGORY] [MAX_TASKS] [OUTPUT]

Run OpenClaw-MemBench benchmark tasks using Docker runtime.

Arguments:
  CATEGORY    Task category to run (default: 01_Recent_Constraint_Tracking)
              Available categories:
                - 01_Recent_Constraint_Tracking
                - 02_Version_Update
                - 03_Procedure_Transfer
                - 04_Repeated_Mistake_Prevention
                - 05_Source_Conflict_Resolution
                - 06_Memory_Operation_Selection
                - 07_Goal_Interruption_Resumption
                - 08_Staleness_Applicability_Judgment
  MAX_TASKS   Maximum number of tasks to run (default: 1)
  OUTPUT      Output file path (default: outputs/openclaw_docker_summary.json)

Environment Variables:
  OPENCLAW_RUNTIME          Runtime mode (default: openclaw-docker)
  OPENCLAW_DOCKER_IMAGE     Docker image to use (default: openclaw-membench:latest)
  OPENCLAW_MODEL            Model to use (default: from .env)
  OPENCLAW_API_KEY          API key for LLM provider (default: from .env)
  OPENCLAW_BASE_URL         Base URL for API (default: from .env)

Examples:
  # Run 1 task from category 01
  bash scripts/run_openclaw_docker.sh

  # Run 5 tasks from category 02
  bash scripts/run_openclaw_docker.sh 02_Version_Update 5

  # Run all tasks from category 03 with custom output
  bash scripts/run_openclaw_docker.sh 03_Procedure_Transfer 100 outputs/procedure_results.json

EOF
}

# Parse arguments
CATEGORY="${1:-01_Recent_Constraint_Tracking}"
MAX_TASKS="${2:-1}"
OUTPUT="${3:-outputs/openclaw_docker_summary.json}"

# Show help if requested
if [[ "$CATEGORY" == "-h" || "$CATEGORY" == "--help" ]]; then
    show_usage
    exit 0
fi

# Validate that the category exists
TASKS_DIR="$ROOT_DIR/tasks/$CATEGORY"
if [ ! -d "$TASKS_DIR" ]; then
    echo "Error: Category directory not found: $TASKS_DIR"
    echo ""
    echo "Available categories:"
    ls -1 "$ROOT_DIR/tasks/" 2>/dev/null || echo "  (tasks directory not found)"
    exit 1
fi

# Check if required files exist
echo "========================================="
echo "OpenClaw-MemBench Docker Runner"
echo "========================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please edit .env with your API credentials before running."
        exit 1
    else
        echo "Error: .env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Check Python dependencies
echo "Checking Python environment..."
if ! python3 -c "import yaml, rich, dotenv, requests" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check Docker image
DOCKER_IMAGE="${OPENCLAW_DOCKER_IMAGE:-openclaw-membench:latest}"
echo "Checking Docker image: $DOCKER_IMAGE"
if ! docker image inspect "$DOCKER_IMAGE" > /dev/null 2>&1; then
    echo "Docker image not found: $DOCKER_IMAGE"
    echo "Building image first..."
    bash scripts/build_openclaw_image.sh "$DOCKER_IMAGE"
fi

# Create output directory
mkdir -p "$(dirname "$OUTPUT")"

echo ""
echo "Configuration:"
echo "  Category:     $CATEGORY"
echo "  Max tasks:    $MAX_TASKS"
echo "  Output:       $OUTPUT"
echo "  Runtime:      openclaw-docker"
echo "  Docker image: $DOCKER_IMAGE"
echo ""
echo "Starting benchmark run..."
echo "========================================="
echo ""

# Run the benchmark
export OPENCLAW_RUNTIME=openclaw-docker
export OPENCLAW_DOCKER_IMAGE="$DOCKER_IMAGE"

python eval/run_batch.py \
  --runtime openclaw-docker \
  --category "$CATEGORY" \
  --max-tasks "$MAX_TASKS" \
  --output "$OUTPUT"

EXIT_CODE=$?

echo ""
echo "========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "Benchmark completed successfully!"
    echo "Results saved to: $OUTPUT"
else
    echo "Benchmark failed with exit code: $EXIT_CODE"
fi
echo "========================================="

exit $EXIT_CODE
