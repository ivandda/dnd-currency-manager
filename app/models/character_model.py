from sqlalchemy import Column, Integer, TIMESTAMP, text, String, ForeignKey

from app.database.database import Base


class Characters(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text("now()"), nullable=False)
    # wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
