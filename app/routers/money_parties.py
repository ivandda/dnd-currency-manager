from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.money import Money
from app.utils.checks import *
from app.utils.currency import *
from app.utils.currency_convertions import convert_to_copper

router = APIRouter(
    prefix="/money/parties",
    tags=["money parties"]
)


@router.put("/character_transfers_party/{character_id}/{party_id}", status_code=status.HTTP_200_OK)
async def character_transfers_to_party(character_id: UUID, party_id: UUID, amount: Money,
                                       db: Session = Depends(get_db)):
    check_character_id_exists(db, character_id)
    check_party_id_exists(db, party_id)
    check_party_has_characters(db, party_id)

    copper_amount = convert_to_copper(amount)
    check_character_has_funds(db, character_id, copper_amount)

    subtract_money(db, character_id, copper_amount)
    add_money_to_characters_in_party(db, copper_amount, party_id)

    return {"message": "Transactions successful"}


@router.put("/party_transfers_character/{party_id}/{character_id}", status_code=status.HTTP_200_OK)
async def party_transfers_to_character(party_id: UUID, character_id: UUID, amount: Money,
                                       db: Session = Depends(get_db)):
    check_character_id_exists(db, character_id)
    check_party_id_exists(db, party_id)
    check_party_has_characters(db, party_id)

    copper_amount = convert_to_copper(amount)
    characters = get_all_characters_in_party(db, party_id)
    check_funds_for_characters(db, copper_amount, characters)

    subtract_money_from_characters_in_party(db, copper_amount, party_id)
    add_money(db, character_id, copper_amount)

    return {"message": "Transactions successful"}


@router.put("/party_transfers_party/{party_id_from}/{party_id_to}", status_code=status.HTTP_200_OK)
async def party_transfers_to_party(party_id_from: UUID, party_id_to: UUID, amount: Money,
                                   db: Session = Depends(get_db)):
    check_party_id_exists(db, party_id_from)
    check_party_id_exists(db, party_id_to)
    check_party_has_characters(db, party_id_from)

    copper_amount = convert_to_copper(amount)
    characters = get_all_characters_in_party(db, party_id_from)
    check_funds_for_characters(db, copper_amount, characters)

    subtract_money_from_characters_in_party(db, copper_amount, party_id_from)
    add_money_to_characters_in_party(db, copper_amount, party_id_to)

    return {"message": "Transactions successful"}
