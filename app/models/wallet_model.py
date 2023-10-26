from sqlalchemy import Column, Integer, TIMESTAMP, text, String, ForeignKey

from app.database.database import Base


# class Wallet(Base):
#     __tablename__ = "wallets"
#
#     id = Column(Integer, primary_key=True, nullable=False)
#     money = Column(Integer, server_default="0", nullable=False)
#     owner_name = Column(String, nullable=False)
#     created_at = Column(TIMESTAMP(timezone=True),
#                         server_default=text("now()"), nullable=False)
#     character_owner_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"),
#                        unique=True,nullable=False)
