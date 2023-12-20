from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.characters import CharacterIdLists
from app.schemas.money import Money
from app.utils.auth import get_current_user_id
from app.utils.checks import *
from app.utils.currency import *
from app.utils.currency_convertions import convert_to_copper

router = APIRouter(
    prefix="/money/dm",
    tags=["money dm"]
)


@router.put("/sum-characters", status_code=status.HTTP_200_OK)
async def sum_money_to_many_characters(character_ids: CharacterIdLists,
                                       amount: Money, db: Session = Depends(get_db),
                                       current_user_id: int = Depends(get_current_user_id)):

    check_current_user_role("DM", current_user_id, db)

    for character_id in character_ids.ids:
        check_character_id_exists(db, character_id)

    copper_amount = convert_to_copper(amount)
    money_for_each_character = divide_money_evenly(copper_amount, len(character_ids.ids))

    for character_id, money in zip(character_ids.ids, money_for_each_character):
        add_money(db, character_id, money)

    return {"message": "Characters with ids: " + str(character_ids.ids) + " have received " + str(amount)}


@router.put("/subtract-characters", status_code=status.HTTP_200_OK)
async def subtract_money_to_many_characters(character_ids: CharacterIdLists,
                                            amount: Money,
                                            db: Session = Depends(get_db),
                                            current_user_id: int = Depends(get_current_user_id)):
    check_current_user_role("DM", current_user_id, db)

    for character_id in character_ids.ids:
        check_character_id_exists(db, character_id)

    copper_amount = convert_to_copper(amount)
    money_for_each_character = divide_money_evenly(copper_amount, len(character_ids.ids))

    max_money_needed = max(money_for_each_character)
    for character_id in character_ids.ids:
        check_character_has_funds(db, character_id, max_money_needed)

    for character_id, money in zip(character_ids.ids, money_for_each_character):
        subtract_money(db, character_id, money)

    return {"message": "Characters with ids: " + str(character_ids.ids) + " have lost " + str(amount)}
