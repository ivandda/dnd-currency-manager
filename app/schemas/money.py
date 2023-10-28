from pydantic import BaseModel
from typing import Optional


class Money(BaseModel):
    platinum: Optional[int] = 0
    gold: Optional[int] = 0
    electrum: Optional[int] = 0
    silver: Optional[int] = 0
    copper: Optional[int] = 0
