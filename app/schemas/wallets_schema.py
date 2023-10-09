from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# this is the shema (from pydantic) for defining the shape of the requests (for validation)
class WalletBase(BaseModel):
    owner_name: str
    money: Optional[int] = None


class WalletCreate(WalletBase):
    pass


class WalletUpdate(WalletBase):
    pass


class WalletResponse(BaseModel):
    id: int
    owner_name: str
    money: int
    created_at: datetime

    # class Config:
    #     orm_mode = True
