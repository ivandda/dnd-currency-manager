"""Party management endpoints: create, join, leave, kick, archive, list."""

import random
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.dependencies import (
    get_current_user,
    get_party_by_code,
    get_user_character_in_party,
    require_active_party,
    require_dm,
    require_party_member_or_dm,
)
from app.core.coin_preferences import get_party_coin_config, upsert_party_coin_config
from app.core.currency import cp_to_breakdown
from app.core.events import event_manager
from app.models.user import User
from app.models.party import Party
from app.models.character import Character
from app.schemas.party import (
    CharacterInParty,
    CharacterSettingsResponse,
    CharacterSettingsUpdate,
    KickRequest,
    PartyCreate,
    PartyDetailResponse,
    PartyJoin,
    PartyResponse,
    PartyUpdateCoins,
    CoinSettingsResponse,
)
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/api/parties", tags=["parties"])


def _generate_party_code(session: Session, length: int = 4) -> str:
    """Generate a unique alphanumeric party code."""
    chars = string.ascii_uppercase + string.digits
    for _ in range(100):  # max attempts
        code = "".join(random.choices(chars, k=length))
        existing = session.exec(select(Party).where(Party.code == code)).first()
        if not existing:
            return code
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate unique party code",
    )


def _build_character_response(
    char: Character,
    party: Party,
    session: Session,
    coin_settings: CoinSettingsResponse,
    viewer_user_id: int,
    viewer_is_dm: bool,
) -> CharacterInParty:
    """Build a CharacterInParty response with balance display and username."""
    can_view_balance = viewer_is_dm or char.user_id == viewer_user_id or char.is_balance_public
    breakdown = cp_to_breakdown(
        char.balance_cp if can_view_balance else 0,
        use_platinum=coin_settings.use_platinum,
        use_gold=coin_settings.use_gold,
        use_electrum=coin_settings.use_electrum,
    )
    user = session.get(User, char.user_id)
    return CharacterInParty(
        id=char.id,
        name=char.name,
        character_class=char.character_class,
        balance_cp=char.balance_cp if can_view_balance else 0,
        balance_display=breakdown.to_display_dict(
            use_platinum=coin_settings.use_platinum,
            use_gold=coin_settings.use_gold,
            use_electrum=coin_settings.use_electrum,
        ),
        balance_visible_to_viewer=can_view_balance,
        is_balance_public=char.is_balance_public,
        is_active=char.is_active,
        user_id=char.user_id,
        username=user.username if user else "Unknown",
    )


