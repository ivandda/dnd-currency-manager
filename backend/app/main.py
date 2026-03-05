from contextlib import asynccontextmanager

from fastapi import FastAPI
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
