from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.coin_preference import PartyCoinPreference
from app.models.party import Party


@dataclass(frozen=True)
class CoinConfig:
    use_gold: bool
    use_electrum: bool
    use_platinum: bool


def get_party_coin_config(session: Session, party: Party, user_id: int) -> CoinConfig:
    """Return this user's coin config for the party, with legacy party fallback."""
    pref = session.exec(
        select(PartyCoinPreference).where(
            PartyCoinPreference.party_id == party.id,
            PartyCoinPreference.user_id == user_id,
        )
    ).first()
    if pref:
        return CoinConfig(
            use_gold=pref.use_gold,
            use_electrum=pref.use_electrum,
            use_platinum=pref.use_platinum,
        )
    return CoinConfig(
        use_gold=party.use_gold,
        use_electrum=party.use_electrum,
        use_platinum=party.use_platinum,
    )


def upsert_party_coin_config(
    session: Session,
    party: Party,
    user_id: int,
    use_gold: bool | None = None,
    use_electrum: bool | None = None,
    use_platinum: bool | None = None,
) -> CoinConfig:
    """Create or update this user's coin config for a party."""
    pref = session.exec(
        select(PartyCoinPreference).where(
            PartyCoinPreference.party_id == party.id,
            PartyCoinPreference.user_id == user_id,
        )
    ).first()
    if not pref:
        pref = PartyCoinPreference(
            party_id=party.id,
            user_id=user_id,
            use_gold=party.use_gold,
            use_electrum=party.use_electrum,
            use_platinum=party.use_platinum,
        )

    if use_gold is not None:
        pref.use_gold = use_gold
    if use_electrum is not None:
        pref.use_electrum = use_electrum
    if use_platinum is not None:
        pref.use_platinum = use_platinum

    session.add(pref)
    session.commit()
    session.refresh(pref)

    return CoinConfig(
        use_gold=pref.use_gold,
        use_electrum=pref.use_electrum,
        use_platinum=pref.use_platinum,
    )
