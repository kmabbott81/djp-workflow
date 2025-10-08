#!/usr/bin/env sh
set -e
PORT="${PORT:-8000}"
exec python -m uvicorn src.webapi:app --host 0.0.0.0 --port "$PORT"
