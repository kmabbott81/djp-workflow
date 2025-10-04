#!/bin/bash
# DJP Workflow Platform - Docker Quick Start Script (Bash)
# Launches the complete Docker stack with health checks

set -e

# Script configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE="../.env"
ENV_EXAMPLE=".env.example"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
BACKGROUND=false
BUILD=false
WORKERS=1
CLEAN=false

function show_help() {
    echo -e "${CYAN}DJP Workflow Platform - Docker Quick Start${NC}"
    echo ""
    echo "Usage: ./start-docker.sh [options]"
    echo ""
    echo "Options:"
    echo "  -b, --background   Start services in background (detached mode)"
    echo "  -B, --build        Build images before starting"
    echo "  -w, --workers N    Number of worker instances (default: 1)"
    echo "  -c, --clean        Clean up containers and volumes before starting"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start-docker.sh                    # Start in foreground"
    echo "  ./start-docker.sh -b                 # Start in background"
    echo "  ./start-docker.sh -B -w 3            # Build and start with 3 workers"
    echo "  ./start-docker.sh -c -B              # Clean rebuild"
    echo ""
}

function check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check Docker
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        echo -e "${GREEN}✓ Docker found: $DOCKER_VERSION${NC}"
    else
        echo -e "${RED}✗ Docker not found. Please install Docker.${NC}"
        exit 1
    fi

    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        echo -e "${GREEN}✓ Docker Compose found: $COMPOSE_VERSION${NC}"
    else
        echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose.${NC}"
        exit 1
    fi

    # Check Docker daemon
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✓ Docker daemon is running${NC}"
    else
        echo -e "${RED}✗ Docker daemon is not running. Please start Docker.${NC}"
        exit 1
    fi
}

function check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        echo ""
        echo -e "${YELLOW}Warning: .env file not found at $ENV_FILE${NC}"
        echo ""

        if [ -f "$ENV_EXAMPLE" ]; then
            read -p "Copy from .env.example? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cp "$ENV_EXAMPLE" "$ENV_FILE"
                echo -e "${GREEN}✓ Created .env from template${NC}"
                echo ""
                echo -e "${RED}IMPORTANT: Edit $ENV_FILE and add your API keys!${NC}"
                echo ""
                read -p "Continue anyway? (y/n) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 0
                fi
            fi
        else
            echo -e "${RED}Error: $ENV_EXAMPLE not found either!${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Environment file found: $ENV_FILE${NC}"
    fi
}

function cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up existing containers and volumes...${NC}"
    docker-compose -f "$COMPOSE_FILE" down -v
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

function build_images() {
    echo ""
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker-compose -f "$COMPOSE_FILE" build
    echo -e "${GREEN}✓ Build complete${NC}"
}

function start_services() {
    local detached=$1
    local num_workers=$2

    echo ""
    echo -e "${YELLOW}Starting DJP Workflow Platform...${NC}"
    echo -e "${CYAN}  Workers: $num_workers${NC}"
    echo -e "${CYAN}  Mode: $([ "$detached" = true ] && echo "Background" || echo "Foreground")${NC}"
    echo ""

    local args=()
    if [ "$detached" = true ]; then
        args+=("-d")
    fi
    args+=("--scale" "worker=$num_workers")

    docker-compose -f "$COMPOSE_FILE" up "${args[@]}"

    if [ "$detached" = true ]; then
        echo ""
        echo -e "${GREEN}✓ Services started successfully!${NC}"
        echo ""
        echo -e "${CYAN}Access points:${NC}"
        echo -e "  Dashboard:    ${NC}http://localhost:8501"
        echo -e "  Health Check: ${NC}http://localhost:8080/ready"
        echo -e "  Redis:        ${NC}localhost:6379"
        echo ""
        echo -e "${CYAN}Useful commands:${NC}"
        echo "  docker-compose -f $COMPOSE_FILE logs -f      # View logs"
        echo "  docker-compose -f $COMPOSE_FILE ps           # Service status"
        echo "  docker-compose -f $COMPOSE_FILE down         # Stop services"
        echo ""

        # Wait and check health
        echo -e "${YELLOW}Checking service health in 5 seconds...${NC}"
        sleep 5

        if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ App health check passed${NC}"
        else
            echo -e "${YELLOW}⚠ App health check failed (may still be starting)${NC}"
        fi

        echo ""
        echo -e "${CYAN}Service status:${NC}"
        docker-compose -f "$COMPOSE_FILE" ps
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--background)
            BACKGROUND=true
            shift
            ;;
        -B|--build)
            BUILD=true
            shift
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Main script execution
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   DJP Workflow Platform - Docker Launcher    ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════╝${NC}"
echo ""

# Run checks
check_prerequisites
check_env_file

# Clean if requested
if [ "$CLEAN" = true ]; then
    cleanup
fi

# Build if requested
if [ "$BUILD" = true ]; then
    build_images
fi

# Start services
start_services "$BACKGROUND" "$WORKERS"

echo ""
echo -e "${GREEN}Done! 🚀${NC}"
echo ""
