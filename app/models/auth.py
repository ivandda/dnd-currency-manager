import uuid

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.database.database import Base


class User(Base):
    __tablename__ = "users"
    # id = Column(Integer, primary_key=True, index=True, nullable=False)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="player", nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)
