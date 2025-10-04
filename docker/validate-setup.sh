#!/bin/bash
# DJP Workflow Platform - Docker Setup Validator
# Validates Docker configuration and prerequisites

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

function header() {
    echo -e "\n${CYAN}=== $1 ===${NC}\n"
}

function check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

function check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

function check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

header "Checking Prerequisites"

# Docker
if command -v docker &> /dev/null; then
    VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    check_pass "Docker installed: $VERSION"

    # Check Docker daemon
    if docker ps &> /dev/null; then
        check_pass "Docker daemon is running"
    else
        check_fail "Docker daemon is not running"
    fi
else
    check_fail "Docker not installed"
fi

# Docker Compose
if command -v docker-compose &> /dev/null; then
    VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    check_pass "Docker Compose installed: $VERSION"
else
    check_fail "Docker Compose not installed"
fi

# Git
if command -v git &> /dev/null; then
    VERSION=$(git --version | cut -d' ' -f3)
    check_pass "Git installed: $VERSION"
else
    check_warn "Git not installed (optional but recommended)"
fi

# Python (for health checks)
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version | cut -d' ' -f2)
    check_pass "Python 3 installed: $VERSION"
else
    check_warn "Python 3 not installed (optional, for local testing)"
fi

header "Checking File Structure"

# Required files
FILES=(
    "docker/Dockerfile.app"
    "docker/Dockerfile.worker"
    "docker/docker-compose.yml"
    "docker/.env.example"
    "requirements.txt"
    "requirements-cloud.txt"
    "src/ops/health_server.py"
    "src/queue/worker.py"
    "dashboards/app.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "Found: $file"
    else
        check_fail "Missing: $file"
    fi
done

# Required directories
DIRS=(
    "src"
    "dashboards"
    "scripts"
    "templates"
    "schemas"
    "policies"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "Found: $dir/"
    else
        check_fail "Missing: $dir/"
    fi
done

header "Checking Configuration"

# Environment file
if [ -f ".env" ]; then
    check_pass "Environment file exists: .env"

    # Check for API key
    if grep -q "OPENAI_API_KEY=" .env && ! grep -q "OPENAI_API_KEY=sk-your" .env; then
        check_pass "OPENAI_API_KEY configured"
    else
        check_warn "OPENAI_API_KEY not configured in .env"
    fi

    # Check Redis URL
    if grep -q "REDIS_URL=" .env; then
        check_pass "REDIS_URL configured"
    else
        check_warn "REDIS_URL not set (will use default)"
    fi
else
    check_warn ".env file not found (will need to create from .env.example)"
fi

header "Checking Docker Images"

# Check if images exist
if docker images | grep -q "djp-workflow-app"; then
    check_pass "App image exists"
else
    check_warn "App image not built yet (run: docker-compose build)"
fi

if docker images | grep -q "djp-workflow-worker"; then
    check_pass "Worker image exists"
else
    check_warn "Worker image not built yet (run: docker-compose build)"
fi

header "Checking Ports"

# Check if ports are available
PORTS=(8501 8080 6379)
for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -an | grep -q ":$port.*LISTEN" 2>/dev/null; then
        check_warn "Port $port is already in use"
    else
        check_pass "Port $port is available"
    fi
done

header "Checking Docker Compose Configuration"

# Validate docker-compose.yml
if docker-compose -f docker/docker-compose.yml config > /dev/null 2>&1; then
    check_pass "docker-compose.yml is valid"
else
    check_fail "docker-compose.yml has errors"
fi

# Check volume paths
if [ -d "logs" ] || mkdir -p logs; then
    check_pass "logs/ directory ready"
fi

if [ -d "artifacts" ] || mkdir -p artifacts; then
    check_pass "artifacts/ directory ready"
fi

if [ -d "audit" ] || mkdir -p audit; then
    check_pass "audit/ directory ready"
fi

header "Checking System Resources"

# Docker resources
DOCKER_MEM=$(docker system info 2>/dev/null | grep "Total Memory" | awk '{print $3}')
if [ -n "$DOCKER_MEM" ]; then
    check_pass "Docker memory: ${DOCKER_MEM}GiB"
    # Convert to GB and check if > 4
    MEM_GB=$(echo "$DOCKER_MEM" | sed 's/GiB//')
    if (( $(echo "$MEM_GB < 4" | bc -l 2>/dev/null || echo "0") )); then
        check_warn "Docker has less than 4GB RAM (recommended: 4GB+)"
    fi
fi

# Disk space
DISK_FREE=$(df -h . | tail -1 | awk '{print $4}')
check_pass "Free disk space: $DISK_FREE"

header "Checking Running Containers"

# Check if DJP containers are running
if docker ps --filter "label=com.djp.service" --format "{{.Names}}" | grep -q "djp"; then
    echo -e "${CYAN}Running DJP containers:${NC}"
    docker ps --filter "label=com.djp.service" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    # Check health
    if docker ps --filter "health=healthy" --filter "label=com.djp.service" | grep -q "djp-app"; then
        check_pass "App container is healthy"
    else
        check_warn "App container may not be healthy"
    fi
else
    check_warn "No DJP containers running (start with: docker-compose up)"
fi

header "Summary"

echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Your Docker setup is ready.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Configure .env with your API keys"
    echo "  2. Run: docker-compose -f docker/docker-compose.yml up"
    echo "  3. Access dashboard at http://localhost:8501"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Setup is mostly ready with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Review warnings above and proceed with caution."
else
    echo -e "${RED}✗ Found $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before proceeding."
    exit 1
fi

echo ""
