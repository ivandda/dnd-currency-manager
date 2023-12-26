from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None


class CreateUser(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserInDB(User):
    hashed_password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True
