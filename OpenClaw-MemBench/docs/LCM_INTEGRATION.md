# OpenClaw LCM Integration

This document describes the Lossless Context Management (LCM) integration for OpenClaw-MemBench.

## Overview

LCM provides intelligent context compression that preserves critical information while reducing token usage. The integration supports:

1. **Real LCM API**: Connect to an OpenClaw LCM service
2. **Fallback Proxy**: Local implementation when API is unavailable
3. **Episode-aware Compression**: Respects scenario episode boundaries
4. **Skill-guided Compression**: Uses skill hints to preserve relevant context

## Architecture

```
utils/lcm_client.py
├── LCMConfig - Configuration management
├── LCMClient - API client
│   ├── compress_context()
│   ├── summarize_layer()
│   └── check_compression_health()
├── CompressionResult - Result dataclass
└── build_context_with_lcm() - Integration helper

utils/compression_profiles.py
├── build_context() - Enhanced with LCM support
└── Fallback to local compression
```

## Configuration

### Environment Variables

```bash
# LCM API endpoint
OPENCLAW_LCM_BASE_URL=http://127.0.0.1:18790
OPENCLAW_LCM_API_KEY=optional-api-key
OPENCLAW_LCM_TIMEOUT=60

# Compression settings
OPENCLAW_CONTEXT_BUDGET_CHARS=12000
OPENCLAW_COMPRESSION_METHOD=lcm-proxy
```

See `.env.example` for complete configuration options.

## Compression Methods

| Method | Description | LCM API |
|--------|-------------|---------|
| `full` | No compression | No |
| `lcm-proxy` | Two-layer summary (signal + tail) | Yes (falls back to local) |
| `sliding-window` | Keep recent N chars | No |
| `keyword` | Keyword-dense extraction | No |
| `episode` | Episode-level digest | No |
| `lcm` | Full LCM hierarchical | Yes (falls back to local) |

## LCM API Specification

### Endpoint: POST /v1/compress

**Request:**
```json
{
  "text": "long context text...",
  "method": "lcm",
  "budget_chars": 12000,
  "preserve_structures": ["episode", "checkpoint", "constraint"],
  "episodes": [
    {
      "id": "E1",
      "turns": [{"role": "user", "content": "..."}],
      "hint": "checkpoint_soft"
    }
  ],
  "skill_hints": ["constraint_tracking", "version_management"]
}
```

**Response:**
```json
{
  "compressed_text": "compressed context...",
  "reduction_ratio": 0.65,
  "metadata": {
    "original_tokens": 5000,
    "compressed_tokens": 1750,
    "layers": ["summary", "signals", "tail"]
  },
  "compression_events": [
    {"type": "episode_summarized", "episode_id": "E1"}
  ],
  "layer_info": {
    "summary_chars": 2000,
    "signals_chars": 3000,
    "tail_chars": 7000
  }
}
```

### Endpoint: POST /v1/summarize

**Request:**
```json
{
  "text": "episode content...",
  "layer_type": "episode",
  "preserve_constraints": true
}
```

**Response:**
```json
{
  "summary": "summarized content...",
  "constraint_preservation": 0.95,
  "key_phrases": ["must use CSV", "year 2024-2025"]
}
```

### Endpoint: GET /health

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "compression_methods": ["lcm", "hierarchical", "semantic"]
}
```

## Usage

### Automatic Integration

When running benchmarks, LCM integration is automatic:

```bash
# Uses LCM API if available, falls back to local
python eval/run_batch.py --category 01_Recent_Constraint_Tracking
```

### Programmatic

```python
from utils.lcm_client import LCMClient, LCMConfig

# Create client
config = LCMConfig.from_env()
client = LCMClient(config)

# Check health
health = client.check_compression_health()
print(f"LCM healthy: {health['healthy']}")

# Compress context
result = client.compress_context(
    text=long_context,
    method="lcm",
    budget_chars=12000,
    scenario_turns=turns,
)

print(f"Reduction: {result.reduction_ratio:.2%}")
print(f"Compressed: {result.context[:200]}...")
```

### With Scenario Awareness

```python
from utils.lcm_client import build_context_with_lcm
from utils.scenario_replayer import load_scenario_turns

scenario_turns = load_scenario_turns("workspace/task/scenario.jsonl")

