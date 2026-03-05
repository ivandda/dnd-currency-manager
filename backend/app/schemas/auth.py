from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """Request body for user registration."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    """Request body for user login."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Response body containing the access token."""

    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
