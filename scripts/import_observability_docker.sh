#!/bin/bash
# Fully Automated Observability Import for Docker Setup
# Handles Prometheus + Grafana with zero manual steps

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_API_KEY="${GRAFANA_API_KEY}"
PROM_CONTAINER="${PROM_CONTAINER:-prom}"
GRAFANA_CONTAINER="${GRAFANA_CONTAINER:-grafana}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 Fully Automated Observability Import${NC}"
echo "=========================================="
echo ""

# Validate inputs
if [ -z "$GRAFANA_API_KEY" ]; then
    echo -e "${RED}✗ GRAFANA_API_KEY not set${NC}"
    exit 1
fi

# Check Docker containers exist
if ! docker ps --filter "name=$PROM_CONTAINER" --format '{{.Names}}' | grep -q "$PROM_CONTAINER"; then
    echo -e "${RED}✗ Prometheus container '$PROM_CONTAINER' not found${NC}"
    exit 1
fi

if ! docker ps --filter "name=$GRAFANA_CONTAINER" --format '{{.Names}}' | grep -q "$GRAFANA_CONTAINER"; then
    echo -e "${RED}✗ Grafana container '$GRAFANA_CONTAINER' not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker containers found${NC}"
echo ""

# ============================================================================
# 1. Import Prometheus Alert Rules (Fully Automated)
# ============================================================================

echo -e "${BLUE}📊 Step 1: Importing Prometheus Alert Rules${NC}"
echo "-------------------------------------------"
echo ""

ALERTS_FILE="$PROJECT_ROOT/observability/templates/prometheus-alerts.yml"

if [ ! -f "$ALERTS_FILE" ]; then
    echo -e "${RED}✗ Alerts file not found: $ALERTS_FILE${NC}"
    exit 1
fi

echo "→ Copying alert rules to Prometheus container..."
docker cp "$ALERTS_FILE" "$PROM_CONTAINER:/etc/prometheus/alerts.yml"
echo -e "${GREEN}✓ Alert rules copied${NC}"

echo "→ Updating Prometheus configuration..."
# Get current config
docker exec "$PROM_CONTAINER" cat /etc/prometheus/prometheus.yml > /tmp/prom-config-backup.yml

# Check if rule_files already exists
if docker exec "$PROM_CONTAINER" grep -q "rule_files:" /etc/prometheus/prometheus.yml 2>/dev/null; then
    echo "  rule_files section exists, checking if alerts.yml is included..."
    if docker exec "$PROM_CONTAINER" grep -q "alerts.yml" /etc/prometheus/prometheus.yml; then
        echo -e "${GREEN}✓ alerts.yml already configured${NC}"
    else
        echo "  Adding alerts.yml to existing rule_files..."
        docker exec "$PROM_CONTAINER" sh -c "sed -i '/rule_files:/a\  - \"alerts.yml\"' /etc/prometheus/prometheus.yml"
        echo -e "${GREEN}✓ alerts.yml added to rule_files${NC}"
    fi
else
    echo "  Adding rule_files section..."
    docker exec "$PROM_CONTAINER" sh -c "cat >> /etc/prometheus/prometheus.yml << 'EOF'

# Alert rules
rule_files:
  - \"alerts.yml\"
EOF"
    echo -e "${GREEN}✓ rule_files section added${NC}"
fi

echo "→ Reloading Prometheus configuration..."
# Try lifecycle reload first (if enabled)
if curl -s -X POST http://localhost:9090/-/reload > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus reloaded via API${NC}"
else
    echo "  API reload not available, restarting container..."
    docker restart "$PROM_CONTAINER" > /dev/null
    echo "  Waiting for Prometheus to start..."
    sleep 5
    echo -e "${GREEN}✓ Prometheus container restarted${NC}"
fi

