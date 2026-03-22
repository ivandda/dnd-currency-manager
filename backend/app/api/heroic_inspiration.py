"""Heroic Inspiration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.dependencies import get_user_character_in_party, require_active_party, require_dm
from app.core.events import event_manager
from app.models.character import Character
from app.models.party import Party
from app.models.user import User
from app.schemas.heroic_inspiration import HeroicInspirationActionResponse

router = APIRouter(prefix="/api/parties/{code}/heroic-inspiration", tags=["heroic-inspiration"])


def _get_active_character_in_party(session: Session, party_id: int, character_id: int) -> Character:
    character = session.exec(
        select(Character).where(
            Character.id == character_id,
            Character.party_id == party_id,
            Character.is_active == True,  # noqa: E712
        )
    ).first()
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found in this party",
        )
    return character


async def _broadcast_and_respond(
    *,
    party_id: int,
    character: Character,
    actor_user_id: int,
    action: str,
) -> HeroicInspirationActionResponse:
    payload = HeroicInspirationActionResponse(
        character_id=character.id,
        has_heroic_inspiration=character.has_heroic_inspiration,
        action=action,
        target_user_id=character.user_id,
        actor_user_id=actor_user_id,
    )
    await event_manager.broadcast(party_id, "heroic_inspiration_update", payload.model_dump())
    return payload


@router.post("/{character_id}/grant", response_model=HeroicInspirationActionResponse)
async def grant_heroic_inspiration(
    character_id: int,
    party: Party = Depends(require_active_party),
    dm_user: User = Depends(require_dm),
    session: Session = Depends(get_session),
):
    """Grant Heroic Inspiration to an active party member."""
    character = _get_active_character_in_party(session, party.id, character_id)
    if character.has_heroic_inspiration:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Character already has Heroic Inspiration",
        )

    character.has_heroic_inspiration = True
    session.add(character)
    session.commit()
    session.refresh(character)

    return await _broadcast_and_respond(
        party_id=party.id,
        character=character,
        actor_user_id=dm_user.id,
        action="granted",
    )


@router.post("/{character_id}/revoke", response_model=HeroicInspirationActionResponse)
async def revoke_heroic_inspiration(
    character_id: int,
    party: Party = Depends(require_active_party),
    dm_user: User = Depends(require_dm),
    session: Session = Depends(get_session),
):
    """Revoke Heroic Inspiration from an active party member."""
    character = _get_active_character_in_party(session, party.id, character_id)
    if not character.has_heroic_inspiration:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Character does not have Heroic Inspiration",
        )

    character.has_heroic_inspiration = False
    session.add(character)
    session.commit()
    session.refresh(character)

    return await _broadcast_and_respond(
        party_id=party.id,
        character=character,
        actor_user_id=dm_user.id,
        action="revoked",
    )


@router.post("/use", response_model=HeroicInspirationActionResponse)
async def use_heroic_inspiration(
    party: Party = Depends(require_active_party),
    character: Character = Depends(get_user_character_in_party),
    session: Session = Depends(get_session),
):
    """Spend the current player's Heroic Inspiration."""
    if not character.has_heroic_inspiration:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You do not have Heroic Inspiration",
        )

    character.has_heroic_inspiration = False
    session.add(character)
    session.commit()
    session.refresh(character)

    return await _broadcast_and_respond(
        party_id=party.id,
        character=character,
        actor_user_id=character.user_id,
        action="used",
    )
