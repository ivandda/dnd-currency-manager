from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class PartyCreate(BaseModel):
    name: str


class PartyAddCharacters(BaseModel):
    characters_id: List[int]


class PartyResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        orm_mode = True
