# Nightwatch - Multi-arch Docker image
# Works on x86_64 (dev) and ARM64 (Raspberry Pi)
#
# Build: docker build -t nightwatch .
# Run:   docker run -p 8000:9531 nightwatch

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Audio support
    libportaudio2 \
    portaudio19-dev \
    # Serial port support (for real hardware)
    udev \
    # ZeroMQ
    libzmq3-dev \
    # Build tools (for some Python packages)
    gcc \
    python3-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY pyproject.toml README.md LICENSE ./
COPY nightwatch/ ./nightwatch/

RUN pip install --no-cache-dir .

# Copy config and scripts
COPY config/ ./config/
COPY scripts/ ./scripts/

# Default config
ENV NIGHTWATCH_CONFIG=/app/config/docker.yaml
ENV NIGHTWATCH_MOCK_SENSORS=true

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9531/health')" || exit 1

# Default command - runs with mock sensors for dev
CMD ["python", "-m", "nightwatch", "--mock-sensors", "--config", "/app/config/docker.yaml"]
