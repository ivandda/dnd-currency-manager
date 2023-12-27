import uuid

from sqlalchemy import Column, Integer, TIMESTAMP, text, String, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.database import Base

character_parties = Table(
    "character_parties",
    Base.metadata,
    Column("character_id", UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True),
    Column("party_id", UUID(as_uuid=True), ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True),
)


class Characters(Base):
    __tablename__ = "characters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    parties = relationship("Parties", secondary="character_parties", back_populates="characters")
    users = relationship("User", secondary="users_characters", back_populates="characters")


class Parties(Base):
    __tablename__ = "parties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)

    characters = relationship("Characters", secondary="character_parties", back_populates="parties")
    users = relationship("User", secondary="dm_parties", back_populates="parties")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    money_copper = Column(Integer, server_default="0", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"),
                          unique=True, nullable=False)
