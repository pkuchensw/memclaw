# OpenClaw-MemBench Docker Setup Guide

This guide provides detailed instructions for setting up and running OpenClaw-MemBench using Docker.

## Overview

The Docker setup provides:
- **Isolated environment**: Consistent execution regardless of host system
- **Reproducibility**: Same environment across different machines
- **Easy deployment**: Simple commands to get started
- **No dependency conflicts**: Self-contained with all required tools

## Prerequisites

### Required
- Docker Engine 20.10+ or Docker Desktop
- 4GB+ available RAM
- 2GB+ free disk space

### Optional
- Docker Compose 2.0+ (for docker-compose deployment)
- bash shell (for helper scripts)

## Installation

### Step 1: Verify Docker Installation

```bash
docker --version
docker info
```

### Step 2: Clone/Navigate to Project

```bash
cd OpenClaw-MemBench
```

### Step 3: Configure Environment

```bash
cp .env.example .env
# Edit .env with your API credentials
```

Required variables:
```bash
OPENCLAW_API_KEY=your-api-key
OPENCLAW_BASE_URL=https://api.openai.com/v1  # or your provider
OPENCLAW_MODEL=gpt-4  # or your model
```

## Building the Docker Image

### Option A: Using Build Script (Recommended)

```bash
bash scripts/build_openclaw_image.sh
```

This builds `openclaw-membench:latest` using the standalone Dockerfile.

### Option B: Manual Build

```bash
docker build -f docker/Dockerfile.standalone -t openclaw-membench:latest .
```

### Option C: Using Docker Compose

```bash
docker-compose build openclaw-membench
```

## Testing the Setup

Run the test script to verify everything is working:

```bash
bash scripts/test_docker_setup.sh
```

This checks:
- Docker daemon is running
- Image exists (builds if missing)
- OpenClaw CLI works inside container
- Python environment is correct
- API configuration is present

## Running Benchmarks

### Quick Start

```bash
# Run 1 task from category 01
bash scripts/run_openclaw_docker.sh

# Run 5 tasks from category 02
bash scripts/run_openclaw_docker.sh 02_Version_Update 5

# Run all tasks from a category
bash scripts/run_openclaw_docker.sh 03_Procedure_Transfer 100
```

### Available Categories

| Category ID | Name |
|-------------|------|
| 01_Recent_Constraint_Tracking | Recent Constraint Tracking |
| 02_Version_Update | Version Update |
| 03_Procedure_Transfer | Procedure Transfer |
| 04_Repeated_Mistake_Prevention | Repeated Mistake Prevention |
| 05_Source_Conflict_Resolution | Source Conflict Resolution |
| 06_Memory_Operation_Selection | Memory Operation Selection |
| 07_Goal_Interruption_Resumption | Goal Interruption and Task Resumption |
| 08_Staleness_Applicability_Judgment | Staleness and Applicability Judgment |

### Manual Docker Run

If you need more control:

```bash
# Set environment
export OPENCLAW_RUNTIME=openclaw-docker
export OPENCLAW_DOCKER_IMAGE=openclaw-membench:latest

# Run benchmark
python eval/run_batch.py \
  --runtime openclaw-docker \
  --category 01_Recent_Constraint_Tracking \
  --max-tasks 1 \
  --output outputs/results.json
```

## Docker Compose Usage

### Start Services

```bash
# Start the benchmark environment
docker-compose up -d openclaw-membench

# Check status
docker-compose ps
```

### Execute Commands

```bash
# Open shell in container
docker-compose exec openclaw-membench bash

# Run command directly
docker-compose exec openclaw-membench openclaw --version
```

### Stop Services

```bash
docker-compose down
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCLAW_RUNTIME` | `api` | Runtime mode: `api`, `docker`, or `openclaw-docker` |
| `OPENCLAW_DOCKER_IMAGE` | `openclaw-membench:latest` | Docker image to use |
| `OPENCLAW_DOCKER_NETWORK` | `host` | Docker network mode |
| `OPENCLAW_DOCKER_PRESERVE_CONTAINER` | `false` | Keep containers after run |
| `OPENCLAW_DOCKER_HIDE_PATTERNS` | `oracle.yaml,grader.py,...` | Files to hide from agent |

