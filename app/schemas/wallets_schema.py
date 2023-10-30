from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# this is the shema (from pydantic) for defining the shape of the requests (for validation)
class WalletBase(BaseModel):
    money: Optional[int] = None


class WalletCreate(WalletBase):
    character_owner_id: int
    pass


class WalletUpdate(WalletBase):
    pass


class WalletResponse(BaseModel):
    id: int
    money: int
    created_at: datetime
    character_owner_id: int

    class Config:
    #     orm_mode = True
        from_attributes = True
