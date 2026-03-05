from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.database import engine

# Import all models so SQLModel registers them
import app.models  # noqa: F401

# Import routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.parties import router as parties_router
from app.api.transfers import router as transfers_router
from app.api.transactions import router as transactions_router
from app.api.joint_payments import router as joint_payments_router
from app.api.sse import router as sse_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup (development only)."""
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="D&D Currency Manager",
    description="Real-time currency management for D&D parties on LAN",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow any origin since this is a LAN-only app.
# Devices connect via different IPs (localhost, 192.168.x.x, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(sse_router)


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "D&D Currency Manager"}


@app.get("/api/network/lan-url")
def get_lan_url(request: Request):
    """Return the shareable LAN URL for other players to connect.

    Detection priority:
    1. LAN_IP environment variable (user-configured, most reliable)
    2. Request Host header (works when accessed via LAN IP already)
    3. UDP socket outbound IP (works outside Docker)
    """
    import os
    import socket

    lan_ip: str | None = None

    # 1. User-configured env var — most reliable since Docker can't
    #    see the host's real network interfaces
    env_ip = os.environ.get("LAN_IP", "").strip()
    if env_ip and env_ip not in ("localhost", "127.0.0.1"):
        lan_ip = env_ip

    # 2. Use the Host header from the incoming request
    #    (works when someone already accesses via LAN IP)
    if not lan_ip:
        host_header = request.headers.get("host", "")
        host_part = host_header.split(":")[0]
        if host_part and host_part not in ("localhost", "127.0.0.1"):
            lan_ip = host_part

    # 3. UDP socket trick — find the outbound network interface IP.
    #    Inside Docker this gives the container IP, but outside Docker
    #    it gives the real LAN IP.
    if not lan_ip:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            candidate = s.getsockname()[0]
            s.close()
            # Skip Docker-internal IPs (172.x.x.x are often Docker networks)
            if not candidate.startswith("127."):
                lan_ip = candidate
        except Exception:
            pass

    if lan_ip:
        return {"lan_url": f"http://{lan_ip}:3000", "ip": lan_ip}

    return {"lan_url": None, "ip": None}


