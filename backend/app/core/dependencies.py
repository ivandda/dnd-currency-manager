"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import decode_token
from app.models.user import User
from app.models.party import Party
from app.models.character import Character


def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    """Extract and validate the current user from the Authorization header.

    Expects: Authorization: Bearer <access_token>
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ")[1]
    payload = decode_token(token)

    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def get_party_by_code(
    code: str,
    session: Session = Depends(get_session),
) -> Party:
    """Fetch a party by its join code. Raises 404 if not found."""
    statement = select(Party).where(Party.code == code)
    party = session.exec(statement).first()

    if party is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found",
        )
    return party


def require_active_party(
    party: Party = Depends(get_party_by_code),
) -> Party:
    """Ensure the party is active (not archived)."""
    if not party.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This party has been archived",
        )
    return party


def require_dm(
    current_user: User = Depends(get_current_user),
    party: Party = Depends(get_party_by_code),
) -> User:
    """Ensure the current user is the DM of the given party."""
    if party.dm_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Dungeon Master can perform this action",
        )
    return current_user


def get_user_character_in_party(
    current_user: User = Depends(get_current_user),
    party: Party = Depends(get_party_by_code),
    session: Session = Depends(get_session),
) -> Character:
    """Get the current user's active character in the given party.

    Raises 403 if the user has no active character in this party.
    """
    statement = select(Character).where(
        Character.user_id == current_user.id,
        Character.party_id == party.id,
        Character.is_active == True,  # noqa: E712
    )
    character = session.exec(statement).first()

    if character is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have an active character in this party",
        )
    return character
