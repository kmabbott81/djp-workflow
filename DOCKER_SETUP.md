# DJP Workflow Platform - Docker Setup Guide

## Quick Start

### Prerequisites
- Docker Engine 20.10+ and Docker Compose 2.0+
- At least 4GB RAM available for Docker
- 10GB free disk space

### 1. Configure Environment

```bash
# Copy environment template
cp docker/.env.example .env

# Edit .env and add your API keys
# Minimum required: OPENAI_API_KEY
```

### 2. Start Services

**Windows (PowerShell):**
```powershell
cd docker
.\start-docker.ps1 -Background -Workers 2
```

**Linux/Mac:**
```bash
cd docker
./start-docker.sh -b -w 2
```

**Or use Docker Compose directly:**
```bash
docker-compose -f docker/docker-compose.yml up -d --scale worker=2
```

### 3. Access Dashboard

- **Dashboard UI**: http://localhost:8501
- **Health Check**: http://localhost:8080/ready
- **Redis**: localhost:6379

### 4. View Logs

```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Specific service
docker-compose -f docker/docker-compose.yml logs -f app
docker-compose -f docker/docker-compose.yml logs -f worker
```

### 5. Stop Services

```bash
docker-compose -f docker/docker-compose.yml down

# With volume cleanup
docker-compose -f docker/docker-compose.yml down -v
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DJP Workflow Stack                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────┐  │
│  │  App (8501)  │───▶│ Redis (6379) │◀───│ Worker  │  │
│  │  Dashboard   │    │  Queue       │    │ (x1-N)  │  │
│  │  + Health    │    │  + Cache     │    │         │  │
│  │    (8080)    │    └──────────────┘    └─────────┘  │
│  └──────────────┘                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Components

1. **App Container** (`Dockerfile.app`)
   - Streamlit dashboard on port 8501
   - Health server on port 8080
   - User-facing APIs
   - Non-root user (djpapp:1000)

2. **Worker Container** (`Dockerfile.worker`)
   - Queue job processor
   - Heartbeat health monitoring
   - Scales horizontally
   - Non-root user (djpworker:1001)

3. **Redis Container**
   - Message broker
   - Persistent queue backend
   - AOF persistence enabled
   - 512MB memory limit

## Common Operations

### Scale Workers

```bash
# Using helper script (PowerShell)
.\start-docker.ps1 -Workers 5

# Using helper script (Bash)
./start-docker.sh -w 5

# Using docker-compose
docker-compose -f docker/docker-compose.yml up -d --scale worker=5

# Using Makefile
make scale WORKERS=5
```

### Check Service Health

```bash
# App health
curl http://localhost:8080/health

# App readiness
curl http://localhost:8080/ready

# Redis
docker-compose -f docker/docker-compose.yml exec redis redis-cli ping

# All services
docker-compose -f docker/docker-compose.yml ps
```

### Access Container Shells

```bash
# App container
docker-compose -f docker/docker-compose.yml exec app /bin/bash

# Worker container
docker-compose -f docker/docker-compose.yml exec worker /bin/bash

# Redis CLI
docker-compose -f docker/docker-compose.yml exec redis redis-cli
```

### View Metrics

```bash
# Container stats
docker stats $(docker ps --filter "label=com.djp.service" --format "{{.Names}}")

# Disk usage
docker system df

# Service status
docker-compose -f docker/docker-compose.yml ps
```

### Backup & Restore

**Backup Redis data:**
```bash
docker-compose -f docker/docker-compose.yml exec redis redis-cli BGSAVE
```

**Export logs:**
```bash
docker-compose -f docker/docker-compose.yml logs --no-color > docker_logs.txt
```

## Troubleshooting

### App won't start

**Check logs:**
```bash
docker-compose -f docker/docker-compose.yml logs app
```

**Common issues:**
- Missing `OPENAI_API_KEY` in `.env`
- Port 8501 or 8080 already in use (check: `netstat -ano | findstr :8501`)
- Redis not reachable (check network: `docker network ls`)

**Solution:**
```bash
# Stop conflicting services
docker-compose -f docker/docker-compose.yml down

# Rebuild with no cache
docker-compose -f docker/docker-compose.yml build --no-cache

# Start fresh
docker-compose -f docker/docker-compose.yml up
```

### Worker not processing jobs

**Check worker logs:**
```bash
docker-compose -f docker/docker-compose.yml logs worker
```

**Common issues:**
- Redis connection failed
- No jobs in queue
- Heartbeat timeout

**Solution:**
```bash
# Check Redis connectivity
docker-compose -f docker/docker-compose.yml exec redis redis-cli ping

# Restart worker
docker-compose -f docker/docker-compose.yml restart worker

# Check worker health file
docker-compose -f docker/docker-compose.yml exec worker ls -lh /tmp/worker/heartbeat.txt
```

### Redis connection errors

**Test Redis:**
```bash
# From host
redis-cli -h localhost -p 6379 ping

# From container
docker-compose -f docker/docker-compose.yml exec redis redis-cli ping

