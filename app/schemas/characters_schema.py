from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.schemas.party_schema import PartyResponse
from app.schemas.wallets_schema import WalletResponse


# this is the shema (from pydantic) for defining the shape of the requests (for validation)
class CharacterCreate(BaseModel):
    name: str


class CharacterResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        # orm_mode = True
        from_attributes = True


class CharacterInfoResponse(BaseModel):
    id: int
    name: str
    wallet: dict
    parties: list[PartyResponse]
    created_at: datetime

