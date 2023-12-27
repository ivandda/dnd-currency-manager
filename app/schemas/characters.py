import re
from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, constr, field_validator

from app.schemas.parties import PartyResponse


# class CharacterCreate(BaseModel):
#     name: str

class CharacterCreate(BaseModel):
    name: constr(min_length=4) = Field(
        ...,
        description="Valid characters: a-z, A-Z, 0-9, _ , . , -, &,'. Contains at least one character that is not a number. Has a minimum length of four characters"
    )

    @field_validator('name')
    def name_must_match_pattern(cls, v):
        pattern = "^(?=.*[^0-9])[a-zA-Z0-9_.'&-]{4,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid character name. Valid characters: a-z, A-Z, 0-9, _ , . , -, &,'. Contains "
                             "at least one character that is not a number. Has a minimum length of four "
                             "characters")
        return v


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
