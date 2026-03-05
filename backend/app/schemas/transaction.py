from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.transaction import TransactionType


class TransferRequest(BaseModel):
    """P2P transfer: character sends money to another character."""

    receiver_id: int
    amount: dict[str, int] = Field(
        description="Coins to send, e.g. {'gp': 5, 'sp': 3}"
    )
    reason: Optional[str] = Field(default=None, max_length=500)


class DMLootRequest(BaseModel):
    """DM loot: grant money to one or more characters."""

    character_ids: list[int] = Field(min_length=1)
    amount: dict[str, int] = Field(
        description="Coins to grant, e.g. {'gp': 10}"
    )
    reason: Optional[str] = Field(default=None, max_length=500)


class DMGodModeRequest(BaseModel):
    """DM god mode: directly add or subtract money from a character."""

    character_id: int
    amount: dict[str, int] = Field(
        description="Coins to add/subtract, e.g. {'gp': 5}"
    )
    is_deduction: bool = False
    reason: Optional[str] = Field(default=None, max_length=500)


class SpendRequest(BaseModel):
    """Player spends money on NPC/shop."""

    amount: dict[str, int] = Field(
        description="Coins to spend, e.g. {'gp': 5, 'sp': 3}"
    )
    reason: str = Field(min_length=1, max_length=500, description="What are you buying?")


class SelfAddRequest(BaseModel):
    """Player adds money to their own wallet (e.g., found loot, sold items)."""

    amount: dict[str, int] = Field(
        description="Coins to add, e.g. {'gp': 10}"
    )
    reason: Optional[str] = Field(default=None, max_length=500)


class TransactionResponse(BaseModel):
    """A single transaction record."""

    id: int
    transaction_type: TransactionType
    amount_cp: int
    amount_display: dict[str, int] = {}
    reason: Optional[str]
    timestamp: datetime
    sender_id: Optional[int]
    sender_name: Optional[str] = None
    receiver_id: Optional[int]
    receiver_name: Optional[str] = None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Paginated transaction list."""

    transactions: list[TransactionResponse]
    total: int
    page: int
    page_size: int
