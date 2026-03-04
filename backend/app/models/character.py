from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.party import Party


class Character(SQLModel, table=True):
    """A player's character within a party. Stores balance in copper (CP)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=100)
    character_class: str = Field(max_length=50)  # e.g. "Warrior", "Mage", "Rogue"
    balance_cp: int = Field(default=0)  # All currency stored as copper pieces
    is_active: bool = Field(default=True)  # False = left the party / archived
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user_id: int = Field(foreign_key="user.id")
    party_id: int = Field(foreign_key="party.id")

    # Relationships
    user: "User" = Relationship(back_populates="characters")
    party: "Party" = Relationship(back_populates="characters")
