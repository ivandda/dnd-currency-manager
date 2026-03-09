from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class PartyCoinPreference(SQLModel, table=True):
    """Per-user coin display/input preferences scoped to a party."""

    __table_args__ = (
        UniqueConstraint("party_id", "user_id", name="uq_party_coin_preference_party_user"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    party_id: int = Field(foreign_key="party.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    use_gold: bool = Field(default=True)
    use_electrum: bool = Field(default=False)
    use_platinum: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
