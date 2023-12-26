from fastapi import Depends, APIRouter, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.money import Money
from app.utils.auth import get_current_user_id
from app.utils.checks import *
from app.utils.currency import *
from app.utils.currency_convertions import convert_to_type, convert_to_copper
from app.utils.getters import get_user_id_by_character_id

router = APIRouter(
    prefix="/money/characters",
    tags=["money characters"]
)


@router.get("/{id}/funds", response_model=Money)
async def check_funds(id: UUID, db: Session = Depends(get_db),
                      user_id: UUID = Depends(get_current_user_id)):
    check_character_id_exists(db, id)
    check_user_id_is_authenticated(user_id, get_user_id_by_character_id(db, id))

    copper = get_money_in_character_wallet(db, id)
    money_simplified = convert_to_simplified(copper)
    return Money(**money_simplified)


@router.get("/{id}/funds-by-currency-type", response_model=Money)
async def get_funds_simplified_to_currency_type(id: UUID, currency_type: str = Query(...),
                                                db: Session = Depends(get_db),
                                                user_id: UUID = Depends(get_current_user_id)):
    check_character_id_exists(db, id)
    check_user_id_is_authenticated(user_id, get_user_id_by_character_id(db, id))
    check_currency_type(currency_type)
    money_in_copper = get_money_in_character_wallet(db, id)
    money_simplified_to_curr_type = convert_to_type(money_in_copper, currency_type)
    return Money(**money_simplified_to_curr_type)


@router.put("/transfer/{remitter_id}/{beneficiary_id}", status_code=status.HTTP_200_OK)
async def transfer_money(remitter_id: UUID, amount: Money, beneficiary_id: UUID,
                         db: Session = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    check_character_id_exists(db, remitter_id)
    check_character_id_exists(db, beneficiary_id)
    check_user_id_is_authenticated(user_id, get_user_id_by_character_id(db, remitter_id))

    copper_amount = convert_to_copper(amount)
    check_character_has_funds(db, remitter_id, copper_amount)
    subtract_money(db, remitter_id, copper_amount)
    add_money(db, beneficiary_id, copper_amount)
    return {"message": "Transfer completed"}
