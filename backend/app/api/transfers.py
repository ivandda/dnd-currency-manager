"""Transfer endpoints: P2P, distribution, DM controls, spend, and self-add."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.coin_preferences import CoinConfig, get_party_coin_config
from app.core.currency import coins_to_cp, cp_to_breakdown, split_amount
from app.core.database import get_session
from app.core.dependencies import (
    get_user_character_in_party,
    require_active_party,
    require_dm,
)
from app.core.events import event_manager
from app.models.character import Character
from app.models.party import Party
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.transaction import (
    DistributeRequest,
    DMLootRequest,
    DMGodModeRequest,
    SelfAddRequest,
    SpendRequest,
    TransactionResponse,
    TransferRequest,
)

router = APIRouter(prefix="/api/parties/{code}/transfers", tags=["transfers"])


def _transaction_to_response(
    txn: Transaction,
    coin_settings: CoinConfig,
    session: Session,
) -> TransactionResponse:
    """Convert a Transaction model to a response with display info."""
    breakdown = cp_to_breakdown(
        txn.amount_cp,
        use_platinum=coin_settings.use_platinum,
        use_gold=coin_settings.use_gold,
        use_electrum=coin_settings.use_electrum,
    )

    sender_name = None
    receiver_name = None
    if txn.sender_id:
        sender = session.get(Character, txn.sender_id)
        sender_name = sender.name if sender else None
    if txn.receiver_id:
        receiver = session.get(Character, txn.receiver_id)
        receiver_name = receiver.name if receiver else None

    return TransactionResponse(
        id=txn.id,
        transaction_type=txn.transaction_type,
        amount_cp=txn.amount_cp,
        amount_display=breakdown.to_display_dict(
            use_platinum=coin_settings.use_platinum,
            use_gold=coin_settings.use_gold,
            use_electrum=coin_settings.use_electrum,
        ),
        reason=txn.reason,
        timestamp=txn.timestamp,
        sender_id=txn.sender_id,
        sender_name=sender_name,
        receiver_id=txn.receiver_id,
        receiver_name=receiver_name,
    )


@router.post("/p2p", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def transfer_p2p(
    body: TransferRequest,
    party: Party = Depends(require_active_party),
    sender_char: Character = Depends(get_user_character_in_party),
    session: Session = Depends(get_session),
):
    """Character-to-character transfer."""
    viewer_coin_settings = get_party_coin_config(session, party, sender_char.user_id)

    try:
        amount_cp = coins_to_cp(**body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if amount_cp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount must be positive",
        )

    receiver = session.get(Character, body.receiver_id)
    if not receiver or receiver.party_id != party.id or not receiver.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver character not found in this party",
        )

    if receiver.id == sender_char.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to yourself",
        )

    if sender_char.balance_cp < amount_cp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )

    sender_char.balance_cp -= amount_cp
    receiver.balance_cp += amount_cp

    txn = Transaction(
        transaction_type=TransactionType.TRANSFER,
        amount_cp=amount_cp,
        reason=body.reason,
        party_id=party.id,
        sender_id=sender_char.id,
        receiver_id=receiver.id,
    )

    session.add(sender_char)
    session.add(receiver)
    session.add(txn)
    session.commit()
    session.refresh(txn)

    await event_manager.broadcast(party.id, "transaction_new", {"transaction_id": txn.id})
    await event_manager.broadcast(
        party.id,
        "balance_update",
        {"character_id": sender_char.id, "balance_cp": sender_char.balance_cp},
    )
    await event_manager.broadcast(
        party.id,
        "balance_update",
        {"character_id": receiver.id, "balance_cp": receiver.balance_cp},
    )

    return _transaction_to_response(txn, viewer_coin_settings, session)


@router.post("/distribute", response_model=list[TransactionResponse], status_code=status.HTTP_201_CREATED)
async def transfer_distribute(
    body: DistributeRequest,
    party: Party = Depends(require_active_party),
    sender_char: Character = Depends(get_user_character_in_party),
    session: Session = Depends(get_session),
):
    """Character distributes money among selected characters and/or NPC."""
    viewer_coin_settings = get_party_coin_config(session, party, sender_char.user_id)

    try:
        total_amount_cp = coins_to_cp(**body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if total_amount_cp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Distribution amount must be positive",
        )

    if sender_char.balance_cp < total_amount_cp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )

    unique_character_ids = list(dict.fromkeys(body.character_ids))
    recipients_count = len(unique_character_ids) + (1 if body.include_npc else 0)
    if recipients_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must select at least one recipient (character or NPC)",
        )

    receiver_chars: list[Character] = []
    for char_id in unique_character_ids:
        if char_id == sender_char.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot distribute to yourself",
            )
        receiver = session.get(Character, char_id)
        if not receiver or receiver.party_id != party.id or not receiver.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {char_id} not found in this party",
            )
        receiver_chars.append(receiver)

    shares = split_amount(total_amount_cp, recipients_count)
    character_shares = shares[: len(receiver_chars)]
    npc_share_cp = shares[-1] if body.include_npc else 0

    sender_char.balance_cp -= total_amount_cp
    session.add(sender_char)

    transactions: list[tuple[Transaction, int | None]] = []

    for receiver, share_cp in zip(receiver_chars, character_shares):
        if share_cp <= 0:
            continue
        receiver.balance_cp += share_cp
        txn = Transaction(
            transaction_type=TransactionType.TRANSFER,
            amount_cp=share_cp,
            reason=body.reason,
            party_id=party.id,
            sender_id=sender_char.id,
            receiver_id=receiver.id,
        )
        session.add(receiver)
        session.add(txn)
        transactions.append((txn, receiver.id))

    if npc_share_cp > 0:
        txn = Transaction(
            transaction_type=TransactionType.SPEND,
            amount_cp=npc_share_cp,
            reason=body.reason,
            party_id=party.id,
            sender_id=sender_char.id,
            receiver_id=None,
        )
        session.add(txn)
        transactions.append((txn, None))

    session.commit()

    results: list[TransactionResponse] = []
    for txn, char_id in transactions:
        session.refresh(txn)
        results.append(_transaction_to_response(txn, viewer_coin_settings, session))
        await event_manager.broadcast(party.id, "transaction_new", {"transaction_id": txn.id})
        if char_id is not None:
            char = session.get(Character, char_id)
            await event_manager.broadcast(
                party.id,
                "balance_update",
                {"character_id": char_id, "balance_cp": char.balance_cp},
            )

    await event_manager.broadcast(
        party.id,
        "balance_update",
        {"character_id": sender_char.id, "balance_cp": sender_char.balance_cp},
    )

    return results


@router.post("/loot", response_model=list[TransactionResponse], status_code=status.HTTP_201_CREATED)
async def dm_loot(
    body: DMLootRequest,
    party: Party = Depends(require_active_party),
    dm_user: User = Depends(require_dm),
    session: Session = Depends(get_session),
):
    """DM grants or deducts money evenly among characters from an infinite source."""
    viewer_coin_settings = get_party_coin_config(session, party, dm_user.id)

    try:
        total_amount_cp = coins_to_cp(**body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if total_amount_cp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive",
        )

    unique_character_ids = list(dict.fromkeys(body.character_ids))
    if not unique_character_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must select at least one character",
        )

    split_amount_cp = total_amount_cp // len(unique_character_ids)
    if split_amount_cp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount is too small to split among the selected characters.",
        )

    characters_to_update: list[Character] = []
    for char_id in unique_character_ids:
        character = session.get(Character, char_id)
        if not character or character.party_id != party.id or not character.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {char_id} not found in this party",
            )

        if body.is_deduction and character.balance_cp < split_amount_cp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Character {character.name} does not have enough funds for this deduction. "
                    f"They need {split_amount_cp} CP but have {character.balance_cp} CP."
                ),
            )
        characters_to_update.append(character)

    transactions: list[tuple[Transaction, Character]] = []
    for character in characters_to_update:
        if body.is_deduction:
            character.balance_cp -= split_amount_cp
            txn_type = TransactionType.DM_DEDUCT
        else:
            character.balance_cp += split_amount_cp
            txn_type = TransactionType.DM_GRANT

        txn = Transaction(
            transaction_type=txn_type,
            amount_cp=split_amount_cp,
            reason=body.reason,
            party_id=party.id,
            sender_id=None,
            receiver_id=character.id,
        )
        session.add(character)
        session.add(txn)
        transactions.append((txn, character))

    session.commit()

    results: list[TransactionResponse] = []
    for txn, character in transactions:
        session.refresh(txn)
        results.append(_transaction_to_response(txn, viewer_coin_settings, session))
        await event_manager.broadcast(
            party.id,
            "balance_update",
            {"character_id": character.id, "balance_cp": character.balance_cp},
        )
        await event_manager.broadcast(party.id, "transaction_new", {"transaction_id": txn.id})

    return results


@router.post("/god-mode", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def dm_god_mode(
    body: DMGodModeRequest,
    party: Party = Depends(require_active_party),
    dm_user: User = Depends(require_dm),
    session: Session = Depends(get_session),
):
    """DM directly adds or subtracts money from a character's wallet."""
    viewer_coin_settings = get_party_coin_config(session, party, dm_user.id)

    try:
        amount_cp = coins_to_cp(**body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if amount_cp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive",
        )

    character = session.get(Character, body.character_id)
    if not character or character.party_id != party.id or not character.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found in this party",
        )

    if body.is_deduction:
        if character.balance_cp < amount_cp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deduct more than the character's balance",
            )
        character.balance_cp -= amount_cp
        txn_type = TransactionType.DM_DEDUCT
    else:
        character.balance_cp += amount_cp
        txn_type = TransactionType.DM_GRANT

    txn = Transaction(
        transaction_type=txn_type,
        amount_cp=amount_cp,
        reason=body.reason,
        party_id=party.id,
        sender_id=None,
        receiver_id=character.id,
    )

    session.add(character)
    session.add(txn)
    session.commit()
    session.refresh(txn)

    await event_manager.broadcast(
        party.id,
        "balance_update",
        {"character_id": character.id, "balance_cp": character.balance_cp},
    )
    await event_manager.broadcast(party.id, "transaction_new", {"transaction_id": txn.id})

    return _transaction_to_response(txn, viewer_coin_settings, session)


