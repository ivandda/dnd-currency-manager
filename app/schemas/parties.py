from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PartyCreate(BaseModel):
    name: str


class PartyResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class PartyAllInfoResponse(BaseModel):
    id: UUID
    name: str
    characters: list
    created_at: datetime
