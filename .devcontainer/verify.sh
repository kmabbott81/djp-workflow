#!/bin/bash
# Codespace verification script
# Run this inside your Codespace to check setup

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Codespace Dev UI Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if we're in a Codespace
if [ -z "$CODESPACE_NAME" ]; then
    echo "⚠️  Not running in a Codespace"
    echo "   CODESPACE_NAME environment variable not set"
    echo ""
else
    echo "✅ Running in Codespace: $CODESPACE_NAME"
    echo ""
fi

# Check Redis
echo "📦 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running on port 6379"
else
    echo "❌ Redis is not running"
    echo "   Try: redis-server --daemonize yes"
fi
echo ""

# Check if FastAPI is running
echo "🌐 Checking FastAPI server..."
if curl -s http://localhost:8000/_stcore/health > /dev/null 2>&1; then
    echo "✅ FastAPI is running on port 8000"
else
    echo "❌ FastAPI is not running on port 8000"
    echo "   Try: bash .devcontainer/startup.sh"
fi
echo ""

# Check if static files exist
echo "📁 Checking static files..."
if [ -f "static/dev/action-runner.html" ]; then
    echo "✅ Dev UI HTML found"
else
    echo "❌ Dev UI HTML not found at static/dev/action-runner.html"
fi

if [ -f "static/dev/action-runner.js" ]; then
    echo "✅ Dev UI JS found"
else
    echo "❌ Dev UI JS not found at static/dev/action-runner.js"
fi
echo ""

# Check startup script
echo "🔧 Checking startup script..."
if [ -f ".devcontainer/startup.sh" ]; then
    echo "✅ Startup script exists"
    if [ -x ".devcontainer/startup.sh" ]; then
        echo "✅ Startup script is executable"
    else
        echo "⚠️  Startup script is not executable"
        echo "   Run: chmod +x .devcontainer/startup.sh"
    fi
else
    echo "❌ Startup script not found"
fi
echo ""

# Generate the correct URL
if [ -n "$CODESPACE_NAME" ] && [ -n "$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN" ]; then
    DEV_UI_URL="https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/static/dev/action-runner.html"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Your Dev UI URL:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "   $DEV_UI_URL"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Test the URL
    echo "🧪 Testing URL accessibility..."
    if curl -s "$DEV_UI_URL" | grep -q "Action Runner" > /dev/null 2>&1; then
        echo "✅ Dev UI is accessible at the URL above!"
    else
        echo "⚠️  Could not verify URL accessibility"
        echo "   This might be a port visibility issue"
        echo ""
        echo "   To fix:"
        echo "   1. Open the PORTS tab (bottom panel in VS Code)"
        echo "   2. Find port 8000"
        echo "   3. Right-click → Port Visibility → Public"
    fi
else
    echo "⚠️  Cannot generate URL - Codespace environment variables not set"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Quick Fixes:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "If Redis is not running:"
echo "  redis-server --daemonize yes"
echo ""
echo "If FastAPI is not running:"
echo "  bash .devcontainer/startup.sh"
echo ""
echo "To check server logs:"
echo "  tail -f /tmp/codespaces-logs/uvicorn.log"
echo ""
echo "To manually start server:"
echo "  python -m uvicorn src.webapi:app --host 0.0.0.0 --port 8000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
