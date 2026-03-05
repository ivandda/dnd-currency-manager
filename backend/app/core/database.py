from sqlmodel import Session, create_engine
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, echo=False)


def get_session():
    """FastAPI dependency that provides a database session."""
    with Session(engine) as session:
        yield session
