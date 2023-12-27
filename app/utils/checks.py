from uuid import UUID

from fastapi import status, HTTPException

from app.models import auth
from app.utils.constants import currency_types
from app.utils.getters import get_all_character_ids, get_all_character_names, get_all_party_ids, get_all_party_names, \
    get_all_characters_id_in_party


def check_character_id_exists(db, id: UUID):
    if id not in get_all_character_ids(db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Character with id " + str(id) + " not found")


def check_character_name_exists(character_name, db):
    if character_name in get_all_character_names(db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Character name already exists")


def check_party_id_exists(db, id: UUID):
    if id not in get_all_party_ids(db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Party does not exist")


def check_party_name_exists(name, db):
    if name in get_all_party_names(db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Party name already exists")


def check_character_is_in_party(db, party_id, character_id):
    if character_id in get_all_characters_id_in_party(db, party_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Character is already in party")


def check_party_has_characters(db, party_id):
    if len(get_all_characters_id_in_party(db, party_id)) == 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Party " + str(party_id) + " has no characters")


def check_currency_type(currency_type):
    if currency_type not in currency_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid currency type. Valid currency types: " + str(currency_types))


def check_current_user_role(user_roll: str, current_user_id: UUID, db):
    current_user_role = db.query(auth.User).filter(auth.User.id == current_user_id).first().role
    if current_user_role != user_roll:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User role invalid for this operation")
