from fastapi import status, HTTPException

from app.models import models


# repositorios
def check_if_exists(exists):
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Does not exist")


def query_get_party_by_id(db, id):
    return db.query(models.Parties).filter(models.Parties.id == id).first()


def query_get_wallet_by_id(db, id):
    return db.query(models.Wallet).filter(models.Wallet.id == id).first()


def query_get_character_by_id(db, id):
    return db.query(models.Characters).filter(models.Characters.id == id).first()


def get_character_name(db, id):
    # return query_get_character_by_id(db, id).first().name
    return query_get_character_by_id(db, id).name


def get_all_characters(db):
    return db.query(models.Characters).all()


def get_all_character_names(db):
    return [character.name for character in get_all_characters(db)]


def get_all_character_ids(db):
    return [character.id for character in get_all_characters(db)]


def get_all_parties(db):
    return db.query(models.Parties).all()


def get_all_party_names(db):
    return [party.name for party in get_all_parties(db)]


def get_all_party_ids(db):
    return [party.id for party in get_all_parties(db)]


# def get_all_characters_in_party(db, party_id):
#     party = query_get_party_by_id(db, party_id)
#     return party.characters


def get_all_characters_in_party(db, party_id):
    party = query_get_party_by_id(db, party_id)
    return [character.id for character in party.characters]


def get_all_wallet_ids(db):
    return [wallet.id for wallet in db.query(models.Wallet).all()]


async def check_character_id_exists(db, id):
    if id not in get_all_character_ids(db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Character does not exist")


async def check_character_name_exists(character_name, db):
    if character_name in get_all_character_names(db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Character name already exists")


def check_party_id_exists(db, id):
    if id not in get_all_party_ids(db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Party does not exist")


def check_party_name_exists(name, db):
    if name in get_all_party_names(db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Party name already exists")


def check_character_is_in_party(db, party_id, character_id):
    if character_id in get_all_characters_in_party(db, party_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Character is already in party")


def check_wallet_id_exists(db, id):
    if id not in get_all_wallet_ids(db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Wallet does not exist")
