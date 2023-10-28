from app.utils.utils import *
from fastapi import Response, status, HTTPException, Depends, APIRouter

values = {"platinum": 1000, "gold": 100, "electrum": 50, "silver": 10,"copper": 1}


def get_wallet_by_character_id(db, character_id):
    return db.query(models.Wallet).filter(models.Wallet.character_owner_id == character_id).first()


def get_money_in_wallet(db, id):
    wallet = query_get_wallet_by_id(db, id).first()

    return wallet.money


def get_money_in_character_wallet(db, character_id):
    character_wallet = get_wallet_by_character_id(db, character_id)
    print(character_wallet)
    character_money = get_money_in_wallet(db, character_wallet.id)

    return character_money


def character_has_founds(db, character_id, amount):
    character_money = get_money_in_character_wallet(db, character_id)

    if character_money < amount:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Character "
                                   + get_character_name(db, character_id)
                                   + " (with id " + str(character_id)
                                   + ") does not have enough money")

    else:
        return True


def add_money(db, id, amount):
    wallet = get_wallet_by_character_id(db, id)
    wallet.money += amount
    db.commit()
    db.refresh(wallet)
    return wallet


def subtract_money(db, id, amount):
    if character_has_founds(db, id, amount):
        wallet = get_wallet_by_character_id(db, id)
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


def check_money_available_for_characters(db, total_money: int, characters: list):
    money_by_character = divide_money_evenly(total_money, len(characters))

    for money, character in zip(money_by_character, characters):
        if not character_has_founds(db, character.id, money):
            return Response(status.HTTP_409_CONFLICT,
                            "Character " + get_character_name(db, character.id)
                            + " (with id " + str(character.id) + ") does not have enough money")


def divide_money_evenly_between_characters(db, total_money, characters):
    amounts = divide_money_evenly(total_money, len(characters))
    for i in range(len(characters)):
        subtract_money(db, characters[i].id, amounts[i])
