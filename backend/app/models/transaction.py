from typing import Optional
from enum import Enum
from sqlmodel import Field, SQLModel
from datetime import datetime, timezone


class TransactionType(str, Enum):
    """Types of currency transactions."""

    TRANSFER = "transfer"           # P2P character-to-character
    DM_GRANT = "dm_grant"           # DM gives money (loot)
    DM_DEDUCT = "dm_deduct"         # DM removes money (god mode)
    JOINT_PAYMENT = "joint_payment" # Joint payment deduction
    SPEND = "spend"                 # Player spends on NPC/shop
    SELF_ADD = "self_add"           # Player adds money to own wallet


class Transaction(SQLModel, table=True):
    """Immutable record of a currency movement. Cannot be altered or deleted."""

    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_type: TransactionType
    amount_cp: int  # Always positive; type and sender/receiver determine direction
    reason: Optional[str] = Field(default=None, max_length=500)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    party_id: int = Field(foreign_key="party.id")
    # Null sender = DM-generated funds (dm_grant)
    sender_id: Optional[int] = Field(default=None, foreign_key="character.id")
    # Null receiver = money removed from economy (joint_payment NPC cost)
    receiver_id: Optional[int] = Field(default=None, foreign_key="character.id")
    # Link to joint payment record if applicable
    joint_payment_id: Optional[int] = Field(default=None, foreign_key="jointpayment.id")
