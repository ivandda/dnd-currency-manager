import re
from http.client import HTTPException
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import characters
from app.utils.auth import get_current_user_id
from app.utils.checks import *
from app.utils.currency import *
from app.utils.getters import *

router = APIRouter(
    prefix="/characters",
    tags=["characters"]
)


@router.post("/", response_model=characters.CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(character: characters.CharacterCreate,
                           db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    character_name = character.name

    if not (re.match("^(?=.*[^0-9])[a-zA-Z0-9_.'&-]{4,}$", character_name)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid character name. Valid characters: a-z, A-Z, 0-9, _ , . , -, &,'. Contains "
                                   "at least one character that is not a number. Has a minimum length of four "
                                   "characters")

    check_character_name_exists(character_name, db)

    new_character = models.Characters(name=character_name, user_id=user_id)
    db.add(new_character)
    db.commit()
    db.refresh(new_character)

    # Add new wallet to character
    character_wallet = models.Wallet(character_owner_id=new_character.id)
    db.add(character_wallet)
    db.commit()
    db.refresh(character_wallet)

    return new_character


@router.get("/", response_model=List[characters.CharacterResponse], status_code=status.HTTP_200_OK)
async def get_characters_from_user(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return get_all_characters_with_user_id(db, user_id)


@router.get("/{character_id}", response_model=characters.CharacterAllInfoResponse, status_code=status.HTTP_200_OK)
async def all_character_info(character_id: int,
                             db: Session = Depends(get_db),
                             user_id: int = Depends(get_current_user_id)):
    check_character_id_exists(db, character_id)
    check_user_id_is_authenticated(user_id, get_user_id_by_character_id(db, character_id))
    return get_all_character_info(db, character_id)
