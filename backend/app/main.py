from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.database import engine

# Import all models so SQLModel registers them
import app.models  # noqa: F401


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

# CORS — allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "D&D Currency Manager"}
