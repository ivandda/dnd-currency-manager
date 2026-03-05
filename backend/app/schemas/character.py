from datetime import datetime
from pydantic import BaseModel


class CharacterResponse(BaseModel):
    """Full character response with balance breakdown."""

    id: int
    name: str
    character_class: str
    balance_cp: int
    balance_display: dict[str, int] = {}
    is_active: bool
    party_id: int
    user_id: int

    model_config = {"from_attributes": True}