# Check Redis logs
docker-compose -f docker/docker-compose.yml logs redis
```

**Solution:**
```bash
# Restart Redis
docker-compose -f docker/docker-compose.yml restart redis

# Check Redis data integrity
docker-compose -f docker/docker-compose.yml exec redis redis-cli --scan --pattern '*'
```

### Permission denied errors

**Check ownership:**
```bash
ls -la logs artifacts audit
```

**Fix permissions:**
```bash
# Create directories with proper permissions
mkdir -p logs artifacts audit runs corpus workflows
chmod 755 logs artifacts audit runs corpus workflows

# Or use sudo if needed
sudo chown -R $(id -u):$(id -g) logs artifacts audit
```

### Out of disk space

**Check usage:**
```bash
docker system df
```

**Clean up:**
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes (CAUTION: deletes data)
docker volume prune

# Full cleanup (CAUTION: removes everything)
docker system prune -a --volumes
```

## Development Tips

### Live Code Reload

Edit `docker/docker-compose.yml` to mount source code:

```yaml
services:
  app:
    volumes:
      - ../src:/app/src
      - ../dashboards:/app/dashboards
      # Streamlit will auto-reload on file changes
```

### Debug Mode

Set in `.env`:
```bash
LOG_LEVEL=DEBUG
```

### Use Local Redis

For development, use host Redis instead of container:

```yaml
# In docker-compose.yml
environment:
  REDIS_URL: redis://host.docker.internal:6379/0
```

### Run Tests

```bash
docker-compose -f docker/docker-compose.yml exec app python -m pytest tests/
```

## Production Deployment

### 1. Build Production Images

```bash
# Tag with version
docker build -f docker/Dockerfile.app -t djp-workflow-app:1.0.0 .
docker build -f docker/Dockerfile.worker -t djp-workflow-worker:1.0.0 .

# Tag as latest
docker tag djp-workflow-app:1.0.0 djp-workflow-app:latest
docker tag djp-workflow-worker:1.0.0 djp-workflow-worker:latest
```

### 2. Push to Registry

```bash
# Docker Hub
docker tag djp-workflow-app:1.0.0 username/djp-workflow-app:1.0.0
docker push username/djp-workflow-app:1.0.0

# Private registry
docker tag djp-workflow-app:1.0.0 registry.example.com/djp-workflow-app:1.0.0
docker push registry.example.com/djp-workflow-app:1.0.0
```

### 3. Deploy to Kubernetes

Use the Dockerfiles with Kubernetes manifests. Health checks map directly to probes:

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: djp-app
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: app
        image: djp-workflow-app:1.0.0
        ports:
        - containerPort: 8501
        - containerPort: 8080
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

### 4. Production Environment Variables

Ensure these are set in production:

```bash
# Required
OPENAI_API_KEY=sk-prod-key-here
REDIS_URL=redis://prod-redis:6379/0
QUEUE_BACKEND=redis

# Recommended
LOG_LEVEL=WARNING
MAX_JOB_RETRIES=5
BUILD_VERSION=1.0.0
GIT_SHA=abc123
BUILD_DATE=2025-10-04

# Optional features
FEATURE_MULTI_REGION=true
REGIONS=us-east-1,us-west-2
PRIMARY_REGION=us-east-1
```

## Helper Tools

### Makefile Commands

```bash
# From docker/ directory
make help        # Show all commands
make build       # Build images
make up-d        # Start in background
make logs        # View all logs
make health      # Check service health
make scale       # Scale workers (WORKERS=N)
make clean       # Remove everything
```

### PowerShell Script

```powershell
# From docker/ directory
.\start-docker.ps1 -Help                    # Show help
.\start-docker.ps1 -Background              # Start detached
.\start-docker.ps1 -Build -Workers 3        # Build + 3 workers
.\start-docker.ps1 -Clean -Build            # Clean rebuild
```

### Bash Script

```bash
# From docker/ directory
./start-docker.sh -h              # Show help
./start-docker.sh -b              # Start detached
./start-docker.sh -B -w 3         # Build + 3 workers
./start-docker.sh -c -B           # Clean rebuild
```

## File Structure

```
docker/
├── Dockerfile.app          # Application container definition
├── Dockerfile.worker       # Worker container definition
├── docker-compose.yml      # Service orchestration
├── .env.example           # Environment template
├── Makefile               # Helper commands
├── start-docker.ps1       # PowerShell launcher
├── start-docker.sh        # Bash launcher
└── README.md              # Detailed documentation
```

## Security Notes

1. **Non-root users**: Both containers run as non-root (UIDs 1000, 1001)
2. **Read-only configs**: Configuration directories mounted read-only
3. **No secrets in images**: API keys via environment variables only
4. **Network isolation**: Services on internal bridge network
5. **Health checks**: All containers monitored for availability

## Support

For detailed documentation, see:
- `docker/README.md` - Complete Docker documentation
- `README.md` - Main project documentation
- `docs/OPERATIONS.md` - Operations guide

For issues:
1. Check service logs
2. Verify health endpoints
3. Review environment configuration
4. Consult troubleshooting section above
