# DJP Workflow Platform - Docker Deployment

This directory contains Docker packaging files for deploying the DJP Workflow platform in containerized environments.

## Architecture

The platform consists of three main services:

1. **App Container** (`Dockerfile.app`): Runs the Streamlit dashboard, APIs, and health check server
2. **Worker Container** (`Dockerfile.worker`): Processes jobs from the queue with reliability features
3. **Redis**: Message broker and persistent queue backend

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- `.env` file in project root (copy from `docker/.env.example`)

### Launch Development Stack

```bash
# From project root
cd openai-agents-workflows-2025.09.28-v1

# Copy environment template (if not already done)
cp docker/.env.example .env
# Edit .env with your API keys and configuration

# Start all services
docker-compose -f docker/docker-compose.yml up

# Or run in background
docker-compose -f docker/docker-compose.yml up -d
```

### Access Services

- **Dashboard**: http://localhost:8501
- **Health Check**: http://localhost:8080/ready
- **Redis**: localhost:6379 (for debugging)

## Service Details

### App Container (Dockerfile.app)

**Purpose**: User-facing dashboard and API endpoints

**Features**:
- Multi-stage build for optimized image size
- Non-root user (`djpapp:1000`) for security
- Health checks via `/ready` endpoint
- Automatic health server startup

**Ports**:
- `8501`: Streamlit dashboard
- `8080`: Health check server

**Volumes**:
- `/app/logs`: Application logs
- `/app/artifacts`: Generated artifacts
- `/app/audit`: Audit logs
- `/app/runs`: Workflow run data
- `/app/corpus`: Document corpus

**Environment Variables**:
- `OPENAI_API_KEY`: Required for AI features
- `QUEUE_BACKEND`: Set to `redis` for production
- `REDIS_URL`: Redis connection string
- `HEALTH_PORT`: Health server port (default: 8080)

### Worker Container (Dockerfile.worker)

**Purpose**: Background job processing and queue management

**Features**:
- Multi-stage build for optimized image size
- Non-root user (`djpworker:1001`) for security
- Heartbeat-based health checks
- Automatic job retry with exponential backoff
- Dead letter queue (DLQ) for failed jobs

**Health Check**: Worker maintains a heartbeat file at `/tmp/worker/heartbeat.txt`

**Volumes**:
- `/app/logs`: Worker logs and events
- `/app/artifacts`: Job artifacts
- `/app/audit`: Audit logs
- `/app/workflows`: DAG definitions (read-only)

**Environment Variables**:
- `WORKER_ID`: Unique worker identifier
- `MAX_JOB_RETRIES`: Maximum retry attempts (default: 3)
- `LEASE_HEARTBEAT_MS`: Heartbeat interval (default: 15000)
- `QUEUE_BACKEND`: Set to `redis` for production
- `REDIS_URL`: Redis connection string

### Redis Container

**Purpose**: Message broker and persistent queue

**Features**:
- Redis 7 Alpine (minimal footprint)
- AOF persistence (append-only file)
- 512MB memory limit with LRU eviction
- Automatic health checks

**Volumes**:
- `/data`: Persistent Redis data

## Common Operations

### View Logs

```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Specific service
docker-compose -f docker/docker-compose.yml logs -f app
docker-compose -f docker/docker-compose.yml logs -f worker
docker-compose -f docker/docker-compose.yml logs -f redis
```

### Scale Workers

```bash
# Run 3 worker instances
docker-compose -f docker/docker-compose.yml up -d --scale worker=3

# Worker IDs will be: worker-1, djp-worker-1_2, djp-worker-1_3
```

### Restart Services

```bash
# Restart all
docker-compose -f docker/docker-compose.yml restart

# Restart specific service
docker-compose -f docker/docker-compose.yml restart worker
```

### Stop Services

```bash
# Stop but keep volumes
docker-compose -f docker/docker-compose.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker/docker-compose.yml down -v
```

### Check Service Health

