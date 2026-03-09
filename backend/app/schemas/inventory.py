from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.inventory import InventoryEventType


class InventoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description_md: str = Field(default="", max_length=10000)
    amount: int = Field(default=1, ge=0)
    owner_character_id: Optional[int] = None
    is_public: bool = True


class InventoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description_md: Optional[str] = Field(default=None, max_length=10000)
    amount: Optional[int] = Field(default=None, ge=0)
    is_public: Optional[bool] = None


class InventoryTransferRequest(BaseModel):
    owner_character_id: Optional[int] = None


class InventoryItemResponse(BaseModel):
    id: int
    party_id: int
    name: str
    description_md: str
    amount: int
    owner_character_id: Optional[int]
    owner_name: Optional[str] = None
    is_public: bool
    is_active: bool
    created_by_user_id: int
    updated_by_user_id: int
    created_at: datetime
    updated_at: datetime
    can_edit: bool


class InventoryHistoryEntryResponse(BaseModel):
    id: int
    event_type: InventoryEventType
    item_id: int
    item_name: Optional[str] = None
    timestamp: datetime
    actor_username: Optional[str] = None
    redacted: bool
    summary: str
    old_owner_name: Optional[str] = None
    new_owner_name: Optional[str] = None
    old_amount: Optional[int] = None
    new_amount: Optional[int] = None
    old_is_public: Optional[bool] = None
    new_is_public: Optional[bool] = None


class InventoryHistoryListResponse(BaseModel):
    events: list[InventoryHistoryEntryResponse]
