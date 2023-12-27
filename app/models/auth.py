import uuid

from sqlalchemy import Column, String, Boolean, TIMESTAMP, text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)

    parties = relationship("Parties", secondary="dm_parties", back_populates="users")
    characters = relationship("Characters", secondary="users_characters", back_populates="users")


dm_parties = Table(
    "dm_parties",
    Base.metadata,
    Column("dm_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("party_id", UUID(as_uuid=True), ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True),
)