```bash
# App health
curl http://localhost:8080/health
curl http://localhost:8080/ready

# Redis health
docker-compose -f docker/docker-compose.yml exec redis redis-cli ping

# Worker health (via Docker)
docker-compose -f docker/docker-compose.yml ps
```

## Production Deployment

### Build Images

```bash
# Build app image
docker build -f docker/Dockerfile.app -t djp-workflow-app:1.0 .

# Build worker image
docker build -f docker/Dockerfile.worker -t djp-workflow-worker:1.0 .
```

### Push to Registry

```bash
# Tag for your registry
docker tag djp-workflow-app:1.0 your-registry.com/djp-workflow-app:1.0
docker tag djp-workflow-worker:1.0 your-registry.com/djp-workflow-worker:1.0

# Push
docker push your-registry.com/djp-workflow-app:1.0
docker push your-registry.com/djp-workflow-worker:1.0
```

### Environment Configuration

For production, ensure these variables are set:

**Required**:
- `OPENAI_API_KEY`: AI provider API key
- `REDIS_URL`: Production Redis instance
- `QUEUE_BACKEND=redis`

**Recommended**:
- `LOG_LEVEL=INFO` or `WARNING`
- `MAX_JOB_RETRIES=3`
- `BUILD_VERSION`: Deployment version
- `GIT_SHA`: Git commit SHA
- `BUILD_DATE`: Build timestamp

**Optional** (for advanced features):
- `FEATURE_MULTI_REGION=true`: Enable multi-region support
- `FEATURE_BLUE_GREEN=true`: Enable blue/green deployments
- `AWS_*` or `GCS_*`: Cloud storage credentials

## Security Best Practices

1. **Non-root Users**: Both containers run as non-root users (UIDs 1000, 1001)
2. **Read-only Mounts**: Configuration directories mounted as read-only
3. **Secret Management**: Use Docker secrets or environment files (not committed to git)
4. **Network Isolation**: Services communicate via internal bridge network
5. **Health Checks**: All services have health checks for orchestration

## Troubleshooting

### App won't start

Check logs:
```bash
docker-compose -f docker/docker-compose.yml logs app
```

Common issues:
- Missing `OPENAI_API_KEY` in `.env`
- Port 8501 or 8080 already in use
- Redis not reachable

### Worker not processing jobs

Check worker logs:
```bash
docker-compose -f docker/docker-compose.yml logs worker
```

Common issues:
- Redis connection failed (check `REDIS_URL`)
- No jobs in queue
- Heartbeat file not updating (check health status)

### Redis connection errors

```bash
# Test Redis connectivity
docker-compose -f docker/docker-compose.yml exec redis redis-cli ping

# Check Redis logs
docker-compose -f docker/docker-compose.yml logs redis
```

### Permission denied errors

Ensure directories exist with proper permissions:
```bash
mkdir -p logs artifacts audit runs corpus workflows
chmod 755 logs artifacts audit runs corpus workflows
```

## Development Tips

### Live Code Reload

For development, mount source code as volumes in `docker-compose.yml`:

```yaml
services:
  app:
    volumes:
      - ../src:/app/src
      - ../dashboards:/app/dashboards
```

### Debug Mode

Set environment variable:
```yaml
environment:
  LOG_LEVEL: DEBUG
```

### Local Redis

Use local Redis instead of container:
```yaml
environment:
  REDIS_URL: redis://host.docker.internal:6379/0
```

## Kubernetes Deployment

The Dockerfiles are designed for Kubernetes deployment:

- Health checks map to liveness/readiness probes
- Non-root users for Pod Security Policies
- Configurable via environment variables
- Horizontal scaling supported (workers)

Example Kubernetes health probe:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
```

## File Structure

```
docker/
├── Dockerfile.app          # Application container
├── Dockerfile.worker       # Worker container
├── docker-compose.yml      # Development stack orchestration
├── .env.example           # Environment template
└── README.md              # This file
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review health endpoints: `/health`, `/ready`
3. Verify `.env` configuration
4. Consult main project documentation

## License

See project LICENSE file.
