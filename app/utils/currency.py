from uuid import UUID

from fastapi import HTTPException, status

from app.utils.currency_convertions import convert_to_simplified
from app.utils.getters import get_wallet_with_character_id, get_money_in_character_wallet, get_character_name, \
    get_all_characters_in_party


# services


def add_money(db, id: UUID, amount: int):
    wallet = get_wallet_with_character_id(db, id)
    wallet.money_copper += amount
    db.commit()
    db.refresh(wallet)
    return wallet


def subtract_money(db, id, amount):
    if check_character_has_funds(db, id, amount):
        wallet = get_wallet_with_character_id(db, id)
        wallet.money_copper -= amount
        db.commit()
        db.refresh(wallet)
        return wallet


# NOT TESTED:
def divide_money_evenly(total_money, num_people):
    if num_people <= 0:
        raise ValueError("Number of people must be greater than 0")
    amount_per_person = total_money // num_people

    residue = total_money % num_people

    amounts = [amount_per_person] * num_people

    for i in range(residue):
        amounts[i] += 1

    return amounts


def add_money_to_characters(db, total_money: int, characters: list):
    money_divided_list = divide_money_evenly(total_money, len(characters))

    for money, character in zip(money_divided_list, characters):
        add_money(db, character.id, money)


def add_money_to_characters_in_party(db, total_money: int, party_id: UUID):
    characters = get_all_characters_in_party(db, party_id)
    add_money_to_characters(db, total_money, characters)


def subtract_money_from_characters(db, total_money: int, characters: list):
    money_divided_list = divide_money_evenly(total_money, len(characters))

    for money, character in zip(money_divided_list, characters):
        subtract_money(db, character.id, money)


def subtract_money_from_characters_in_party(db, total_money: int, party_id: UUID):
    characters = get_all_characters_in_party(db, party_id)
    subtract_money_from_characters(db, total_money, characters)


def check_character_has_funds(db, character_id: UUID, amount: int) -> bool:
    character_money = get_money_in_character_wallet(db, character_id)

    if character_money < amount:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Character "
                                   + get_character_name(db, character_id)
                                   + " (with id " + str(character_id)
                                   + ") does not have"
                                   + str(convert_to_simplified(amount)) + " to spend")

    else:
        return True


def check_funds_for_characters(db, total_money: int, characters: list):
    money_by_character = divide_money_evenly(total_money, len(characters))

    for money, character in zip(money_by_character, characters):
        if not check_character_has_funds(db, character.id, money):
            return HTTPException(status_code=status.HTTP_409_CONFLICT,
                                 detail="Character " + get_character_name(db, character.id)
                                        + " (with id " + str(character.id) + ") does not have enough money")
