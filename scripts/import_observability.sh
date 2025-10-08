#!/bin/bash
# Import Prometheus alerts and Grafana dashboards automatically
# Usage:
#   PROM_URL=http://localhost:9090 \
#   GRAFANA_URL=http://localhost:3000 \
#   GRAFANA_API_KEY=your-api-key \
#   ./scripts/import_observability.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROM_URL="${PROM_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_API_KEY="${GRAFANA_API_KEY}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Files
ALERTS_FILE="$PROJECT_ROOT/observability/dashboards/alerts.json"
DASHBOARD_FILE="$PROJECT_ROOT/observability/dashboards/golden-signals.json"

echo "🔧 Observability Import Tool"
echo "=============================="
echo ""

# Check files exist
if [ ! -f "$ALERTS_FILE" ]; then
    echo -e "${RED}✗ Alerts file not found: $ALERTS_FILE${NC}"
    exit 1
fi

if [ ! -f "$DASHBOARD_FILE" ]; then
    echo -e "${RED}✗ Dashboard file not found: $DASHBOARD_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found alerts and dashboard files${NC}"
echo ""

# ============================================================================
# 1. Import Prometheus Alert Rules
# ============================================================================

echo "📊 Importing Prometheus Alert Rules..."
echo "Target: $PROM_URL"
echo ""

# Convert alerts.json to Prometheus rules format
# Prometheus expects rules in YAML format, not JSON dashboard format
# We need to transform the JSON to Prometheus rule groups

# Check if Prometheus is reachable
if curl -s --connect-timeout 5 "$PROM_URL/-/healthy" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus is reachable${NC}"

    # Note: Prometheus alert rules are typically configured via files, not API
    # For dynamic import, you'd need to:
    # 1. Use Prometheus config reload API (requires --web.enable-lifecycle flag)
    # 2. Or use a tool like promtool to validate and deploy

    echo -e "${YELLOW}⚠ Prometheus alert import requires manual configuration${NC}"
    echo ""
    echo "To import alerts:"
    echo "1. Copy alert rules to Prometheus rules directory"
    echo "2. Update prometheus.yml to include:"
    echo "   rule_files:"
    echo "     - 'alerts.yml'"
    echo "3. Reload Prometheus: curl -X POST $PROM_URL/-/reload"
    echo ""
    echo "Alternative: Use Alertmanager API or Prometheus Operator"
    echo ""

else
    echo -e "${RED}✗ Cannot reach Prometheus at $PROM_URL${NC}"
    echo "Skipping Prometheus import"
    echo ""
fi

# ============================================================================
# 2. Import Grafana Dashboard
# ============================================================================

echo "📈 Importing Grafana Dashboard..."
echo "Target: $GRAFANA_URL"
echo ""

# Check if Grafana API key is provided
if [ -z "$GRAFANA_API_KEY" ]; then
    echo -e "${RED}✗ GRAFANA_API_KEY not set${NC}"
    echo ""
    echo "To get an API key:"
    echo "1. Login to Grafana: $GRAFANA_URL"
    echo "2. Go to Configuration → API Keys (or Admin → Service accounts → Tokens)"
    echo "3. Create new API key with 'Editor' or 'Admin' role"
    echo "4. Copy the key and set: export GRAFANA_API_KEY=your-key"
    echo ""
    exit 1
fi

# Check if Grafana is reachable
if ! curl -s --connect-timeout 5 "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot reach Grafana at $GRAFANA_URL${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Grafana is reachable${NC}"

# Import dashboard
echo "Importing dashboard: Relay Actions API - Golden Signals"

RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $GRAFANA_API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$DASHBOARD_FILE" \
    "$GRAFANA_URL/api/dashboards/db")

# Check response
if echo "$RESPONSE" | grep -q '"status":"success"'; then
    DASHBOARD_URL=$(echo "$RESPONSE" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Dashboard imported successfully!${NC}"
    echo "Dashboard URL: $GRAFANA_URL$DASHBOARD_URL"
    echo ""
elif echo "$RESPONSE" | grep -q '"message"'; then
    ERROR_MSG=$(echo "$RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
    echo -e "${RED}✗ Dashboard import failed: $ERROR_MSG${NC}"
    echo "Full response: $RESPONSE"
    echo ""
    exit 1
else
    echo -e "${RED}✗ Dashboard import failed with unknown error${NC}"
    echo "Response: $RESPONSE"
    echo ""
    exit 1
fi

# ============================================================================
# 3. Verify Installation
# ============================================================================

echo "🔍 Verifying installation..."
echo ""

# List Grafana dashboards
echo "Grafana dashboards:"
DASHBOARDS=$(curl -s \
    -H "Authorization: Bearer $GRAFANA_API_KEY" \
    "$GRAFANA_URL/api/search?type=dash-db")

if echo "$DASHBOARDS" | grep -q "Golden Signals"; then
    echo -e "${GREEN}✓ Golden Signals dashboard found in Grafana${NC}"
else
    echo -e "${YELLOW}⚠ Dashboard not found in search results${NC}"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "=============================="
echo "📋 Import Summary"
echo "=============================="
echo ""
echo "Grafana Dashboard: ✅ Imported"
echo "Prometheus Alerts: ⚠️  Manual configuration required"
echo ""
echo "Next steps:"
echo "1. Open Grafana dashboard to verify panels render correctly"
echo "2. Configure Prometheus data source in Grafana if not already done"
echo "3. Manually configure Prometheus alert rules (see above)"
echo "4. Set up notification channels in Grafana/Alertmanager"
echo ""
echo "For Prometheus alerts, see: observability/templates/alerts.yml"
echo ""

exit 0
