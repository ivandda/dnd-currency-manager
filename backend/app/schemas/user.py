from datetime import datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    """Public user profile."""

    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}
