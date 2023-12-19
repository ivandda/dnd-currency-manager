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
    role: str | None = None


class UserInDB(User):
    hashed_password: str
