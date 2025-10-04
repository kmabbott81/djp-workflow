# Multi-stage build for DJP Workflow Application Container
# Runs: Dashboard + APIs + Health Server
# Ports: 8501 (Streamlit), 8080 (Health Check)

FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt requirements-cloud.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user -r requirements-cloud.txt && \
    pip install --no-cache-dir --user redis>=5.0.0

# Production stage
FROM python:3.11-slim

# Metadata labels
LABEL maintainer="DJP Workflow Platform"
LABEL description="Application container for DJP Workflow (dashboard, APIs, health server)"
LABEL version="1.0"

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r djpapp --gid=1000 && \
    useradd -r -g djpapp --uid=1000 --home-dir=/app --shell=/bin/bash djpapp && \
    mkdir -p /app && \
    chown -R djpapp:djpapp /app

# Copy Python dependencies from builder
COPY --from=builder --chown=djpapp:djpapp /root/.local /home/djpapp/.local

# Set PATH for installed packages
ENV PATH=/home/djpapp/.local/bin:$PATH

# Copy application code
COPY --chown=djpapp:djpapp src/ ./src/
COPY --chown=djpapp:djpapp dashboards/ ./dashboards/
COPY --chown=djpapp:djpapp templates/ ./templates/
COPY --chown=djpapp:djpapp schemas/ ./schemas/
COPY --chown=djpapp:djpapp policies/ ./policies/
COPY --chown=djpapp:djpapp presets/ ./presets/
COPY --chown=djpapp:djpapp styles/ ./styles/
COPY --chown=djpapp:djpapp config/ ./config/
COPY --chown=djpapp:djpapp scripts/ ./scripts/
COPY --chown=djpapp:djpapp pyproject.toml README.md LICENSE ./

# Create directories for runtime data with proper permissions
RUN mkdir -p runs corpus artifacts logs audit && \
    chown -R djpapp:djpapp runs corpus artifacts logs audit

# Switch to non-root user
USER djpapp

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    HEALTH_PORT=8080 \
    LOG_LEVEL=INFO

# Expose ports
# 8501: Streamlit dashboard
# 8080: Health check server
EXPOSE 8501 8080

# Health check using /ready endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${HEALTH_PORT:-8080}/ready || exit 1

# Startup command: Launch Streamlit with health server
# The health server is started automatically by dashboards/app.py (see line 30)
CMD ["python", "-m", "streamlit", "run", "dashboards/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
