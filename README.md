# Claude Code Proxy - Nebius Edition

A specialized proxy server that enables **Claude Code** to work seamlessly with **Nebius** token factory. This proxy is exclusively designed and tested for Nebius AI services, converting Claude API requests to Nebius-compatible API calls, allowing you to use Nebius LLM providers through the Claude Code CLI.

**Based on original work by [holegots](https://github.com/holegots)** - This project has been extensively customized and optimized exclusively for Nebius token factory infrastructure.

> **Important**: This proxy is built exclusively for Nebius token factory. All development, testing, and optimization is focused entirely on Nebius infrastructure.

![Claude Code Proxy](demo.png)

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
2. **Routes to Vision Model**: Automatically switches to the configured `IMAGE_MODEL` (default: `mistralai/pixtral-12b-2409`)
3. **Maintains Context**: Preserves text context alongside image data
4. **Returns Structured Responses**: Processes image inputs and returns appropriate text responses

```bash
# Example image model configuration
VISION_MODEL="Qwen/Qwen2.5-VL-72B-Instruct"  # Nebius multi-modal vision model
# Optional: Strip image context for non-vision models
STRIP_IMAGE_CONTEXT=true
```

The image support has been **succesfully tested** with the provided test suite, confirming the proxy's ability to handle image-based requests properly.

## Quick Start (Nebius Configuration)

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
BIG_MODEL="zai-org/GLM-4.5"
MIDDLE_MODEL="zai-org/GLM-4.5"
SMALL_MODEL="zai-org/GLM-4.5"
VISION_MODEL="Qwen/Qwen2.5-VL-72B-Instruct"
STRIP_IMAGE_CONTEXT=true
```

### 3. Start Server

```bash
# Direct run
python start_proxy.py

# Or with UV
uv run claude-code-proxy

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
- `STRIP_IMAGE_CONTEXT` - Strips image context from non-vision models (default: `true`)

**API Configuration:**

- `OPENAI_BASE_URL` - API base URL (default: `https://api.tokenfactory.nebius.com/v1`) - Optimized for Nebius token factory

**Server Settings:**

- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8083`)
- `LOG_LEVEL` - Logging level (default: `WARNING`)

**Performance:**

- `MAX_TOKENS_LIMIT` - Token limit (default: `4096`)
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: `90`)

**Custom Headers:**

- `CUSTOM_HEADER_*` - Custom headers for API requests (e.g., `CUSTOM_HEADER_ACCEPT`, `CUSTOM_HEADER_AUTHORIZATION`)
  - Uncomment in `.env` file to enable custom headers

### Custom Headers Configuration

Add custom headers to your API requests by setting environment variables with the `CUSTOM_HEADER_` prefix:

```bash
# Uncomment to enable custom headers
# CUSTOM_HEADER_ACCEPT="application/jsonstream"
# CUSTOM_HEADER_CONTENT_TYPE="application/json"
# CUSTOM_HEADER_USER_AGENT="your-app/1.0.0"
# CUSTOM_HEADER_AUTHORIZATION="Bearer your-token"
# CUSTOM_HEADER_X_API_KEY="your-api-key"
# CUSTOM_HEADER_X_CLIENT_ID="your-client-id"
# CUSTOM_HEADER_X_CLIENT_VERSION="1.0.0"
# CUSTOM_HEADER_X_REQUEST_ID="unique-request-id"
# CUSTOM_HEADER_X_TRACE_ID="trace-123"
# CUSTOM_HEADER_X_SESSION_ID="session-456"
```

### Header Conversion Rules

Environment variables with the `CUSTOM_HEADER_` prefix are automatically converted to HTTP headers:

- Environment variable: `CUSTOM_HEADER_ACCEPT`
- HTTP Header: `ACCEPT`

- Environment variable: `CUSTOM_HEADER_X_API_KEY`
- HTTP Header: `X-API-KEY`

- Environment variable: `CUSTOM_HEADER_AUTHORIZATION`
- HTTP Header: `AUTHORIZATION`

### Supported Header Types

- **Content Type**: `ACCEPT`, `CONTENT-TYPE`
- **Authentication**: `AUTHORIZATION`, `X-API-KEY`
- **Client Identification**: `USER-AGENT`, `X-CLIENT-ID`, `X-CLIENT-VERSION`
- **Tracking**: `X-REQUEST-ID`, `X-TRACE-ID`, `X-SESSION-ID`

### Usage Example

```bash
# Basic configuration
OPENAI_API_KEY="sk-your-openai-api-key-here"
OPENAI_BASE_URL="https://api.openai.com/v1"

# Enable custom headers (uncomment as needed)
CUSTOM_HEADER_ACCEPT="application/jsonstream"
CUSTOM_HEADER_CONTENT_TYPE="application/json"
CUSTOM_HEADER_USER_AGENT="my-app/1.0.0"
CUSTOM_HEADER_AUTHORIZATION="Bearer my-token"
```

The proxy will automatically include these headers in all API requests to the target LLM provider.

### Model Mapping (Nebius Optimized)

The proxy maps Claude model requests to Nebius-compatible models:

| Claude Request          | Mapped To      | Environment Variable            | Nebius Default                          |
| ---------------------- | -------------- | ------------------------------ | --------------------------------------- |
| Models with "haiku"    | `SMALL_MODEL`  | `zai-org/GLM-4.5`              | High-quality text generation            |
| Models with "sonnet"   | `MIDDLE_MODEL` | `zai-org/GLM-4.5`              | Balanced performance and quality        |
| Models with "opus"     | `BIG_MODEL`    | `zai-org/GLM-4.5`              | Highest quality, complex reasoning      |
| **Requests with images** | `VISION_MODEL` | `Qwen/Qwen2.5-VL-72B-Instruct` | **🆕 Multi-modal vision model**        |

### Provider Examples

#### Nebius Token Factory (Recommended)

```bash
OPENAI_API_KEY="your-nebius-api-key"
OPENAI_BASE_URL="https://api.tokenfactory.nebius.com/v1"
BIG_MODEL="zai-org/GLM-4.5"
MIDDLE_MODEL="zai-org/GLM-4.5"
SMALL_MODEL="zai-org/GLM-4.5"
VISION_MODEL="Qwen/Qwen2.5-VL-72B-Instruct"
STRIP_IMAGE_CONTEXT=true
```


## Usage Examples

### Basic Chat

```python
import httpx

response = httpx.post(
    "http://localhost:8083/v1/messages",
    json={
        "model": "claude-3-5-sonnet-20241022",  # Maps to MIDDLE_MODEL
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
)
```

## Integration with Claude Code

This proxy is designed to work seamlessly with Claude Code CLI:

```bash
# Start the proxy
python start_proxy.py

# Use Claude Code with the proxy
ANTHROPIC_BASE_URL=http://localhost:8083 claude

# Or set permanently
export ANTHROPIC_BASE_URL=http://localhost:8083
claude
```

## Testing

The proxy includes comprehensive testing specifically designed for Nebius infrastructure:

```bash
# Run comprehensive Nebius-focused tests
python src/test_claude_to_openai.py
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
uv run claude-code-proxy

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
│   ├── test_claude_to_openai.py    # Tests
│   └── [other modules...]
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
