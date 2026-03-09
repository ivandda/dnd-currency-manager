"""Inventory manager endpoints with immutable inventory history."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func

from app.core.database import get_session
from app.core.dependencies import (
    get_party_by_code,
    require_active_party,
    require_party_member_or_dm,
)
from app.core.events import event_manager
from app.models.character import Character
from app.models.inventory import InventoryEvent, InventoryEventType, InventoryItem
from app.models.party import Party
from app.models.user import User
from app.schemas.inventory import (
    InventoryCreateRequest,
    InventoryHistoryEntryResponse,
    InventoryHistoryListResponse,
    InventoryItemResponse,
    InventoryTransferRequest,
    InventoryUpdateRequest,
)

router = APIRouter(prefix="/api/parties/{code}/inventory", tags=["inventory"])

MAX_ACTIVE_ITEMS_PER_PARTY = 100


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_viewer_character(session: Session, party_id: int, user_id: int) -> Optional[Character]:
    return session.exec(
        select(Character).where(
            Character.party_id == party_id,
            Character.user_id == user_id,
            Character.is_active == True,  # noqa: E712
        )
    ).first()


def _get_active_owner_or_400(session: Session, party_id: int, owner_character_id: int) -> Character:
    character = session.get(Character, owner_character_id)
    if not character or character.party_id != party_id or not character.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner must be an active character in this party",
        )
    return character


def _get_item_or_404(
    session: Session,
    party_id: int,
    item_id: int,
    *,
    include_archived: bool,
) -> InventoryItem:
    item = session.get(InventoryItem, item_id)
    if not item or item.party_id != party_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if not include_archived and not item.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


def _can_view_item(item: InventoryItem, *, is_dm: bool, viewer_character_id: Optional[int]) -> bool:
    return is_dm or item.is_public or item.owner_character_id == viewer_character_id


def _can_edit_item(item: InventoryItem, *, is_dm: bool, viewer_character_id: Optional[int]) -> bool:
    return is_dm or item.owner_character_id == viewer_character_id


def _owner_name(session: Session, owner_character_id: Optional[int]) -> Optional[str]:
    if owner_character_id is None:
        return None
    owner = session.get(Character, owner_character_id)
    return owner.name if owner else None


def _ensure_active_item_capacity(session: Session, party_id: int) -> None:
    total_active = session.exec(
        select(func.count(InventoryItem.id)).where(
            InventoryItem.party_id == party_id,
            InventoryItem.is_active == True,  # noqa: E712
        )
    ).one()
    if total_active >= MAX_ACTIVE_ITEMS_PER_PARTY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Party inventory is full ({MAX_ACTIVE_ITEMS_PER_PARTY} active items max)",
        )


def _record_event(
    session: Session,
    *,
    item: InventoryItem,
    event_type: InventoryEventType,
    actor_user_id: int,
    item_name_snapshot: Optional[str] = None,
    owner_character_id: Optional[int] = None,
    old_owner_character_id: Optional[int] = None,
    new_owner_character_id: Optional[int] = None,
    old_amount: Optional[int] = None,
    new_amount: Optional[int] = None,
    old_is_public: Optional[bool] = None,
    new_is_public: Optional[bool] = None,
    is_public_snapshot: Optional[bool] = None,
    note: Optional[str] = None,
) -> None:
    session.add(
        InventoryEvent(
            party_id=item.party_id,
            item_id=item.id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            item_name_snapshot=item_name_snapshot if item_name_snapshot is not None else item.name,
            owner_character_id=item.owner_character_id if owner_character_id is None else owner_character_id,
            old_owner_character_id=old_owner_character_id,
            new_owner_character_id=new_owner_character_id,
            old_amount=old_amount,
            new_amount=new_amount,
            old_is_public=old_is_public,
            new_is_public=new_is_public,
            is_public_snapshot=item.is_public if is_public_snapshot is None else is_public_snapshot,
            note=note,
        )
    )


def _to_item_response(
    item: InventoryItem,
    *,
    session: Session,
    is_dm: bool,
    viewer_character_id: Optional[int],
) -> InventoryItemResponse:
    return InventoryItemResponse(
        id=item.id,
        party_id=item.party_id,
        name=item.name,
        description_md=item.description_md,
        amount=item.amount,
        owner_character_id=item.owner_character_id,
        owner_name=_owner_name(session, item.owner_character_id),
        is_public=item.is_public,
        is_active=item.is_active,
        created_by_user_id=item.created_by_user_id,
        updated_by_user_id=item.updated_by_user_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
        can_edit=_can_edit_item(item, is_dm=is_dm, viewer_character_id=viewer_character_id),
    )


def _event_visible_to_viewer(
    event: InventoryEvent,
    *,
    is_dm: bool,
    viewer_character_id: Optional[int],
) -> bool:
    if is_dm or event.is_public_snapshot:
        return True
    if viewer_character_id is None:
        return False
    return viewer_character_id in {
        event.owner_character_id,
        event.old_owner_character_id,
        event.new_owner_character_id,
    }


def _event_summary(
    event: InventoryEvent,
    *,
    old_owner_name: Optional[str],
    new_owner_name: Optional[str],
) -> str:
    item_name = event.item_name_snapshot or "Item"
    if event.event_type == InventoryEventType.ITEM_CREATED:
        owner_label = new_owner_name or old_owner_name or "Unassigned stash"
        return f"Created '{item_name}' for {owner_label}"
    if event.event_type == InventoryEventType.ITEM_UPDATED:
        return f"Updated details for '{item_name}'"
    if event.event_type == InventoryEventType.ITEM_AMOUNT_CHANGED:
        return f"Changed amount for '{item_name}'"
    if event.event_type == InventoryEventType.ITEM_VISIBILITY_CHANGED:
        return f"Changed visibility for '{item_name}'"
    if event.event_type == InventoryEventType.ITEM_TRANSFERRED:
        src = old_owner_name or "Unassigned stash"
        dst = new_owner_name or "Unassigned stash"
        return f"Transferred '{item_name}' from {src} to {dst}"
    if event.event_type == InventoryEventType.ITEM_DELETED:
        return f"Archived '{item_name}'"
    if event.event_type == InventoryEventType.ITEM_RESTORED:
        return f"Restored '{item_name}'"
    return "Updated inventory"


def _to_history_response(
    event: InventoryEvent,
    *,
    session: Session,
    is_dm: bool,
    viewer_character_id: Optional[int],
) -> InventoryHistoryEntryResponse:
    can_view_full = _event_visible_to_viewer(
        event,
        is_dm=is_dm,
        viewer_character_id=viewer_character_id,
    )
    if not can_view_full:
        return InventoryHistoryEntryResponse(
            id=event.id,
            event_type=event.event_type,
            item_id=event.item_id,
            item_name=None,
            timestamp=event.created_at,
            actor_username=None,
            redacted=True,
            summary="Private item updated",
        )

    actor = session.get(User, event.actor_user_id)
    old_owner_name = _owner_name(session, event.old_owner_character_id)
    new_owner_name = _owner_name(session, event.new_owner_character_id)

    return InventoryHistoryEntryResponse(
        id=event.id,
        event_type=event.event_type,
        item_id=event.item_id,
        item_name=event.item_name_snapshot,
        timestamp=event.created_at,
        actor_username=actor.username if actor else None,
        redacted=False,
        summary=_event_summary(event, old_owner_name=old_owner_name, new_owner_name=new_owner_name),
        old_owner_name=old_owner_name,
        new_owner_name=new_owner_name,
        old_amount=event.old_amount,
        new_amount=event.new_amount,
        old_is_public=event.old_is_public,
        new_is_public=event.new_is_public,
    )


@router.get("", response_model=list[InventoryItemResponse])
def list_inventory_items(
    include_archived: bool = Query(default=True),
    party: Party = Depends(get_party_by_code),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
):
    """List inventory items visible to the current viewer."""
    viewer_char = _get_viewer_character(session, party.id, current_user.id)
    viewer_char_id = viewer_char.id if viewer_char else None
    is_dm = party.dm_id == current_user.id

    statement = select(InventoryItem).where(InventoryItem.party_id == party.id)
    if not include_archived:
        statement = statement.where(InventoryItem.is_active == True)  # noqa: E712
    items = session.exec(statement.order_by(InventoryItem.updated_at.desc())).all()

    visible_items = [
        _to_item_response(item, session=session, is_dm=is_dm, viewer_character_id=viewer_char_id)
        for item in items
        if _can_view_item(item, is_dm=is_dm, viewer_character_id=viewer_char_id)
    ]
    return visible_items


@router.get("/history", response_model=InventoryHistoryListResponse)
def list_inventory_history(
    limit: int = Query(default=200, ge=1, le=500),
    party: Party = Depends(get_party_by_code),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
):
    """List immutable inventory history events with privacy-aware redaction."""
    viewer_char = _get_viewer_character(session, party.id, current_user.id)
    viewer_char_id = viewer_char.id if viewer_char else None
    is_dm = party.dm_id == current_user.id

    events = session.exec(
        select(InventoryEvent)
        .where(InventoryEvent.party_id == party.id)
        .order_by(InventoryEvent.created_at.desc())
        .limit(limit)
    ).all()

    return InventoryHistoryListResponse(
        events=[
            _to_history_response(
                event,
                session=session,
                is_dm=is_dm,
                viewer_character_id=viewer_char_id,
            )
            for event in events
        ]
    )


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    body: InventoryCreateRequest,
    party: Party = Depends(require_active_party),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
):
    """Create a new inventory item."""
    viewer_char = _get_viewer_character(session, party.id, current_user.id)
    viewer_char_id = viewer_char.id if viewer_char else None
    is_dm = party.dm_id == current_user.id

    if not is_dm and viewer_char_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not an active character in this party")

    owner_character_id = body.owner_character_id
    if is_dm:
        if owner_character_id is not None:
            _get_active_owner_or_400(session, party.id, owner_character_id)
    else:
        if owner_character_id is not None and owner_character_id != viewer_char_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Players can only create items for themselves",
            )
        owner_character_id = viewer_char_id

    _ensure_active_item_capacity(session, party.id)

    now = _now()
    item = InventoryItem(
        party_id=party.id,
        name=body.name.strip(),
        description_md=body.description_md,
        amount=body.amount,
        owner_character_id=owner_character_id,
        is_public=body.is_public,
        is_active=True,
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
        created_at=now,
        updated_at=now,
    )

    session.add(item)
    session.flush()
    _record_event(
        session,
        item=item,
        event_type=InventoryEventType.ITEM_CREATED,
        actor_user_id=current_user.id,
        new_owner_character_id=owner_character_id,
        new_amount=item.amount,
        new_is_public=item.is_public,
    )
    session.commit()
    session.refresh(item)

    await event_manager.broadcast(party.id, "inventory_update", {"item_id": item.id})

    return _to_item_response(item, session=session, is_dm=is_dm, viewer_character_id=viewer_char_id)


@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: int,
    body: InventoryUpdateRequest,
    party: Party = Depends(require_active_party),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
):
    """Update mutable item fields (name, description, amount, visibility)."""
    viewer_char = _get_viewer_character(session, party.id, current_user.id)
    viewer_char_id = viewer_char.id if viewer_char else None
    is_dm = party.dm_id == current_user.id

    item = _get_item_or_404(session, party.id, item_id, include_archived=False)
    if not _can_edit_item(item, is_dm=is_dm, viewer_character_id=viewer_char_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to edit this item")

    changed = False
    now = _now()

    details_changed_fields: list[str] = []
    if body.name is not None:
        new_name = body.name.strip()
        if new_name != item.name:
            item.name = new_name
            details_changed_fields.append("name")
            changed = True
    if body.description_md is not None and body.description_md != item.description_md:
        item.description_md = body.description_md
        details_changed_fields.append("description")
        changed = True

    if details_changed_fields:
        _record_event(
            session,
            item=item,
            event_type=InventoryEventType.ITEM_UPDATED,
            actor_user_id=current_user.id,
            note=", ".join(details_changed_fields),
        )

    if body.amount is not None and body.amount != item.amount:
        old_amount = item.amount
        item.amount = body.amount
        changed = True
        _record_event(
            session,
            item=item,
            event_type=InventoryEventType.ITEM_AMOUNT_CHANGED,
            actor_user_id=current_user.id,
            old_amount=old_amount,
            new_amount=item.amount,
        )

    if body.is_public is not None and body.is_public != item.is_public:
        old_public = item.is_public
        item.is_public = body.is_public
        changed = True
        _record_event(
            session,
            item=item,
            event_type=InventoryEventType.ITEM_VISIBILITY_CHANGED,
            actor_user_id=current_user.id,
            old_is_public=old_public,
            new_is_public=item.is_public,
        )

    if changed:
        item.updated_by_user_id = current_user.id
        item.updated_at = now
        session.add(item)
        session.commit()
        await event_manager.broadcast(party.id, "inventory_update", {"item_id": item.id})

    session.refresh(item)
    return _to_item_response(item, session=session, is_dm=is_dm, viewer_character_id=viewer_char_id)


@router.post("/{item_id}/transfer", response_model=InventoryItemResponse)
async def transfer_inventory_item(
    item_id: int,
    body: InventoryTransferRequest,
    party: Party = Depends(require_active_party),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
):
    """Transfer item ownership. Players can transfer their own items to active players."""
    viewer_char = _get_viewer_character(session, party.id, current_user.id)
    viewer_char_id = viewer_char.id if viewer_char else None
    is_dm = party.dm_id == current_user.id

    item = _get_item_or_404(session, party.id, item_id, include_archived=True)
    if not _can_edit_item(item, is_dm=is_dm, viewer_character_id=viewer_char_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to transfer this item")

    new_owner_id = body.owner_character_id
    if not is_dm and new_owner_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Players must transfer to an active player",
        )
    if new_owner_id is not None:
        _get_active_owner_or_400(session, party.id, new_owner_id)

    old_owner_id = item.owner_character_id
    if new_owner_id == old_owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item already belongs to that owner")

    item.owner_character_id = new_owner_id
    item.updated_by_user_id = current_user.id
    item.updated_at = _now()

    _record_event(
        session,
        item=item,
        event_type=InventoryEventType.ITEM_TRANSFERRED,
        actor_user_id=current_user.id,
        old_owner_character_id=old_owner_id,
        new_owner_character_id=new_owner_id,
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    await event_manager.broadcast(party.id, "inventory_update", {"item_id": item.id})

    return _to_item_response(item, session=session, is_dm=is_dm, viewer_character_id=viewer_char_id)


@router.post("/{item_id}/archive", response_model=InventoryItemResponse)
async def archive_inventory_item(
    item_id: int,
    party: Party = Depends(require_active_party),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
):
    """Soft-delete an item from active inventory."""
    viewer_char = _get_viewer_character(session, party.id, current_user.id)
    viewer_char_id = viewer_char.id if viewer_char else None
    is_dm = party.dm_id == current_user.id

    item = _get_item_or_404(session, party.id, item_id, include_archived=True)
    if not _can_edit_item(item, is_dm=is_dm, viewer_character_id=viewer_char_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to archive this item")
    if not item.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item is already archived")

    item.is_active = False
    item.updated_by_user_id = current_user.id
    item.updated_at = _now()

    _record_event(
        session,
        item=item,
        event_type=InventoryEventType.ITEM_DELETED,
        actor_user_id=current_user.id,
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    await event_manager.broadcast(party.id, "inventory_update", {"item_id": item.id})

    return _to_item_response(item, session=session, is_dm=is_dm, viewer_character_id=viewer_char_id)


@router.post("/{item_id}/restore", response_model=InventoryItemResponse)
async def restore_inventory_item(
    item_id: int,
    party: Party = Depends(require_active_party),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
):
    """Restore a previously archived item."""
    viewer_char = _get_viewer_character(session, party.id, current_user.id)
    viewer_char_id = viewer_char.id if viewer_char else None
    is_dm = party.dm_id == current_user.id

    item = _get_item_or_404(session, party.id, item_id, include_archived=True)
    if not _can_edit_item(item, is_dm=is_dm, viewer_character_id=viewer_char_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to restore this item")
    if item.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item is already active")

    _ensure_active_item_capacity(session, party.id)

    item.is_active = True
    item.updated_by_user_id = current_user.id
    item.updated_at = _now()

    _record_event(
        session,
        item=item,
        event_type=InventoryEventType.ITEM_RESTORED,
        actor_user_id=current_user.id,
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    await event_manager.broadcast(party.id, "inventory_update", {"item_id": item.id})

    return _to_item_response(item, session=session, is_dm=is_dm, viewer_character_id=viewer_char_id)