@router.post("/spend", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def spend_npc(
    body: SpendRequest,
    party: Party = Depends(require_active_party),
    spender: Character = Depends(get_user_character_in_party),
    session: Session = Depends(get_session),
):
    """Player spends money (NPC purchase, shop, toll, etc.)."""
    viewer_coin_settings = get_party_coin_config(session, party, spender.user_id)

    try:
        amount_cp = coins_to_cp(**body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if amount_cp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Spend amount must be positive",
        )

    if spender.balance_cp < amount_cp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )

    spender.balance_cp -= amount_cp

    txn = Transaction(
        transaction_type=TransactionType.SPEND,
        amount_cp=amount_cp,
        reason=body.reason,
        party_id=party.id,
        sender_id=spender.id,
        receiver_id=None,
    )

    session.add(spender)
    session.add(txn)
    session.commit()
    session.refresh(txn)

    await event_manager.broadcast(
        party.id,
        "balance_update",
        {"character_id": spender.id, "balance_cp": spender.balance_cp},
    )
    await event_manager.broadcast(party.id, "transaction_new", {"transaction_id": txn.id})

    return _transaction_to_response(txn, viewer_coin_settings, session)


@router.post("/self-add", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def self_add(
    body: SelfAddRequest,
    party: Party = Depends(require_active_party),
    character: Character = Depends(get_user_character_in_party),
    session: Session = Depends(get_session),
):
    """Player adds money to their own wallet (found loot, sold items, etc.)."""
    viewer_coin_settings = get_party_coin_config(session, party, character.user_id)

    try:
        amount_cp = coins_to_cp(**body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if amount_cp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive",
        )

    character.balance_cp += amount_cp

    txn = Transaction(
        transaction_type=TransactionType.SELF_ADD,
        amount_cp=amount_cp,
        reason=body.reason,
        party_id=party.id,
        sender_id=None,
        receiver_id=character.id,
    )

    session.add(character)
    session.add(txn)
    session.commit()
    session.refresh(txn)

    await event_manager.broadcast(
        party.id,
        "balance_update",
        {"character_id": character.id, "balance_cp": character.balance_cp},
    )
    await event_manager.broadcast(party.id, "transaction_new", {"transaction_id": txn.id})

    return _transaction_to_response(txn, viewer_coin_settings, session)
