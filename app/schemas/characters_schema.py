from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# this is the shema (from pydantic) for defining the shape of the requests (for validation)
class CharacterCreate(BaseModel):
    name: str


class CharacterResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        orm_mode = True
