from datetime import datetime

from pydantic import BaseModel

from app.schemas.party import PartyResponse


class CharacterCreate(BaseModel):
    name: str


class CharacterResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class CharacterAllInfoResponse(BaseModel):
    id: int
    name: str
    wallet: dict
    parties: list[PartyResponse]
    created_at: datetime
