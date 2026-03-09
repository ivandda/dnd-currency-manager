#!/bin/sh
# Auto-detect LAN IP and start the app.
# Usage: ./start.sh        (foreground)
#        ./start.sh -d      (detached / background)

is_valid_lan_ip() {
    case "$1" in
        ""|127.*|0.*|169.254.*|localhost)
            return 1
            ;;
        *.*.*.*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Respect explicit user override first.
if is_valid_lan_ip "${LAN_IP:-}"; then
    DETECTED_IP="$LAN_IP"
else
    DETECTED_IP=""
fi

# macOS: detect the default route interface first, then common fallbacks.
if [ -z "$DETECTED_IP" ] && command -v ipconfig >/dev/null 2>&1; then
    if command -v route >/dev/null 2>&1; then
        DEFAULT_IF=$(route -n get default 2>/dev/null | awk '/interface:/{print $2; exit}')
        if [ -n "$DEFAULT_IF" ]; then
            DETECTED_IP=$(ipconfig getifaddr "$DEFAULT_IF" 2>/dev/null)
        fi
    fi

    if ! is_valid_lan_ip "$DETECTED_IP"; then
        for IFACE in en0 en1 en2; do
            DETECTED_IP=$(ipconfig getifaddr "$IFACE" 2>/dev/null)
            if is_valid_lan_ip "$DETECTED_IP"; then
                break
            fi
        done
    fi
fi

# Linux: prefer routing table source IP; fall back to hostname -I.
if [ -z "$DETECTED_IP" ] && command -v ip >/dev/null 2>&1; then
    DETECTED_IP=$(ip route get 1 2>/dev/null | awk '{for (i=1; i<=NF; i++) if ($i=="src") {print $(i+1); exit}}')
fi

if [ -z "$DETECTED_IP" ] && command -v hostname >/dev/null 2>&1; then
    DETECTED_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi

if ! is_valid_lan_ip "$DETECTED_IP"; then
    DETECTED_IP=""
fi

if [ -z "$DETECTED_IP" ]; then
    echo "⚠️  Could not detect LAN IP. Share URL will show localhost."
    echo "   You can set it manually: LAN_IP=x.x.x.x ./start.sh"
    echo "   If players are on restricted Wi-Fi, use a tunnel (for example: ngrok)."
else
    echo "🌐 Detected LAN IP: $DETECTED_IP"
    echo "📡 Players connect at: http://$DETECTED_IP:3000"
fi

LAN_IP="$DETECTED_IP"
export LAN_IP
exec env LAN_IP="$LAN_IP" docker compose up "$@"