# Verify alerts loaded
sleep 2
RULES_CHECK=$(curl -s http://localhost:9090/api/v1/rules)
if echo "$RULES_CHECK" | grep -q "relay_api_golden_signals"; then
    echo -e "${GREEN}✓ Alert rules loaded successfully!${NC}"
    ALERT_COUNT=$(echo "$RULES_CHECK" | grep -o '"alert"' | wc -l)
    echo "  Loaded $ALERT_COUNT alert rules"
else
    echo -e "${YELLOW}⚠ Could not verify alert rules (Prometheus may need more time)${NC}"
fi

echo ""

# ============================================================================
# 2. Import Grafana Dashboard (Fully Automated)
# ============================================================================

echo -e "${BLUE}📈 Step 2: Importing Grafana Dashboard${NC}"
echo "--------------------------------------"
echo ""

DASHBOARD_FILE="$PROJECT_ROOT/observability/dashboards/golden-signals.json"

if [ ! -f "$DASHBOARD_FILE" ]; then
    echo -e "${RED}✗ Dashboard file not found: $DASHBOARD_FILE${NC}"
    exit 1
fi

echo "→ Connecting to Grafana..."
if ! curl -s --connect-timeout 5 "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot reach Grafana at $GRAFANA_URL${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Grafana is reachable${NC}"

echo "→ Importing dashboard..."
RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $GRAFANA_API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$DASHBOARD_FILE" \
    "$GRAFANA_URL/api/dashboards/db")

# Check response
if echo "$RESPONSE" | grep -q '"status":"success"'; then
    DASHBOARD_URL=$(echo "$RESPONSE" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Dashboard imported successfully!${NC}"
    echo "  Dashboard URL: $GRAFANA_URL$DASHBOARD_URL"
elif echo "$RESPONSE" | grep -q '"message"'; then
    ERROR_MSG=$(echo "$RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
    echo -e "${RED}✗ Dashboard import failed: $ERROR_MSG${NC}"
    exit 1
else
    echo -e "${RED}✗ Dashboard import failed with unknown error${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

echo ""

# ============================================================================
# 3. Verify Installation
# ============================================================================

echo -e "${BLUE}🔍 Step 3: Verifying Installation${NC}"
echo "----------------------------------"
echo ""

echo "→ Checking Prometheus alerts..."
ALERTS=$(curl -s http://localhost:9090/api/v1/alerts)
if echo "$ALERTS" | grep -q '"state"'; then
    echo -e "${GREEN}✓ Prometheus alerts API responding${NC}"
else
    echo -e "${YELLOW}⚠ Prometheus alerts API not responding yet${NC}"
fi

echo "→ Checking Grafana dashboard..."
DASHBOARDS=$(curl -s \
    -H "Authorization: Bearer $GRAFANA_API_KEY" \
    "$GRAFANA_URL/api/search?type=dash-db")

if echo "$DASHBOARDS" | grep -q "Golden Signals"; then
    echo -e "${GREEN}✓ Dashboard found in Grafana${NC}"
else
    echo -e "${YELLOW}⚠ Dashboard not yet visible in search${NC}"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "=========================================="
echo -e "${GREEN}✅ Import Complete!${NC}"
echo "=========================================="
echo ""
echo "📊 Prometheus:"
echo "   URL: http://localhost:9090"
echo "   Alerts: http://localhost:9090/alerts"
echo "   Rules: http://localhost:9090/rules"
echo ""
echo "📈 Grafana:"
echo "   URL: $GRAFANA_URL"
echo "   Dashboard: ${GRAFANA_URL}${DASHBOARD_URL:-/dashboards}"
echo ""
echo "Next steps:"
echo "1. Open Grafana and verify the dashboard renders correctly"
echo "2. Check Prometheus alerts page to see configured rules"
echo "3. Configure Prometheus data source in Grafana if needed"
echo "4. Set up notification channels for alerts"
echo ""
echo -e "${GREEN}All observability assets imported successfully! 🎉${NC}"
echo ""

exit 0
