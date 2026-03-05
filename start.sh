#!/bin/sh
# Auto-detect LAN IP and start the app.
# Usage: ./start.sh        (foreground)
#        ./start.sh -d      (detached / background)

# Detect LAN IP (macOS → Linux fallback)
if command -v ipconfig >/dev/null 2>&1; then
    LAN_IP=$(ipconfig getifaddr en0 2>/dev/null)
fi

if [ -z "$LAN_IP" ]; then
    LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi

if [ -z "$LAN_IP" ]; then
    echo "⚠️  Could not detect LAN IP. Share URL will show localhost."
    echo "   You can set it manually: LAN_IP=x.x.x.x ./start.sh"
else
    echo "🌐 Detected LAN IP: $LAN_IP"
    echo "📡 Players connect at: http://$LAN_IP:3000"
fi

export LAN_IP
exec docker compose up "$@"
