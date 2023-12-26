from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WalletBase(BaseModel):
    money: Optional[int] = None


class WalletResponse(BaseModel):
    id: UUID
    money: int
    created_at: datetime
    character_owner_id: int

    class Config:
        from_attributes = True
