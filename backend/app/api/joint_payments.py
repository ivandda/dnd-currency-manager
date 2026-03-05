"""Joint payment endpoints: create, accept, reject, cancel, list."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.currency import coins_to_cp, cp_to_breakdown, split_amount
from app.core.database import get_session
from app.core.dependencies import (
    get_current_user,
    get_party_by_code,
    get_user_character_in_party,
    require_active_party,
    require_dm,
)
from app.core.events import event_manager
from app.models.character import Character
from app.models.party import Party
from app.models.transaction import Transaction, TransactionType
from app.models.joint_payment import (
    JointPayment,
    JointPaymentStatus,
    PaymentParticipant,
)
from app.models.user import User
from app.schemas.joint_payment import (
    JointPaymentCreate,
    JointPaymentResponse,
    ParticipantResponse,
)
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/api/parties/{code}/joint-payments", tags=["joint-payments"])


def _payment_to_response(
    payment: JointPayment, party: Party, session: Session
) -> JointPaymentResponse:
    """Convert a JointPayment model to a display response."""
    breakdown = cp_to_breakdown(
        payment.total_amount_cp,
        use_platinum=party.use_platinum,
        use_gold=party.use_gold,
        use_electrum=party.use_electrum,
    )

    creator_name = None
    if payment.creator_character_id:
        creator = session.get(Character, payment.creator_character_id)
        creator_name = creator.name if creator else None
    elif payment.creator_is_dm:
        dm = session.get(User, party.dm_id)
        creator_name = f"DM ({dm.username})" if dm else "DM"

    # Get participants
    participants = session.exec(
        select(PaymentParticipant).where(
            PaymentParticipant.joint_payment_id == payment.id
        )
    ).all()

    participant_responses = []
    for p in participants:
        char = session.get(Character, p.character_id)
        share_breakdown = cp_to_breakdown(
            p.share_cp,
            use_platinum=party.use_platinum,
            use_gold=party.use_gold,
            use_electrum=party.use_electrum,
        )
        participant_responses.append(
            ParticipantResponse(
                character_id=p.character_id,
                character_name=char.name if char else "Unknown",
                share_cp=p.share_cp,
                share_display=share_breakdown.to_display_dict(
                    use_platinum=party.use_platinum,
                    use_gold=party.use_gold,
                    use_electrum=party.use_electrum,
                ),
                has_accepted=p.has_accepted,
            )
        )

    return JointPaymentResponse(
        id=payment.id,
        creator_character_id=payment.creator_character_id,
        creator_name=creator_name,
        creator_is_dm=payment.creator_is_dm,
        total_amount_cp=payment.total_amount_cp,
        total_amount_display=breakdown.to_display_dict(
            use_platinum=party.use_platinum,
            use_gold=party.use_gold,
            use_electrum=party.use_electrum,
        ),
        reason=payment.reason,
        status=payment.status,
        created_at=payment.created_at,
        participants=participant_responses,
    )


@router.post("", response_model=JointPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_joint_payment_as_player(
    body: JointPaymentCreate,
    party: Party = Depends(require_active_party),
    creator_char: Character = Depends(get_user_character_in_party),
    session: Session = Depends(get_session),
):
    """Player creates a joint payment request split among selected characters."""
    try:
        total_cp = coins_to_cp(**body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if total_cp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be positive",
        )

    # Validate all participants exist in the party
    participant_chars = []
    for char_id in body.character_ids:
        char = session.get(Character, char_id)
        if not char or char.party_id != party.id or not char.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {char_id} not found in this party",
            )
        participant_chars.append(char)

    # Calculate shares
    shares = split_amount(total_cp, len(participant_chars))

    # Check all participants have sufficient funds
    for char, share in zip(participant_chars, shares):
        if char.balance_cp < share:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{char.name} has insufficient funds ({char.balance_cp} CP < {share} CP)",
            )

    # Create joint payment
    payment = JointPayment(
        creator_character_id=creator_char.id,
        creator_is_dm=False,
        party_id=party.id,
        total_amount_cp=total_cp,
        reason=body.reason,
        status=JointPaymentStatus.PENDING,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)

    # Create participant records
    for char, share in zip(participant_chars, shares):
        participant = PaymentParticipant(
            joint_payment_id=payment.id,
            character_id=char.id,
            share_cp=share,
            has_accepted=False,
        )
        session.add(participant)
    session.commit()

    await event_manager.broadcast(
        party.id, "joint_payment_update", {"payment_id": payment.id, "status": "pending"}
    )

    return _payment_to_response(payment, party, session)


@router.post("/dm", response_model=JointPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_joint_payment_as_dm(
    body: JointPaymentCreate,
    party: Party = Depends(require_active_party),
    dm_user: User = Depends(require_dm),
    session: Session = Depends(get_session),
):
    """DM creates a charge split among selected characters."""
    try:
        total_cp = coins_to_cp(**body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if total_cp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be positive",
        )

    participant_chars = []
    for char_id in body.character_ids:
        char = session.get(Character, char_id)
        if not char or char.party_id != party.id or not char.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {char_id} not found in this party",
            )
        participant_chars.append(char)

    shares = split_amount(total_cp, len(participant_chars))

    for char, share in zip(participant_chars, shares):
        if char.balance_cp < share:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{char.name} has insufficient funds ({char.balance_cp} CP < {share} CP)",
            )

    payment = JointPayment(
        creator_character_id=None,
        creator_is_dm=True,
        party_id=party.id,
        total_amount_cp=total_cp,
        reason=body.reason,
        status=JointPaymentStatus.PENDING,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)

    for char, share in zip(participant_chars, shares):
        participant = PaymentParticipant(
            joint_payment_id=payment.id,
            character_id=char.id,
            share_cp=share,
            has_accepted=False,
        )
        session.add(participant)
    session.commit()

    await event_manager.broadcast(
        party.id, "joint_payment_update", {"payment_id": payment.id, "status": "pending"}
    )

    return _payment_to_response(payment, party, session)


@router.get("", response_model=list[JointPaymentResponse])
def list_joint_payments(
    party: Party = Depends(get_party_by_code),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List all joint payments for a party (most recent first)."""
    payments = session.exec(
        select(JointPayment)
        .where(JointPayment.party_id == party.id)
        .order_by(JointPayment.created_at.desc())
    ).all()

    return [_payment_to_response(p, party, session) for p in payments]


