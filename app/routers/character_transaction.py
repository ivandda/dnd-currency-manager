from fastapi import Depends, APIRouter, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.characters import CharacterIdLists
from app.schemas.money import Money
from app.utils.checks import *
from app.utils.currency import *
from app.utils.currency_convertions import convert_to_copper, convert_to_type

router = APIRouter(
    prefix="/character-transaction",
    tags=["character transactions"]
)


@router.get("/{id}/funds", response_model=Money)
async def check_funds(id: int, db: Session = Depends(get_db)):
    await check_character_id_exists(db, id)

    copper = get_money_in_character_wallet(db, id)
    money_simplified = convert_to_simplified(copper)
    return Money(**money_simplified)


@router.get("/{id}/funds-by-currency-type", response_model=Money)
async def get_funds_simplified_to_currency_type(id: int, currency_type: str = Query(...),
                                                db: Session = Depends(get_db)):
    await check_character_id_exists(db, id)
    check_currency_type(currency_type)
    money_in_copper = get_money_in_character_wallet(db, id)
    money_simplified_to_curr_type = convert_to_type(money_in_copper, currency_type)
    return Money(**money_simplified_to_curr_type)


@router.put("/sum-characters", status_code=status.HTTP_200_OK)
async def sum_money_to_many_characters(character_ids: CharacterIdLists, amount: Money, db: Session = Depends(get_db)):
    for character_id in character_ids.ids:
        await check_character_id_exists(db, character_id)

    copper_amount = convert_to_copper(amount)
    money_for_each_character = divide_money_evenly(copper_amount, len(character_ids.ids))

    for character_id, money in zip(character_ids.ids, money_for_each_character):
        add_money(db, character_id, money)

    return {"message": "Characters with ids: " + str(character_ids.ids) + " have received " + str(amount)}


@router.put("/subtract-characters", status_code=status.HTTP_200_OK)
async def subtract_money_to_many_characters(character_ids: CharacterIdLists, amount: Money,
                                            db: Session = Depends(get_db)):
    for character_id in character_ids.ids:
        await check_character_id_exists(db, character_id)

    copper_amount = convert_to_copper(amount)
    money_for_each_character = divide_money_evenly(copper_amount, len(character_ids.ids))

    max_money_needed = max(money_for_each_character)
    for character_id in character_ids.ids:
        check_character_has_funds(db, character_id, max_money_needed)

    for character_id, money in zip(character_ids.ids, money_for_each_character):
        subtract_money(db, character_id, money)

    return {"message": "Characters with ids: " + str(character_ids.ids) + " have lost " + str(amount)}


@router.put("/transfer/{remitter_id}/{beneficiary_id}", status_code=status.HTTP_200_OK)
async def transfer_money(remitter_id: int, amount: Money, beneficiary_id: int, db: Session = Depends(get_db)):
    await check_character_id_exists(db, remitter_id)
    await check_character_id_exists(db, beneficiary_id)

    copper_amount = convert_to_copper(amount)
    check_character_has_funds(db, remitter_id, copper_amount)
    subtract_money(db, remitter_id, copper_amount)
    add_money(db, beneficiary_id, copper_amount)
    return {"message": "Transfer completed"}
