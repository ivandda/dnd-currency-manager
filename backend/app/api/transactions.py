"""Transaction history endpoint with pagination."""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func

from app.core.coin_preferences import CoinConfig, get_party_coin_config
from app.core.currency import cp_to_breakdown
from app.core.database import get_session
from app.core.dependencies import get_party_by_code, require_party_member_or_dm
from app.models.character import Character
from app.models.party import Party
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionListResponse, TransactionResponse

router = APIRouter(prefix="/api/parties/{code}/transactions", tags=["transactions"])


def _transaction_to_response(
    txn: Transaction,
    coin_settings: CoinConfig,
    session: Session,
) -> TransactionResponse:
    """Convert a Transaction model to a display response."""
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


@router.get("", response_model=TransactionListResponse)
def get_transaction_history(
    party: Party = Depends(get_party_by_code),
    current_user: User = Depends(require_party_member_or_dm),
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Get paginated transaction history for a party."""
    viewer_coin_settings = get_party_coin_config(session, party, current_user.id)

    # Count total
    total = session.exec(
        select(func.count(Transaction.id)).where(
            Transaction.party_id == party.id
        )
    ).one()

    # Fetch page (newest first)
    offset = (page - 1) * page_size
    transactions = session.exec(
        select(Transaction)
        .where(Transaction.party_id == party.id)
        .order_by(Transaction.timestamp.desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    return TransactionListResponse(
        transactions=[
            _transaction_to_response(txn, viewer_coin_settings, session)
            for txn in transactions
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
