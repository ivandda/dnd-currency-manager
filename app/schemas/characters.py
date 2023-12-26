from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.schemas.parties import PartyResponse


class CharacterCreate(BaseModel):
    name: str


class CharacterResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class CharacterAllInfoResponse(BaseModel):
    id: UUID
    name: str
    wallet: dict
    parties: List[PartyResponse]
    created_at: datetime


class CharacterIdLists(BaseModel):
    ids: List[UUID]