@router.post("/{payment_id}/accept", response_model=JointPaymentResponse)
async def accept_joint_payment(
    payment_id: int,
    party: Party = Depends(require_active_party),
    character: Character = Depends(get_user_character_in_party),
    session: Session = Depends(get_session),
):
    """Accept a joint payment request."""
    payment = session.get(JointPayment, payment_id)
    if not payment or payment.party_id != party.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Joint payment not found",
        )

    if payment.status != JointPaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment is already {payment.status.value}",
        )

    # Find this character's participation record
    participant = session.exec(
        select(PaymentParticipant).where(
            PaymentParticipant.joint_payment_id == payment.id,
            PaymentParticipant.character_id == character.id,
        )
    ).first()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this payment",
        )

    if participant.has_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already accepted",
        )

    # Re-check funds before accepting
    if character.balance_cp < participant.share_cp:
        payment.status = JointPaymentStatus.REJECTED
        session.add(payment)
        session.commit()
        await event_manager.broadcast(
            party.id, "joint_payment_update",
            {"payment_id": payment.id, "status": "rejected", "reason": "insufficient_funds"}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds — payment has been blocked",
        )

    participant.has_accepted = True
    session.add(participant)

    # Check if all participants have accepted
    all_participants = session.exec(
        select(PaymentParticipant).where(
            PaymentParticipant.joint_payment_id == payment.id
        )
    ).all()

    all_accepted = all(p.has_accepted for p in all_participants)

    if all_accepted:
        # Execute the payment: deduct from all participants
        for p in all_participants:
            char = session.get(Character, p.character_id)
            if char.balance_cp < p.share_cp:
                # Edge case: balance changed between accept and execution
                payment.status = JointPaymentStatus.REJECTED
                session.add(payment)
                session.commit()
                await event_manager.broadcast(
                    party.id, "joint_payment_update",
                    {"payment_id": payment.id, "status": "rejected"}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{char.name} no longer has sufficient funds",
                )

            char.balance_cp -= p.share_cp
            session.add(char)

            # Create transaction record for each participant
            txn = Transaction(
                transaction_type=TransactionType.JOINT_PAYMENT,
                amount_cp=p.share_cp,
                reason=payment.reason,
                party_id=party.id,
                sender_id=char.id,
                receiver_id=None,  # Money goes to NPC / disappears
                joint_payment_id=payment.id,
            )
            session.add(txn)

        payment.status = JointPaymentStatus.APPROVED
        session.add(payment)
        session.commit()

        # Broadcast balance updates for all participants
        for p in all_participants:
            char = session.get(Character, p.character_id)
            await event_manager.broadcast(party.id, "balance_update", {
                "character_id": char.id, "balance_cp": char.balance_cp
            })
        await event_manager.broadcast(
            party.id, "joint_payment_update",
            {"payment_id": payment.id, "status": "approved"}
        )
    else:
        session.commit()
        await event_manager.broadcast(
            party.id, "joint_payment_update",
            {"payment_id": payment.id, "status": "pending"}
        )

    return _payment_to_response(payment, party, session)


@router.post("/{payment_id}/reject", response_model=JointPaymentResponse)
async def reject_joint_payment(
    payment_id: int,
    party: Party = Depends(require_active_party),
    character: Character = Depends(get_user_character_in_party),
    session: Session = Depends(get_session),
):
    """Reject a joint payment request. Immediately sets status to rejected."""
    payment = session.get(JointPayment, payment_id)
    if not payment or payment.party_id != party.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Joint payment not found",
        )

    if payment.status != JointPaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment is already {payment.status.value}",
        )

    # Verify participant
    participant = session.exec(
        select(PaymentParticipant).where(
            PaymentParticipant.joint_payment_id == payment.id,
            PaymentParticipant.character_id == character.id,
        )
    ).first()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this payment",
        )

    payment.status = JointPaymentStatus.REJECTED
    session.add(payment)
    session.commit()

    await event_manager.broadcast(
        party.id, "joint_payment_update",
        {"payment_id": payment.id, "status": "rejected"}
    )

    return _payment_to_response(payment, party, session)


@router.post("/{payment_id}/cancel", response_model=JointPaymentResponse)
async def cancel_joint_payment(
    payment_id: int,
    party: Party = Depends(require_active_party),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Cancel a pending joint payment. Only the creator can cancel."""
    payment = session.get(JointPayment, payment_id)
    if not payment or payment.party_id != party.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Joint payment not found",
        )

    if payment.status != JointPaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment is already {payment.status.value}",
        )

    # Verify creator
    is_creator = False
    if payment.creator_is_dm and party.dm_id == current_user.id:
        is_creator = True
    elif payment.creator_character_id:
        creator_char = session.get(Character, payment.creator_character_id)
        if creator_char and creator_char.user_id == current_user.id:
            is_creator = True

    if not is_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can cancel this payment",
        )

    payment.status = JointPaymentStatus.CANCELLED
    session.add(payment)
    session.commit()

    await event_manager.broadcast(
        party.id, "joint_payment_update",
        {"payment_id": payment.id, "status": "cancelled"}
    )

    return _payment_to_response(payment, party, session)
