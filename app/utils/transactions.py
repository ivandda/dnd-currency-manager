from app.utils.utils import *


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
