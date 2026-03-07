from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PartyCreate(BaseModel):
    """Request body for creating a new party."""

    name: str = Field(min_length=1, max_length=100)
    use_gold: bool = True
    use_electrum: bool = False
    use_platinum: bool = False


class PartyJoin(BaseModel):
    """Request body for joining a party."""

    character_name: str = Field(min_length=1, max_length=100)
    character_class: str = Field(min_length=1, max_length=50)


class PartyResponse(BaseModel):
    """Party details response."""

    id: int
    name: str
    code: str
    dm_id: int
    is_active: bool
    use_gold: bool
    use_electrum: bool
    use_platinum: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PartyDetailResponse(PartyResponse):
    """Party details including character list."""

    dm_username: str
    my_coin_settings: "CoinSettingsResponse"
    characters: list["CharacterInParty"] = []


class CharacterInParty(BaseModel):
    """Character summary within a party listing."""

    id: int
    name: str
    character_class: str
    balance_cp: int
    balance_display: dict[str, int] = {}
    is_active: bool
    user_id: int
    username: str

    model_config = {"from_attributes": True}


class KickRequest(BaseModel):
    """Request body for kicking a character from a party."""

    character_id: int


class PartyUpdateCoins(BaseModel):
    """Request body for updating a user's coin settings."""

    use_gold: Optional[bool] = None
    use_electrum: Optional[bool] = None
    use_platinum: Optional[bool] = None


class CoinSettingsResponse(BaseModel):
    """Current user coin settings inside a party."""

    use_gold: bool
    use_electrum: bool
    use_platinum: bool
