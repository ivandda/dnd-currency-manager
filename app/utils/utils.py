from fastapi import status, HTTPException

from app.models import models


def check_if_exists(exists):
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Does not exist")


def query_get_party_by_id(db, id):
    return db.query(models.Parties).filter(models.Parties.id == id)


def query_get_wallet_by_id(db, id):
    return db.query(models.Wallet).filter(models.Wallet.id == id)


def query_get_character_by_id(db, id):
    return db.query(models.Characters).filter(models.Characters.id == id)


def get_character_name(db, id):
    return query_get_character_by_id(db, id).first().name
