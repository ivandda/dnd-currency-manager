from typing import Literal

from pydantic import BaseModel


class HeroicInspirationActionResponse(BaseModel):
    """Response and SSE payload for Heroic Inspiration changes."""

    character_id: int
    has_heroic_inspiration: bool
    action: Literal["granted", "revoked", "used"]
    target_user_id: int
    actor_user_id: int
