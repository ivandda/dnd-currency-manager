import ipaddress
import os
import socket
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings

# Import all models so SQLModel registers them
import app.models  # noqa: F401

# Import routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.parties import router as parties_router
from app.api.transfers import router as transfers_router
from app.api.transactions import router as transactions_router
from app.api.joint_payments import router as joint_payments_router
from app.api.inventory import router as inventory_router
from app.api.heroic_inspiration import router as heroic_inspiration_router
from app.api.sse import router as sse_router


settings = get_settings()


app = FastAPI(
    title="D&D Currency Manager",
    description="Real-time currency management for D&D parties on LAN",
    version="0.1.0",
)

# CORS — allow any origin since this is a LAN-only app.
# Devices connect via different IPs (localhost, 192.168.x.x, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(parties_router)
app.include_router(transfers_router)
app.include_router(transactions_router)
app.include_router(joint_payments_router)
app.include_router(inventory_router)
app.include_router(heroic_inspiration_router)
app.include_router(sse_router)


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "D&D Currency Manager"}


def _is_valid_share_ip(value: str) -> bool:
    """Return True when value is a non-loopback IPv4 address."""
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False

    return (
        ip.version == 4
        and not ip.is_loopback
        and not ip.is_unspecified
        and not ip.is_link_local
    )


def _ip_from_host_header(host_header: str) -> str | None:
    host = host_header.split(":")[0].strip("[]")
    if _is_valid_share_ip(host):
        return host
    return None


@app.get("/api/network/lan-url")
def get_lan_url(request: Request):
    """Return the shareable LAN URL for other players to connect.

    Detection priority:
    1. LAN_IP environment variable (user-configured, most reliable)
    2. Request Host header (works when accessed via LAN IP already)
    3. UDP socket outbound IP (works outside Docker)
    """
    lan_ip: str | None = None
    source = "none"
    warnings: list[str] = []
    frontend_url = urlparse(settings.FRONTEND_URL)
    frontend_scheme = frontend_url.scheme or "http"
    frontend_port = frontend_url.port or (443 if frontend_scheme == "https" else 3000)
    in_docker = os.path.exists("/.dockerenv")

    # 1. User-configured env var — most reliable since Docker can't
    #    see the host's real network interfaces
    env_ip = os.environ.get("LAN_IP", "").strip()
    if _is_valid_share_ip(env_ip):
        lan_ip = env_ip
        source = "env"

    # 2. Use the Host header from the incoming request
    #    (works when someone already accesses via LAN IP).
    #    Only trust raw IP hosts; skip domains/localhost values.
    if not lan_ip:
        host_ip = _ip_from_host_header(request.headers.get("host", ""))
        if host_ip:
            lan_ip = host_ip
            source = "host_header"

    # 3. UDP socket trick — find the outbound network interface IP.
    #    Inside Docker this gives the container IP, but outside Docker
    #    it gives the real LAN IP.
    if not lan_ip and not in_docker:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Use a short timeout so this doesn't block the request
                # thread for a long OS-level timeout in restricted networks.
                s.settimeout(0.5)
                s.connect(("8.8.8.8", 80))
                candidate = s.getsockname()[0]
                if _is_valid_share_ip(candidate):
                    lan_ip = candidate
                    source = "udp_socket"
        except Exception:
            pass

    if in_docker and not os.environ.get("LAN_IP", "").strip():
        warnings.append(
            "Running in Docker without LAN_IP set can prevent accurate host LAN detection."
        )
    if not lan_ip:
        warnings.append(
            "If players are on guest/public Wi-Fi, client isolation may block direct LAN access."
        )

    if lan_ip:
        return {
            "lan_url": f"{frontend_scheme}://{lan_ip}:{frontend_port}",
            "ip": lan_ip,
            "source": source,
            "warnings": warnings,
        }

    return {"lan_url": None, "ip": None, "source": source, "warnings": warnings}
