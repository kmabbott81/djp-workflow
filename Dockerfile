# Multi-stage build for DJP Workflow Platform
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements.in ./
RUN pip install --no-cache-dir --user -r requirements.txt

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
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Create directories for runtime data
RUN mkdir -p runs corpus artifacts

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV HEALTH_PORT=8086

# Expose Streamlit port and health check port
EXPOSE 8080 8086

# Health check using /ready endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${HEALTH_PORT:-8086}/ready')" || exit 1

# Run Streamlit dashboard
CMD ["python", "-m", "streamlit", "run", "dashboards/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
