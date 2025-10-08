#!/usr/bin/env bash
# Quick staging health check
# Usage: ./scripts/check-staging.sh

set -e

BASE_URL="${STAGING_URL:-https://relay-production-f2a6.up.railway.app}"

echo "🔍 Checking staging service: $BASE_URL"
echo ""

# Health check
echo "1. Health Check"
if http_code=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "$BASE_URL/_stcore/health"); then
    if [ "$http_code" = "200" ]; then
        echo "   ✅ Health: HTTP $http_code"
    else
        echo "   ❌ Health: HTTP $http_code"
        exit 1
    fi
else
    echo "   ❌ Health: Connection failed"
    exit 1
fi

# Version check
echo "2. Version Info"
if version=$(curl -s -m 5 "$BASE_URL/version"); then
    echo "   $(echo "$version" | head -c 200)"
else
    echo "   ⚠️  Version endpoint failed"
fi

# Readiness check
echo "3. Readiness Check"
if ready=$(curl -s -m 5 "$BASE_URL/ready"); then
    if echo "$ready" | grep -q '"ready":true'; then
        echo "   ✅ Ready: All checks passed"
    else
        echo "   ⚠️  Ready: Some checks failed"
        echo "   $(echo "$ready" | head -c 200)"
    fi
else
    echo "   ⚠️  Readiness endpoint failed"
fi

# Metrics check
echo "4. Metrics Endpoint"
if metrics=$(curl -s -m 5 "$BASE_URL/metrics" | head -n 5); then
    if echo "$metrics" | grep -q "# HELP"; then
        echo "   ✅ Metrics: Prometheus format detected"
    else
        echo "   ⚠️  Metrics: Unexpected format"
    fi
else
    echo "   ⚠️  Metrics endpoint failed"
fi

echo ""
echo "✅ All critical endpoints operational"
