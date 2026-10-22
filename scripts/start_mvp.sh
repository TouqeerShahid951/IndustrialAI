#!/bin/zsh
set -eu
cd "$(dirname "$0")/.."
MVP_PORT="${MVP_PORT:-8008}"
.venv/bin/python -m backend.manage check
npm --prefix frontend run build
.venv/bin/python -m backend.worker &
MVP_WORKER_PID=$!
trap 'kill "$MVP_WORKER_PID" 2>/dev/null || true' EXIT INT TERM
print "Industrial AI: http://127.0.0.1:$MVP_PORT"
print 'First-run operator password: var/mvp/operator-password.txt (local file, never logged).'
.venv/bin/python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port "$MVP_PORT"
