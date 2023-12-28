from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.money import Money
from app.utils.auth import get_current_user_id
from app.utils.checks import *
from app.utils.currency import *
from app.utils.currency_convertions import convert_to_copper

router = APIRouter(
    prefix="/money/dm",
    tags=["money dm"]
)


# @router.put("/sum-characters", status_code=status.HTTP_200_OK)
# async def sum_money_to_many_characters(character_ids: CharacterIdLists,
#                                        amount: Money, db: Session = Depends(get_db),
#                                        current_user_id: UUID = Depends(get_current_user_id)):
#     check_current_user_role("DM", current_user_id, db)
#
#     for character_id in character_ids.ids:
#         check_character_id_exists(db, character_id)
#
#     copper_amount = convert_to_copper(amount)
#     money_for_each_character = divide_money_evenly(copper_amount, len(character_ids.ids))
#
#     for character_id, money in zip(character_ids.ids, money_for_each_character):
#         add_money(db, character_id, money)
#
#     return {"message": "Characters with ids: " + str(character_ids.ids) + " have received " + str(amount)}
#
#
# @router.put("/subtract-characters", status_code=status.HTTP_200_OK)
# async def subtract_money_to_many_characters(character_ids: CharacterIdLists,
#                                             amount: Money,
#                                             db: Session = Depends(get_db),
#                                             current_user_id: UUID = Depends(get_current_user_id)):
#     check_current_user_role("DM", current_user_id, db)
#
#     for character_id in character_ids.ids:
#         check_character_id_exists(db, character_id)
#
#     copper_amount = convert_to_copper(amount)
#     money_for_each_character = divide_money_evenly(copper_amount, len(character_ids.ids))
#
#     max_money_needed = max(money_for_each_character)
#     for character_id in character_ids.ids:
#         check_character_has_funds(db, character_id, max_money_needed)
#
#     for character_id, money in zip(character_ids.ids, money_for_each_character):
#         subtract_money(db, character_id, money)
#
#     return {"message": "Characters with ids: " + str(character_ids.ids) + " have lost " + str(amount)}


@router.put("/sum-party", status_code=status.HTTP_200_OK)
async def sum_money_to_all_characters_in_party(party_id: UUID,
                                               amount: Money,
                                               db: Session = Depends(get_db),
                                               current_user_id: UUID = Depends(get_current_user_id)):
    check_user_is_dm_of_party(current_user_id, party_id, db)
    characters_in_party = get_all_characters_in_party(db, party_id)

    copper_amount = convert_to_copper(amount)
    money_for_each_character = divide_money_evenly(copper_amount, len(characters_in_party))

    for character, money in zip(characters_in_party, money_for_each_character):
        character_wallet = get_wallet_with_character_id(db, character.id)
        character_wallet.money_copper += money

    db.commit()
    return {"message": "Characters in party with id: " + str(party_id) + " have received " + str(amount)}


@router.put("/subtract-party", status_code=status.HTTP_200_OK)
async def subtract_money_to_all_characters_in_party(party_id: UUID,
                                                    amount: Money,
                                                    db: Session = Depends(get_db),
                                                    current_user_id: UUID = Depends(get_current_user_id)):
    check_user_is_dm_of_party(current_user_id, party_id, db)
    characters_in_party = get_all_characters_in_party(db, party_id)

    copper_amount = convert_to_copper(amount)
    money_for_each_character = divide_money_evenly(copper_amount, len(characters_in_party))

    max_money_needed = max(money_for_each_character)
    for character in characters_in_party:
        check_character_has_funds(db, character.id, max_money_needed)

    for character, money in zip(characters_in_party, money_for_each_character):
        character_wallet = get_wallet_with_character_id(db, character.id)
        character_wallet.money_copper -= money

    db.commit()
    return {"message": "Characters in party with id: " + str(party_id) + " have lost " + str(amount)}