@router.post("", response_model=PartyResponse, status_code=status.HTTP_201_CREATED)
def create_party(
    body: PartyCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new party. The creating user becomes the DM."""
    code = _generate_party_code(session)

    party = Party(
        name=body.name,
        code=code,
        dm_id=current_user.id,
        use_gold=body.use_gold,
        use_electrum=body.use_electrum,
        use_platinum=body.use_platinum,
    )
    session.add(party)
    session.commit()
    session.refresh(party)

    return party


@router.get("", response_model=list[PartyResponse])
def list_my_parties(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List all parties where the current user is DM or has a character."""
    # Parties as DM
    dm_parties = session.exec(
        select(Party).where(Party.dm_id == current_user.id)
    ).all()

    # Parties as player
    player_party_ids = session.exec(
        select(Character.party_id).where(
            Character.user_id == current_user.id,
            Character.is_active == True,  # noqa: E712
        )
    ).all()

    player_parties = []
    if player_party_ids:
        player_parties = session.exec(
            select(Party).where(Party.id.in_(player_party_ids))
        ).all()

    # Combine and deduplicate
    all_parties = {p.id: p for p in list(dm_parties) + list(player_parties)}
    return list(all_parties.values())


@router.get("/{code}", response_model=PartyDetailResponse)
def get_party_detail(
    party: Party = Depends(get_party_by_code),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
):
    """Get party details including characters. Requires membership."""
    viewer_is_dm = party.dm_id == current_user.id
    coin_config = get_party_coin_config(session, party, current_user.id)
    my_coin_settings = CoinSettingsResponse(
        use_gold=coin_config.use_gold,
        use_electrum=coin_config.use_electrum,
        use_platinum=coin_config.use_platinum,
    )

    # Get all characters
    characters = session.exec(
        select(Character).where(Character.party_id == party.id)
    ).all()

    dm_user = session.get(User, party.dm_id)

    return PartyDetailResponse(
        id=party.id,
        name=party.name,
        code=party.code,
        dm_id=party.dm_id,
        dm_username=dm_user.username if dm_user else "Unknown",
        is_active=party.is_active,
        use_gold=party.use_gold,
        use_electrum=party.use_electrum,
        use_platinum=party.use_platinum,
        my_coin_settings=my_coin_settings,
        created_at=party.created_at,
        characters=[
            _build_character_response(
                c,
                party,
                session,
                my_coin_settings,
                current_user.id,
                viewer_is_dm,
            )
            for c in characters
        ],
    )


@router.post("/{code}/join", response_model=CharacterInParty)
async def join_party(
    body: PartyJoin,
    party: Party = Depends(require_active_party),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Join a party by creating a character. Cannot join as DM of same party."""
    if party.dm_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The DM cannot join their own party as a player",
        )

    # Check if user already has an active character in this party
    existing = session.exec(
        select(Character).where(
            Character.user_id == current_user.id,
            Character.party_id == party.id,
            Character.is_active == True,  # noqa: E712
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active character in this party",
        )

    character = Character(
        name=body.character_name,
        character_class=body.character_class,
        user_id=current_user.id,
        party_id=party.id,
    )
    session.add(character)
    session.commit()
    session.refresh(character)

    await event_manager.broadcast(party.id, "party_update", {"party_id": party.id})

    coin_config = get_party_coin_config(session, party, current_user.id)
    my_coin_settings = CoinSettingsResponse(
        use_gold=coin_config.use_gold,
        use_electrum=coin_config.use_electrum,
        use_platinum=coin_config.use_platinum,
    )
    return _build_character_response(
        character,
        party,
        session,
        my_coin_settings,
        current_user.id,
        False,
    )


@router.post("/{code}/leave", response_model=MessageResponse)
async def leave_party(
    party: Party = Depends(get_party_by_code),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Leave a party (archives the character)."""
    character = session.exec(
        select(Character).where(
            Character.user_id == current_user.id,
            Character.party_id == party.id,
            Character.is_active == True,  # noqa: E712
        )
    ).first()

    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have an active character in this party",
        )

    character.is_active = False
    session.add(character)
    session.commit()

    await event_manager.broadcast(party.id, "party_update", {"party_id": party.id})

    return MessageResponse(message=f"{character.name} has left the party")


@router.post("/{code}/kick", response_model=MessageResponse)
async def kick_character(
    body: KickRequest,
    party: Party = Depends(require_active_party),
    dm_user: User = Depends(require_dm),
    session: Session = Depends(get_session),
):
    """DM kicks a character from the party."""
    character = session.get(Character, body.character_id)

    if not character or character.party_id != party.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found in this party",
        )

    if not character.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character is already inactive",
        )

    character.is_active = False
    session.add(character)
    session.commit()

    await event_manager.broadcast(party.id, "party_update", {"party_id": party.id})

    return MessageResponse(message=f"{character.name} has been kicked from the party")


@router.patch("/{code}/archive", response_model=PartyResponse)
async def archive_party(
    party: Party = Depends(get_party_by_code),
    dm_user: User = Depends(require_dm),
    session: Session = Depends(get_session),
):
    """DM archives a party (no new transactions allowed)."""
    party.is_active = False
    session.add(party)
    session.commit()
    session.refresh(party)

    await event_manager.broadcast(party.id, "party_update", {"party_id": party.id})

    return party


@router.patch("/{code}/my-coins", response_model=CoinSettingsResponse)
async def update_coin_config(
    body: PartyUpdateCoins,
    party: Party = Depends(require_active_party),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
):
    """Update the current user's coin settings for this party."""
    updated = upsert_party_coin_config(
        session=session,
        party=party,
        user_id=current_user.id,
        use_gold=body.use_gold,
        use_electrum=body.use_electrum,
        use_platinum=body.use_platinum,
    )
    return CoinSettingsResponse(
        use_gold=updated.use_gold,
        use_electrum=updated.use_electrum,
        use_platinum=updated.use_platinum,
    )


@router.patch("/{code}/my-character-settings", response_model=CharacterSettingsResponse)
async def update_my_character_settings(
    body: CharacterSettingsUpdate,
    party: Party = Depends(require_active_party),
    character: Character = Depends(get_user_character_in_party),
    session: Session = Depends(get_session),
):
    """Update current player's character settings for this party."""
    if body.is_balance_public is not None:
        character.is_balance_public = body.is_balance_public
        session.add(character)
        session.commit()
        await event_manager.broadcast(party.id, "party_update", {"party_id": party.id})

    return CharacterSettingsResponse(is_balance_public=character.is_balance_public)
