from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.joint_payment import JointPaymentStatus


class JointPaymentCreate(BaseModel):
    """Create a joint payment request."""

    character_ids: list[int] = Field(min_length=1)
    amount: dict[str, int] = Field(
        description="Total coins to split, e.g. {'gp': 100}"
    )
    reason: Optional[str] = Field(default=None, max_length=500)
    # When set, pooled money goes to this character instead of disappearing
    receiver_character_id: Optional[int] = None


class JointPaymentAction(BaseModel):
    """Accept or reject a joint payment."""

    # No body needed — action is determined by the endpoint URL


class ParticipantResponse(BaseModel):
    """A participant in a joint payment."""

    character_id: int
    character_name: str
    share_cp: int
    share_display: dict[str, int] = {}
    has_accepted: bool


class JointPaymentResponse(BaseModel):
    """A joint payment record with participant details."""

    id: int
    creator_character_id: Optional[int]
    creator_name: Optional[str] = None
    creator_is_dm: bool
    receiver_character_id: Optional[int] = None
    receiver_name: Optional[str] = None
    total_amount_cp: int
    total_amount_display: dict[str, int] = {}
    reason: Optional[str]
    status: JointPaymentStatus
    created_at: datetime
    participants: list[ParticipantResponse] = []
