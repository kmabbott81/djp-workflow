#!/bin/bash
# Codespaces startup script - Auto-start FastAPI server
# Sprint 55 Week 3

set -e

echo "🚀 Starting OpenAI Agents Workflows Dev Environment..."

# Start Redis
echo "📦 Starting Redis..."
redis-server --daemonize yes --bind 127.0.0.1 --port 6379
sleep 2

# Check Redis is running
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis running on port 6379"
else
    echo "⚠️  Redis failed to start (non-blocking)"
fi

# Create logs directory
mkdir -p /tmp/codespaces-logs

# Start FastAPI server in background with logging
echo "🌐 Starting FastAPI server on port 8000..."
nohup python -m uvicorn src.webapi:app --host 0.0.0.0 --port 8000 --reload \
    > /tmp/codespaces-logs/uvicorn.log 2>&1 &

# Wait for server to be ready
echo "⏳ Waiting for server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/_stcore/health > /dev/null 2>&1; then
        echo "✅ FastAPI server ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "⚠️  Server startup timeout (check logs at /tmp/codespaces-logs/uvicorn.log)"
        exit 1
    fi
done

# Display access information
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Dev Environment Ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Direct URL to Dev UI:"
echo "   https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/static/dev/action-runner.html"
echo ""
echo "🔗 Alternative URLs:"
echo "   API Root: https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/"
echo "   API Docs: https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/docs"
echo "   Health:   https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/_stcore/health"
echo ""
echo "📋 Features Available:"
echo "   ✅ Gmail send action (demo mode)"
echo "   ✅ Outlook send action (demo mode)"
echo "   ✅ Email preview with HTML rendering"
echo "   ✅ Demo outbox (localStorage)"
echo "   ✅ Base64 attachment encoding"
echo ""
echo "📝 View server logs:"
echo "   tail -f /tmp/codespaces-logs/uvicorn.log"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Keep script running (Codespaces needs this)
wait
