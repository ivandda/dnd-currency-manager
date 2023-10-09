from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# this is the shema (from pydantic) for defining the shape of the requests (for validation)
class CharacterCreate(BaseModel):
    email: EmailStr
    password: str


class CharacterResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        orm_mode = True
