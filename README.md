# Claude Code Proxy - Nebius Edition

A specialized proxy server that enables **Claude Code** to work seamlessly with **Nebius** token factory. This proxy is exclusively designed and tested for Nebius AI services, converting Claude API requests to Nebius-compatible API calls, allowing you to use Nebius LLM providers through the Claude Code CLI.

**Based on original work by [holegots](https://github.com/holegots)** - This project has been extensively customized and optimized exclusively for Nebius token factory infrastructure.

> **Important**: This proxy is built exclusively for Nebius token factory. All development, testing, and optimization is focused entirely on Nebius infrastructure.


## Features

- **Nebius Optimized**: Specifically designed and tested for Nebius token factory infrastructure
- **Full Claude API Compatibility**: Complete `/v1/messages` endpoint support with proper Nebius adaptations
- **Smart Model Mapping**: Configure models via environment variables optimized for Nebius model offerings
- **Function Calling**: Complete tool use support with Nebius-compatible conversion
- **Streaming Responses**: Real-time SSE streaming support for Nebius endpoints
- **🆕 Image Support**: Full support for base64 encoded image inputs with automatic model routing to vision-capable models
- **Custom Headers**: Automatic injection of Nebius-specific HTTP headers for API requests
- **Error Handling**: Comprehensive error handling optimized for Nebius error responses
- **Robust Testing**: Rigorous test coverage including image model functionality

### 🆕 Image Support Feature

The proxy now supports image inputs in Claude API requests. When images are detected in messages, the system automatically:

1. **Detects Image Content**: Scans message content for base64 encoded images
2. **Routes to Vision Model**: Automatically switches to the configured `VISION_MODEL` (default: `Qwen/Qwen2.5-VL-72B-Instruct`)
3. **Maintains Context**: Preserves text context alongside image data
4. **Returns Structured Responses**: Processes image inputs and returns appropriate text responses

```bash
# Example image model configuration
VISION_MODEL="Qwen/Qwen2.5-VL-72B-Instruct"  # Nebius multi-modal vision model
# Optional: For image requests, control whether system context is forwarded
STRIP_IMAGE_CONTEXT=true
```

The image support has been **successfully tested** with the provided test suite, confirming the proxy's ability to handle image-based requests properly.

## Quick Start (Nebius Configuration)

### Prerequisites 

- claude-code
```bash
brew install --cask claude-code
```
- docker (if using with Docker like I do)
- UV if running with VU
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Install Dependencies

```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Configure for Nebius

```bash
cp .env.example .env
# Edit .env with your Nebius configuration
# Note: Environment variables are automatically loaded from .env file

# Required Nebius settings
OPENAI_API_KEY="your-nebius-api-key"
OPENAI_BASE_URL="https://api.tokenfactory.nebius.com/v1"

# Optional: Customize Nebius models (default values provided)
BIG_MODEL=zai-org/GLM-4.7-FP8
MIDDLE_MODEL=zai-org/GLM-4.7-FP8
SMALL_MODEL=zai-org/GLM-4.7-FP8
VISION_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
STRIP_IMAGE_CONTEXT=true
```

### 3. Start Server

```bash
# Direct run
python start_proxy.py

# Or with UV
uv run claude-code-proxy-nebius

# Or with docker compose
docker compose up -d
```

### 4. Use with Claude Code

```bash
# If ANTHROPIC_API_KEY is not set in the proxy:
ANTHROPIC_BASE_URL=http://localhost:8083 ANTHROPIC_API_KEY="any-value" claude

# If ANTHROPIC_API_KEY is set in the proxy:
ANTHROPIC_BASE_URL=http://localhost:8083 ANTHROPIC_API_KEY="exact-matching-key" claude
```

## Configuration

The application automatically loads environment variables from a `.env` file in the project root using `python-dotenv`. You can also set environment variables directly in your shell.

### Environment Variables

**Required:**

- `OPENAI_API_KEY` - Your Nebius API key for the token factory

**Security:**

- `ANTHROPIC_API_KEY` - Expected Anthropic API key for client validation
  - If set, clients must provide this exact API key to access the proxy
  - If not set, any API key will be accepted

**Model Configuration:**

- `BIG_MODEL` - Model for Claude opus requests (default: `zai-org/GLM-4.5`)
- `MIDDLE_MODEL` - Model for Claude sonnet requests (default: `zai-org/GLM-4.5`)
- `SMALL_MODEL` - Model for Claude haiku requests (default: `zai-org/GLM-4.5`)
- `VISION_MODEL` - Model for vision/image requests (default: `Qwen/Qwen2.5-VL-72B-Instruct`)
- `STRIP_IMAGE_CONTEXT` - For image requests, controls forwarding of system context to the vision model (default: `true`)
  - Note: Image turns are always text-trimmed to protect vision context size.

**API Configuration:**

- `OPENAI_BASE_URL` - API base URL (default: `https://api.tokenfactory.nebius.com/v1`) - Optimized for Nebius token factory

**Server Settings:**

- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8083`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

**Performance:**

- `MAX_TOKENS_LIMIT` - Token limit (default: `4096`)
- `MIN_TOKENS_LIMIT` - Fallback token limit when request value is invalid (default: `100`)
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: `90`)
- `MAX_RETRIES` - Retries for transient provider/API failures (default: `2`)

### Model Mapping (Nebius Optimized)

The proxy maps Claude model requests to Nebius-compatible models:

| Claude Request          | Mapped To      | Environment Variable            | Nebius Default                          |
| ---------------------- | -------------- | ------------------------------ | --------------------------------------- |
| Models with "haiku"    | `SMALL_MODEL`  | `zai-org/GLM-4.7-FP8`              | High-quality text generation            |
| Models with "sonnet"   | `MIDDLE_MODEL` | `zai-org/GLM-4.7-FP8`              | Balanced performance and quality        |
| Models with "opus"     | `BIG_MODEL`    | `zai-org/GLM-4.7-FP8`              | Highest quality, complex reasoning      |
| **Requests with images** | `VISION_MODEL` | `Qwen/Qwen2.5-VL-72B-Instruct` | **🆕 Multi-modal vision model**        |


## Integration with Claude Code

This proxy is designed to work seamlessly with Claude Code CLI:

```bash
# Start the proxy
python start_proxy.py

# Use Claude Code with the proxy


ANTHROPIC_BASE_URL=http://localhost:8083 claude

# Or set permanently
export ANTHROPIC_BASE_URL="http://localhost:8083"
export ANTHROPIC_API_KEY="claude-local"
export CLAUDE_CODE_MAX_OUTPUT_TOKENS="65536"
claude
```

## Testing

The proxy includes comprehensive testing specifically designed for Nebius infrastructure:

```bash
# Fast unit tests
python -m pytest -q tests/test_request_converter.py tests/test_image_routing.py

# Optional integration smoke tests (requires proxy running on :8083)
python tests/test_main.py

# Optional pytest collection for integration module
RUN_PROXY_INTEGRATION_TESTS=1 python -m pytest -q tests/test_main.py

# Direct upstream auth diagnostic (bypasses proxy conversion)
python tests/auth_test.py
```

### Test Coverage

- **Nebius API Compatibility**: Verified with Nebius token factory endpoints
- **Model Mapping**: All model routing tested with Nebius model offerings
- **Image Support**: Successfully tested with base64 encoded images using `Qwen/Qwen2.5-VL-72B-Instruct`
- **Function Calling**: Tool use compatibility verified with Nebius inference services
- **Error Handling**: Nebius-specific error response handling tested
- **Streaming**: Real-time response streaming validated with Nebius endpoints

## Development

### Using UV

```bash
# Install dependencies
uv sync

# Run server
uv run claude-code-proxy-nebius

# Format code
uv run black src/
uv run isort src/

# Type checking
uv run mypy src/
```

### Project Structure

```
claude-code-proxy/
├── src/
│   ├── main.py                     # Main server
│   └── [api/core/conversion/models]
├── tests/
│   ├── test_request_converter.py   # Unit tests
│   ├── test_image_routing.py       # Unit tests
│   ├── test_main.py                # Optional integration script/tests
│   └── auth_test.py                # Direct provider auth diagnostic
├── start_proxy.py                  # Startup script
├── .env.example                    # Config template
└── README.md                       # This file
```

## Performance

- **Async/await** for high concurrency
- **Connection pooling** for efficiency
- **Streaming support** for real-time responses
- **Configurable timeouts** and retries
- **Smart error handling** with detailed logging

## Nebius Disclaimer

> **Exclusively for Nebius**: This proxy is designed and tested exclusively for Nebius token factory infrastructure. All features, testing, and optimizations are performed specifically for Nebius endpoints. This proxy is not intended for use with other providers.

## License

MIT License
