from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class InventoryEventType(str, Enum):
    """Immutable events representing inventory lifecycle changes."""

    ITEM_CREATED = "item_created"
    ITEM_UPDATED = "item_updated"
    ITEM_AMOUNT_CHANGED = "item_amount_changed"
    ITEM_VISIBILITY_CHANGED = "item_visibility_changed"
    ITEM_TRANSFERRED = "item_transferred"
    ITEM_DELETED = "item_deleted"
    ITEM_RESTORED = "item_restored"


class InventoryItem(SQLModel, table=True):
    """Inventory item owned by a party character (or unassigned DM stash)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    party_id: int = Field(foreign_key="party.id", index=True)
    name: str = Field(min_length=1, max_length=120)
    description_md: str = Field(default="", max_length=10000)
    amount: int = Field(default=1, ge=0)
    owner_character_id: Optional[int] = Field(default=None, foreign_key="character.id", index=True)
    is_public: bool = Field(default=True)
    is_active: bool = Field(default=True)

    created_by_user_id: int = Field(foreign_key="user.id")
    updated_by_user_id: int = Field(foreign_key="user.id")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class InventoryEvent(SQLModel, table=True):
    """Immutable event stream for inventory changes."""

    id: Optional[int] = Field(default=None, primary_key=True)
    party_id: int = Field(foreign_key="party.id", index=True)
    item_id: int = Field(foreign_key="inventoryitem.id", index=True)
    event_type: InventoryEventType
    actor_user_id: int = Field(foreign_key="user.id")

    # Snapshots used for permission checks and history rendering
    item_name_snapshot: Optional[str] = Field(default=None, max_length=120)
    owner_character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    old_owner_character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    new_owner_character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    old_amount: Optional[int] = Field(default=None)
    new_amount: Optional[int] = Field(default=None)
    old_is_public: Optional[bool] = Field(default=None)
    new_is_public: Optional[bool] = Field(default=None)
    is_public_snapshot: bool = Field(default=True)
    note: Optional[str] = Field(default=None, max_length=500)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