result = build_context_with_lcm(
    workspace_path="workspace/task",
    method="lcm",
    budget_chars=12000,
    scenario_turns=scenario_turns,
    use_api=True,
)

print(f"LCM API used: {result['lcm_used']}")
print(f"Reduction ratio: {result['reduction_ratio']}")
```

## Fallback Behavior

When LCM API is unavailable:

1. Client attempts connection to `OPENCLAW_LCM_BASE_URL`
2. If connection fails, falls back to local `compression_profiles.py`
3. Local implementation uses keyword extraction + sliding window
4. Result includes `lcm_used: false` and `fallback: true` in metadata

## Episode-Aware Compression

LCM respects episode boundaries defined in `scenario.jsonl`:

```jsonl
{"turn_id": 1, "episode_id": "E1_constraints", "role": "user", "content": "..."}
{"turn_id": 2, "episode_id": "E1_constraints", "role": "user", "content": "..."}
{"turn_id": 3, "episode_id": "E2_noise", "role": "user", "content": "..."}
{"turn_id": 4, "episode_id": "E3_final", "role": "user", "content": "...", "compression_hint": "checkpoint_hard"}
```

Episodes are compressed individually, with checkpoint hints preserved.

## Compression Checkpoints

Scenario turns can include `compression_hint`:

- `checkpoint_soft`: Summarize but preserve key details
- `checkpoint_hard`: Keep full content (critical constraints)
- `checkpoint_final`: Never compress (final user instruction)

## Metrics in usage.json

Each run includes LCM metrics:

```json
{
  "compression_method": "lcm-proxy",
  "raw_context_chars": 45000,
  "compressed_context_chars": 12000,
  "context_reduction_ratio": 0.7333,
  "lcm_api_used": true,
  "scenario_turns": 12,
  "compression_events": [
    {"turn_id": 4, "episode_id": "E1", "hint": "checkpoint_soft"}
  ]
}
```

## Performance Considerations

### When to Use LCM API

✅ **Recommended:**
- Large context windows (>50K chars)
- Complex multi-episode scenarios
- Production benchmark runs
- Need fine-grained compression control

❌ **Not needed:**
- Small contexts (<10K chars)
- Quick development/testing
- Limited API quota

### Optimization Tips

1. **Adjust budget**: Match to model context window
   ```bash
   OPENCLAW_CONTEXT_BUDGET_CHARS=8000  # For 8K models
   ```

2. **Selective episode compression**: Use `compression_hint` to protect critical episodes

3. **Cache compressed results**: Reuse for repeated runs

4. **Batch compression**: Compress multiple episodes in parallel

## Troubleshooting

### LCM API Connection Failed

```
LCMError: Connection refused
```

**Solution:**
- Check `OPENCLAW_LCM_BASE_URL` is correct
- Verify LCM service is running
- System falls back to local compression automatically

### Excessive Compression

If important information is lost:

1. Increase budget: `OPENCLAW_CONTEXT_BUDGET_CHARS=15000`
2. Add `checkpoint_hard` hints to critical episodes
3. Use `full` method for debugging

### Low Reduction Ratio

If compression is ineffective:

1. Verify text contains compressible patterns
2. Check for very short contexts (< budget)
3. Try `keyword` method for keyword-dense content

## Development

### Mock LCM Server

For testing without real LCM:

```python
# Simple mock server
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/v1/compress', methods=['POST'])
def compress():
    data = request.json
    text = data['text']
    budget = data['budget_chars']
    # Simple truncation
    compressed = text[-budget:] if len(text) > budget else text
    return jsonify({
        'compressed_text': compressed,
        'reduction_ratio': 1 - len(compressed)/len(text),
        'metadata': {'mock': True}
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(port=18790)
```

### Testing Compression

```bash
# Test specific compression method
python -c "
from utils.compression_profiles import build_context
result = build_context('workspace/task', 'lcm-proxy', 12000)
print(f'Ratio: {result[\"reduction_ratio\"]:.2%}')
"
```

## Future Enhancements

1. **Semantic compression**: Use embeddings for similarity-based compression
2. **Adaptive budget**: Dynamic budget based on task complexity
3. **Multi-layer caching**: Cache intermediate compression results
4. **Compression quality metrics**: Measure information preservation
