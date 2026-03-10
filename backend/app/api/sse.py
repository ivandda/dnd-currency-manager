"""Server-Sent Events (SSE) endpoint for real-time updates."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_session
from app.core.events import event_manager
from app.core.security import decode_token
from app.models.party import Party
from app.models.user import User

router = APIRouter(prefix="/api/sse", tags=["sse"])


def _get_user_from_token_query(
    token: str = Query(..., alias="token"),
    session: Session = Depends(get_session),
) -> User:
    """Authenticate via query parameter token (for EventSource which can't set headers)."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = int(payload["sub"])
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def _get_party(
    code: str,
    session: Session = Depends(get_session),
) -> Party:
    from sqlmodel import select
    party = session.exec(select(Party).where(Party.code == code)).first()
    if party is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Party not found")
    return party


@router.get("/{code}")
async def sse_stream(
    request: Request,
    party: Party = Depends(_get_party),
    current_user: User = Depends(_get_user_from_token_query),
):
    """Subscribe to real-time events for a party.

    Uses query param ?token=<jwt> for authentication (EventSource can't set headers).

    Event types:
    - balance_update: A character's balance changed
    - transaction_new: A new transaction was created
    - joint_payment_update: A joint payment status changed
    - party_update: Party settings changed
    - inventory_update: Inventory items changed
    """
    print(f"[SSE] User {current_user.username} connecting to party {party.code} (id={party.id})", flush=True)
    queue = event_manager.subscribe(party.id)

    async def generate():
        try:
            async for event in event_manager.event_stream(party.id, queue):
                if await request.is_disconnected():
                    break
                yield event
        except Exception as e:
            print(f"[SSE] Error in stream for party {party.code}: {e}", flush=True)
        # event_stream's finally block handles unsubscribe

    return EventSourceResponse(
        generate(),
        ping=15,
    )
