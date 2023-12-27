import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, constr, field_validator


class PartyCreate(BaseModel):
    name: constr(min_length=4) = Field(
        ...,
        description="Valid characters: a-z, A-Z, 0-9, _ , . , -, &,'. Contains at least one character that is not a number. Has a minimum length of four characters"
    )

    @field_validator('name')
    def name_must_match_pattern(cls, v):
        pattern = "^(?=.*[^0-9])[a-zA-Z0-9_.'&-]{4,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid party name. Valid characters: a-z, A-Z, 0-9, _ , . , -, &,'. Contains "
                             "at least one character that is not a number. Has a minimum length of four "
                             "characters")
        return v


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
    dms: list[UUID]
