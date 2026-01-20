FROM ghcr.io/astral-sh/uv:bookworm-slim

# Install build tools required for httptools / uvicorn
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the project
ADD . /app
WORKDIR /app

# Install dependencies
RUN uv sync --locked

# Start proxy
CMD ["uv", "run", "start_proxy.py"]
