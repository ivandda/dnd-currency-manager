from typing import TYPE_CHECKING, Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.character import Character


class Party(SQLModel, table=True):
    """A game session grouping characters and one DM."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(unique=True, index=True, max_length=10)
    dm_id: int = Field(foreign_key="user.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Coin configuration (Copper and Silver are always enabled)
    use_gold: bool = Field(default=True)
    use_electrum: bool = Field(default=False)
    use_platinum: bool = Field(default=False)

    # Relationships
    dm: "User" = Relationship(back_populates="parties_as_dm")
    characters: List["Character"] = Relationship(back_populates="party")
