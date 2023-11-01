from enum import Enum

from fastapi import Response, status, HTTPException, Depends, APIRouter

from app.utils.utils import *
from app.schemas.money import Money


# services

class Currencies(int, Enum):
    platinum = 1000
    gold = 100
    electrum = 50
    silver = 10
    copper = 1


values = {currency.name: currency.value for currency in Currencies}
currency_types = [currency.name for currency in Currencies]


def convert_to_copper(money: Money):
    money_dict = money.model_dump()
    total_copper = sum([values[k] * money_dict[k] for k in values])
    return total_copper


def convert_to_simplified(copper: int) -> dict:
    converted = {"platinum": 0, "gold": 0, "electrum": 0, "silver": 0, "copper": 0}
    for k in values:
        converted[k] = copper // values[k]
        copper -= converted[k] * values[k]

    return converted


def converto_to_type(copper: int, curr_type: str) -> dict:
    total_curr_type = copper // values[curr_type]
    reminder_copper = copper - total_curr_type * values[curr_type]

    converted = convert_to_simplified(reminder_copper)
    converted[curr_type] += total_curr_type

    return converted


def get_wallet_with_character_id(db, character_id):
    return db.query(models.Wallet).filter(models.Wallet.character_owner_id == character_id).first()


def get_money_in_wallet(db, id):
    wallet = query_get_wallet_by_id(db, id)
    return wallet.money


def get_money_in_character_wallet(db, character_id: int) -> int:
    character_wallet = get_wallet_with_character_id(db, character_id)
    character_money = get_money_in_wallet(db, character_wallet.id)

    return character_money


def check_character_has_founds(db, character_id: int, amount: int) -> bool:
    character_money = get_money_in_character_wallet(db, character_id)

    if character_money < amount:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Character "
                                   + get_character_name(db, character_id)
                                   + " (with id " + str(character_id)
                                   + ") does not have enough money")

    else:
        return True


def add_money(db, id: int, amount: int):
    wallet = get_wallet_with_character_id(db, id)
    wallet.money += amount
    db.commit()
    db.refresh(wallet)
    return wallet


def subtract_money(db, id, amount):
    if check_character_has_founds(db, id, amount):
        wallet = get_wallet_with_character_id(db, id)
        wallet.money -= amount
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


def add_money_to_characters_in_party(db, total_money: int, party_id: int):
    characters = get_characters_in_party(db, party_id)
    add_money_to_characters(db, total_money, characters)


def subtract_money_from_characters(db, total_money: int, characters: list):
    money_divided_list = divide_money_evenly(total_money, len(characters))

    for money, character in zip(money_divided_list, characters):
        subtract_money(db, character.id, money)


def subtract_money_from_characters_in_party(db, total_money: int, party_id: int):
    characters = get_characters_in_party(db, party_id)
    subtract_money_from_characters(db, total_money, characters)


def check_founds_for_characters(db, total_money: int, characters: list):
    money_by_character = divide_money_evenly(total_money, len(characters))

    for money, character in zip(money_by_character, characters):
        if not check_character_has_founds(db, character.id, money):
            return Response(status.HTTP_409_CONFLICT,
                            "Character " + get_character_name(db, character.id)
                            + " (with id " + str(character.id) + ") does not have enough money")


def divide_money_evenly_between_characters(db, total_money, characters):
    amounts = divide_money_evenly(total_money, len(characters))
    for i in range(len(characters)):
        subtract_money(db, characters[i].id, amounts[i])


def check_currency_type(currency_type):
    if currency_type not in currency_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid currency type. Valid currency types: " + str(currency_types))
