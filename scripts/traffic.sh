#!/usr/bin/env bash
# Generate staged traffic to API endpoints
# Usage: ./scripts/traffic.sh [count] [interval]

set -e

COUNT=${1:-50}
INTERVAL=${2:-2}
BASE_URL="${STAGING_URL:-https://relay-production-f2a6.up.railway.app}"

ENDPOINTS=(
    "/_stcore/health"
    "/version"
    "/ready"
    "/api/templates"
    "/metrics"
)

echo "Generating $COUNT requests to $BASE_URL with ${INTERVAL}s interval..."

for i in $(seq 1 $COUNT); do
    idx=$((i % ${#ENDPOINTS[@]}))
    endpoint="${ENDPOINTS[$idx]}"
    url="$BASE_URL$endpoint"

    if http_code=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$url"); then
        if [ "$http_code" = "200" ]; then
            echo "[$i/$COUNT] $endpoint - ✅ $http_code"
        else
            echo "[$i/$COUNT] $endpoint - ⚠️  $http_code"
        fi
    else
        echo "[$i/$COUNT] $endpoint - ❌ ERROR"
    fi

    if [ "$i" -lt "$COUNT" ]; then
        sleep "$INTERVAL"
    fi
done

echo ""
echo "Traffic generation complete. Check Prometheus/Grafana for updated metrics."
