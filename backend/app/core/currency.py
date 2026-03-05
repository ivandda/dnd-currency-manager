"""Currency conversion engine for D&D standard denominations.

All values are stored internally as Copper Pieces (CP).
Exchange rates (standard D&D):
  1 Platinum (PP) = 10 Gold (GP)
  1 Gold (GP)     = 10 Silver (SP)
  1 Silver (SP)   = 10 Copper (CP)
  1 Electrum (EP) = 5 Silver (SP) = 50 Copper (CP)
"""

import random
from dataclasses import dataclass

# Exchange rates in copper pieces
COPPER_PER_SILVER = 10
COPPER_PER_ELECTRUM = 50  # 1 EP = 5 SP = 50 CP
COPPER_PER_GOLD = 100
COPPER_PER_PLATINUM = 1000

# Maps for conversion
COIN_TO_CP: dict[str, int] = {
    "pp": COPPER_PER_PLATINUM,
    "gp": COPPER_PER_GOLD,
    "ep": COPPER_PER_ELECTRUM,
    "sp": COPPER_PER_SILVER,
    "cp": 1,
}

COIN_NAMES: dict[str, str] = {
    "pp": "Platinum",
    "gp": "Gold",
    "ep": "Electrum",
    "sp": "Silver",
    "cp": "Copper",
}


@dataclass
class CurrencyBreakdown:
    """A breakdown of a copper amount into individual coin types."""

    pp: int = 0
    gp: int = 0
    ep: int = 0
    sp: int = 0
    cp: int = 0

    def to_dict(self) -> dict[str, int]:
        return {"pp": self.pp, "gp": self.gp, "ep": self.ep, "sp": self.sp, "cp": self.cp}

    def to_display_dict(
        self,
        use_platinum: bool = False,
        use_gold: bool = True,
        use_electrum: bool = False,
    ) -> dict[str, int]:
        """Return only enabled coins with non-zero values."""
        result = {}
        if use_platinum and self.pp > 0:
            result["pp"] = self.pp
        if use_gold and self.gp > 0:
            result["gp"] = self.gp
        if use_electrum and self.ep > 0:
            result["ep"] = self.ep
        if self.sp > 0:
            result["sp"] = self.sp
        if self.cp > 0:
            result["cp"] = self.cp
        # Show at least copper if everything is 0
        if not result:
            result["cp"] = 0
        return result


def coins_to_cp(**coins: int) -> int:
    """Convert a mix of coins to total copper pieces.

    Args:
        pp: Platinum pieces
        gp: Gold pieces
        ep: Electrum pieces
        sp: Silver pieces
        cp: Copper pieces

    Returns:
        Total value in copper pieces.

    Example:
        >>> coins_to_cp(gp=1, sp=5, cp=2)
        152
    """
    total = 0
    for coin_type, amount in coins.items():
        if coin_type not in COIN_TO_CP:
            raise ValueError(f"Unknown coin type: {coin_type}")
        if amount < 0:
            raise ValueError(f"Coin amount cannot be negative: {coin_type}={amount}")
        total += amount * COIN_TO_CP[coin_type]
    return total


def cp_to_breakdown(
    total_cp: int,
    use_platinum: bool = False,
    use_gold: bool = True,
    use_electrum: bool = False,
) -> CurrencyBreakdown:
    """Convert copper pieces to the cleanest display format using enabled coins.

    Copper and Silver are always enabled.

    Args:
        total_cp: Total amount in copper pieces.
        use_platinum: Whether platinum coins are enabled.
        use_gold: Whether gold coins are enabled.
        use_electrum: Whether electrum coins are enabled.

    Returns:
        CurrencyBreakdown with the cleanest representation.

    Example:
        >>> cp_to_breakdown(152, use_gold=True)
        CurrencyBreakdown(pp=0, gp=1, ep=0, sp=5, cp=2)
    """
    remaining = total_cp
    breakdown = CurrencyBreakdown()

    if use_platinum:
        breakdown.pp = remaining // COPPER_PER_PLATINUM
        remaining %= COPPER_PER_PLATINUM

    if use_gold:
        breakdown.gp = remaining // COPPER_PER_GOLD
        remaining %= COPPER_PER_GOLD

    if use_electrum:
        breakdown.ep = remaining // COPPER_PER_ELECTRUM
        remaining %= COPPER_PER_ELECTRUM

    # Silver and copper are always enabled
    breakdown.sp = remaining // COPPER_PER_SILVER
    remaining %= COPPER_PER_SILVER

    breakdown.cp = remaining

    return breakdown


def cp_to_single_currency(total_cp: int, target: str) -> float:
    """Convert copper to a single target currency for the 'view all as X' toggle.

    Args:
        total_cp: Total amount in copper pieces.
        target: Target coin type ('pp', 'gp', 'ep', 'sp', 'cp').

    Returns:
        The equivalent value as a float (may have decimals).

    Example:
        >>> cp_to_single_currency(152, 'gp')
        1.52
    """
    if target not in COIN_TO_CP:
        raise ValueError(f"Unknown coin type: {target}")
    return total_cp / COIN_TO_CP[target]


def split_amount(total_cp: int, num_participants: int) -> list[int]:
    """Split a copper amount among participants as equally as possible.

    The indivisible remainder (if any) is randomly assigned to one participant.

    Args:
        total_cp: Total amount to split in copper.
        num_participants: Number of participants.

    Returns:
        A list of amounts (in CP) for each participant.

    Example:
        >>> split_amount(100, 3)  # Could return [34, 33, 33] (random)
    """
    if num_participants <= 0:
        raise ValueError("Number of participants must be positive")
    if total_cp < 0:
        raise ValueError("Amount to split cannot be negative")

    base_share = total_cp // num_participants
    remainder = total_cp % num_participants

    shares = [base_share] * num_participants

    if remainder > 0:
        # Randomly pick one participant to receive the extra copper
        lucky_index = random.randint(0, num_participants - 1)
        shares[lucky_index] += remainder

    return shares
