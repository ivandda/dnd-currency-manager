from pydantic import BaseModel
from enum import Enum


class WalletTransfers(BaseModel):
    id: int
    money: int




async def add_money(wallet, money):
    wallet.money += money
    return wallet


async def subtract_money(wallet, money):
    wallet.money -= money
    return wallet
