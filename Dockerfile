# Multi-stage build for DJP Workflow Platform
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements.in pyproject.toml ./
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user -e ".[observability]"

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY dashboards/ ./dashboards/
COPY templates/ ./templates/
COPY schemas/ ./schemas/
COPY policies/ ./policies/
COPY presets/ ./presets/
COPY styles/ ./styles/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY static/ ./static/
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Make start script executable
RUN chmod +x scripts/start-server.sh

# Create directories for runtime data
RUN mkdir -p runs corpus artifacts

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (Railway will set $PORT at runtime)
EXPOSE 8000

# Health check using /_stcore/health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/_stcore/health')" || exit 1

# Run FastAPI via uvicorn
CMD ["sh", "-c", "scripts/start-server.sh"]
