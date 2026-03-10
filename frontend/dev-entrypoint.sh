#!/bin/sh
set -e

cd /app

LOCK_HASH_FILE="/app/node_modules/.lockhash"
CURRENT_HASH="$(cat package.json pnpm-lock.yaml | sha256sum | awk '{print $1}')"

if [ ! -f "$LOCK_HASH_FILE" ] || [ "$(cat "$LOCK_HASH_FILE")" != "$CURRENT_HASH" ]; then
    echo "[frontend] Dependency lock changed (or first run). Installing with pnpm..."
    CI=true pnpm install --frozen-lockfile
    mkdir -p /app/node_modules
    echo "$CURRENT_HASH" > "$LOCK_HASH_FILE"
else
    echo "[frontend] Dependencies are up to date. Skipping install."
fi

exec pnpm dev --hostname 0.0.0.0
