#!/bin/sh
set -e

cd /app

if [ "${UV_SYNC_ON_START:-0}" = "1" ]; then
    uv sync --frozen --no-dev
fi

echo "Applying database migrations..."
/app/.venv/bin/alembic upgrade head

if [ "${UVICORN_RELOAD:-0}" = "1" ]; then
    exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi

exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