### Volume Mounts

The Docker runtime mounts:
- Task workspace (read-only): `/app`
- Temporary workspace: `/tmp_workspace`
- Results: `/tmp_output`

## Troubleshooting

### Docker Daemon Not Running

**Symptom**: `Cannot connect to the Docker daemon`

**Solution**:
```bash
# Linux
sudo systemctl start docker

# macOS/Windows
# Start Docker Desktop application
```

### Image Build Fails

**Symptom**: Build errors or timeouts

**Solution**:
```bash
# Check Docker is running
docker info

# Clean build
DOCKER_BUILDKIT=1 docker build --no-cache -f docker/Dockerfile.standalone -t openclaw-membench:latest .

# Or disable BuildKit if causing issues
DOCKER_BUILDKIT=0 docker build -f docker/Dockerfile.standalone -t openclaw-membench:latest .
```

### Container Cannot Access API

**Symptom**: API connection errors inside container

**Solution**:
```bash
# Use host network (default)
export OPENCLAW_DOCKER_NETWORK=host

# Or use bridge network with explicit DNS
docker run --network bridge --dns 8.8.8.8 openclaw-membench:latest
```

### Permission Denied

**Symptom**: Cannot execute scripts

**Solution**:
```bash
chmod +x scripts/*.sh
```

### Out of Memory

**Symptom**: Container killed or build fails

**Solution**:
- Increase Docker memory limit in Docker Desktop settings
- Reduce parallel tasks: `--max-tasks 1`
- Use smaller model

### Slow Performance

**Symptom**: Tasks take too long

**Solution**:
```bash
# Use local API endpoint if available
export OPENCLAW_BASE_URL=http://localhost:8000/v1

# Reduce timeout
export OPENCLAW_REQUEST_TIMEOUT=300
```

## Advanced Usage

### Custom Docker Image

Create your own Dockerfile:

```dockerfile
FROM openclaw-membench:latest

# Add custom tools
RUN apt-get update && apt-get install -y your-tools

# Copy custom code
COPY my-benchmarks /root/my-benchmarks
```

Build and use:
```bash
docker build -t my-openclaw-benchmark:latest -f Dockerfile.custom .
export OPENCLAW_DOCKER_IMAGE=my-openclaw-benchmark:latest
bash scripts/run_openclaw_docker.sh
```

### Debugging Inside Container

```bash
# Run container interactively
docker run -it --rm openclaw-membench:latest bash

# Inside container
openclaw --version
openclaw config list

# Test API connectivity
curl $OPENCLAW_BASE_URL/models -H "Authorization: Bearer $OPENCLAW_API_KEY"
```

### Preserving Containers for Inspection

```bash
# Set preserve flag
export OPENCLAW_DOCKER_PRESERVE_CONTAINER=true

# Run benchmark
bash scripts/run_openclaw_docker.sh

# Inspect container
docker ps -a
docker logs <container-name>
```

## Architecture

### Container Flow

```
Host
├── runs eval/run_batch.py
│   └── calls run_task_in_openclaw_container()
│       ├── creates sandbox workspace
│       ├── starts container
│       ├── runs OpenClaw gateway
│       ├── executes agent
│       ├── collects results
│       └── grades output
└── outputs/
    └── results.json
```

### Image Layers

1. **Base**: Ubuntu 22.04
2. **System**: Python 3, Node.js, git, curl
3. **OpenClaw**: OpenClaw CLI from npm
4. **Executor** (optional): Full project code

## Maintenance

### Updating the Image

```bash
# Pull latest base image
docker pull ubuntu:22.04

# Rebuild
bash scripts/build_openclaw_image.sh
```

### Cleaning Up

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune

# Clean all
# WARNING: This removes all unused Docker data
docker system prune -a
```

## Support

For issues or questions:
1. Check [README.md](../README.md) for general info
2. Review [INSTALL_EN.md](INSTALL_EN.md) for installation details
3. Check project issues page
