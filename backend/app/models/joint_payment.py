from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone


class JointPaymentStatus(str, Enum):
    """States of a joint payment request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class JointPayment(SQLModel, table=True):
    """A shared payment request split among multiple characters."""

    id: Optional[int] = Field(default=None, primary_key=True)
    # Creator: character_id if player-initiated, null if DM-initiated
    creator_character_id: Optional[int] = Field(
        default=None, foreign_key="character.id"
    )
    creator_is_dm: bool = Field(default=False)
    party_id: int = Field(foreign_key="party.id")
    total_amount_cp: int
    # When set, pooled money goes to this character. When None, money leaves the economy (NPC spend).
    receiver_character_id: Optional[int] = Field(
        default=None, foreign_key="character.id"
    )
    reason: Optional[str] = Field(default=None, max_length=500)
    status: JointPaymentStatus = Field(default=JointPaymentStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    participants: List["PaymentParticipant"] = Relationship(
        back_populates="joint_payment"
    )


class PaymentParticipant(SQLModel, table=True):
    """A character's participation in a joint payment."""

    id: Optional[int] = Field(default=None, primary_key=True)
    joint_payment_id: int = Field(foreign_key="jointpayment.id")
    character_id: int = Field(foreign_key="character.id")
    share_cp: int  # Pre-calculated share for this participant
    has_accepted: bool = Field(default=False)

    # Relationships
    joint_payment: JointPayment = Relationship(back_populates="participants")
