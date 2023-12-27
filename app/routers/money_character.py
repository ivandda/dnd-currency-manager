from fastapi import Depends, APIRouter, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.money import Money
from app.utils.auth import get_current_user_id
from app.utils.checks import *
from app.utils.currency import *
from app.utils.currency_convertions import convert_to_type, convert_to_copper
from app.utils.getters import get_wallet_with_user_id_and_character_id

router = APIRouter(
    prefix="/money/characters",
    tags=["money characters"]
)


@router.get("/{id}/funds", response_model=Money)
async def check_funds(id: UUID, db: Session = Depends(get_db),
                      user_id: UUID = Depends(get_current_user_id)):
    character_wallet = get_wallet_with_user_id_and_character_id(db, user_id, id)
    if character_wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    copper = character_wallet.money_copper
    money_simplified = convert_to_simplified(copper)
    return Money(**money_simplified)


@router.get("/{id}/funds-by-currency-type", response_model=Money)
async def get_funds_simplified_to_currency_type(id: UUID, currency_type: str = Query(...),
                                                db: Session = Depends(get_db),
                                                user_id: UUID = Depends(get_current_user_id)):
    check_currency_type(currency_type)
    character_wallet = get_wallet_with_user_id_and_character_id(db, user_id, id)
    if character_wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    money_in_copper = character_wallet.money_copper
    money_simplified_to_curr_type = convert_to_type(money_in_copper, currency_type)
    return Money(**money_simplified_to_curr_type)


@router.put("/transfer/{remitter_id}/{beneficiary_id}", status_code=status.HTTP_200_OK)
async def transfer_money(remitter_id: UUID, amount: Money, beneficiary_id: UUID,
                         db: Session = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    remitter_wallet = get_wallet_with_user_id_and_character_id(db, user_id, remitter_id)
    beneficiary_wallet = get_wallet_with_character_id(db, beneficiary_id)

    if remitter_wallet is None or beneficiary_wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    copper_amount = convert_to_copper(amount)

    if remitter_wallet.money_copper < copper_amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Character does not have enough funds")

    remitter_wallet.money_copper -= copper_amount
    beneficiary_wallet.money_copper += copper_amount
    db.commit()
    return {"message": "Transfer completed"}


@router.put("/sum", status_code=status.HTTP_200_OK)
async def sum_money(character_id: UUID, amount: Money,
                    db: Session = Depends(get_db),
                    user_id=Depends(get_current_user_id)):
    character_wallet = get_wallet_with_user_id_and_character_id(db, user_id, character_id)
    if character_wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    copper_amount = convert_to_copper(amount)

    character_wallet.money_copper += copper_amount
    db.commit()
    return {"message": "Sum completed"}


@router.put("/subtract", status_code=status.HTTP_200_OK)
async def subtract_money(character_id: UUID, amount: Money,
                         db: Session = Depends(get_db),
                         user_id=Depends(get_current_user_id)):
    character_wallet = get_wallet_with_user_id_and_character_id(db, user_id, character_id)
    if character_wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    copper_amount = convert_to_copper(amount)

    if character_wallet.money_copper < copper_amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Character does not have enough funds")

    character_wallet.money_copper -= copper_amount
    db.commit()
    return {"message": "Subtract completed"}
