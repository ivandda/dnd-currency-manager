from datetime import datetime

from pydantic import BaseModel


class PartyCreate(BaseModel):
    name: str


class PartyResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class PartyAllInfoResponse(BaseModel):
    id: int
    name: str
    characters: list
    created_at: datetime