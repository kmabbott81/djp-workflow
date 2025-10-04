# DJP Workflow Platform - Docker Operations Makefile
# Convenience commands for building, running, and managing containers

.PHONY: help build up down restart logs clean test scale health

# Default target
help:
	@echo "DJP Workflow Platform - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build       - Build all Docker images"
	@echo "  up          - Start all services in foreground"
	@echo "  up-d        - Start all services in background (detached)"
	@echo "  down        - Stop all services"
	@echo "  restart     - Restart all services"
	@echo "  logs        - View logs for all services"
	@echo "  logs-app    - View app logs"
	@echo "  logs-worker - View worker logs"
	@echo "  logs-redis  - View Redis logs"
	@echo "  clean       - Stop and remove all containers and volumes"
	@echo "  scale       - Scale workers (use WORKERS=N)"
	@echo "  health      - Check health of all services"
	@echo "  shell-app   - Open shell in app container"
	@echo "  shell-worker - Open shell in worker container"
	@echo "  test        - Run test suite in containers"
	@echo "  rebuild     - Clean build and start"
	@echo ""
	@echo "Examples:"
	@echo "  make up-d              - Start in background"
	@echo "  make scale WORKERS=3   - Run 3 worker instances"
	@echo "  make logs-app          - View app logs"

# Docker compose file location
COMPOSE_FILE := docker-compose.yml
COMPOSE := docker-compose -f $(COMPOSE_FILE)

# Build all images
build:
	@echo "Building Docker images..."
	$(COMPOSE) build

# Build with no cache
build-no-cache:
	@echo "Building Docker images (no cache)..."
	$(COMPOSE) build --no-cache

# Start services in foreground
up:
	@echo "Starting DJP Workflow Platform..."
	$(COMPOSE) up

# Start services in background
up-d:
	@echo "Starting DJP Workflow Platform (detached)..."
	$(COMPOSE) up -d
	@echo ""
	@echo "Services started successfully!"
	@echo "  Dashboard: http://localhost:8501"
	@echo "  Health:    http://localhost:8080/ready"
	@echo ""
	@echo "Use 'make logs' to view logs"

# Stop services
down:
	@echo "Stopping DJP Workflow Platform..."
	$(COMPOSE) down

# Restart services
restart:
	@echo "Restarting services..."
	$(COMPOSE) restart

# View all logs
logs:
	$(COMPOSE) logs -f

# View app logs
logs-app:
	$(COMPOSE) logs -f app

# View worker logs
logs-worker:
	$(COMPOSE) logs -f worker

# View Redis logs
logs-redis:
	$(COMPOSE) logs -f redis

# Clean up everything (including volumes)
clean:
	@echo "Cleaning up containers and volumes..."
	$(COMPOSE) down -v
	@echo "Cleanup complete!"

# Scale workers (usage: make scale WORKERS=3)
WORKERS ?= 2
scale:
	@echo "Scaling workers to $(WORKERS) instances..."
	$(COMPOSE) up -d --scale worker=$(WORKERS)

# Check health status
health:
	@echo "Checking service health..."
	@echo ""
	@echo "App health:"
	@curl -s http://localhost:8080/health | python -m json.tool || echo "App not responding"
	@echo ""
	@echo "App readiness:"
	@curl -s http://localhost:8080/ready | python -m json.tool || echo "App not ready"
	@echo ""
	@echo "Redis:"
	@$(COMPOSE) exec -T redis redis-cli ping || echo "Redis not responding"
	@echo ""
	@echo "Docker service status:"
	@$(COMPOSE) ps

# Open shell in app container
shell-app:
	$(COMPOSE) exec app /bin/bash

# Open shell in worker container
shell-worker:
	$(COMPOSE) exec worker /bin/bash

# Open Redis CLI
redis-cli:
	$(COMPOSE) exec redis redis-cli

# Run tests in containers
test:
	@echo "Running tests in containers..."
	$(COMPOSE) exec app python -m pytest tests/ || echo "No tests found or tests failed"

# View container stats
stats:
	docker stats $$(docker ps --filter "label=com.djp.service" --format "{{.Names}}")

# Rebuild everything from scratch
rebuild: clean build up-d
	@echo "Rebuild complete!"

# Pull latest base images
pull:
	$(COMPOSE) pull

# Show running containers
ps:
	$(COMPOSE) ps

# Export logs to file
export-logs:
	@echo "Exporting logs to docker_logs.txt..."
	$(COMPOSE) logs --no-color > docker_logs.txt
	@echo "Logs exported to docker_logs.txt"

# Backup Redis data
backup-redis:
	@echo "Creating Redis backup..."
	$(COMPOSE) exec redis redis-cli BGSAVE
	@echo "Backup initiated. Check Redis logs for completion."

# Validate docker-compose file
validate:
	$(COMPOSE) config

# Show disk usage
disk-usage:
	@echo "Docker disk usage:"
	@docker system df
