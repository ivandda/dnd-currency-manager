from typing import TYPE_CHECKING, Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.models.character import Character
    from app.models.party import Party


class User(SQLModel, table=True):
    """Physical user account. Can be a DM or Player in different parties."""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    characters: List["Character"] = Relationship(back_populates="user")
    parties_as_dm: List["Party"] = Relationship(back_populates="dm")
