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
                           db: Session = Depends(get_db),
                           user_id: int = Depends(get_current_user_id)):
    character_name = character.name

    check_character_name_exists(character_name, db)

    new_character = domain.Characters(name=character_name)
    db.add(new_character)
    new_character.users.append(get_user_by_id(db, user_id))

    db.commit()
    db.refresh(new_character)

    # Add new wallet to character
    character_wallet = domain.Wallet(character_id=new_character.id)
    db.add(character_wallet)
    db.commit()
    db.refresh(character_wallet)

    return new_character


@router.get("/info", response_model=List[characters.CharacterAllInfoResponse], status_code=status.HTTP_200_OK)
async def get_all_info_of_all_characters_from_user(db: Session = Depends(get_db),
                                                   user_id: UUID = Depends(get_current_user_id)):
    all_characters = get_all_characters_with_user_id(db, user_id)
    return [get_all_character_info(db, character.id) for character in all_characters]


@router.get("/{character_id}/info", response_model=characters.CharacterAllInfoResponse, status_code=status.HTTP_200_OK)
async def all_character_info(character_id: UUID,
                             db: Session = Depends(get_db),
                             user_id: int = Depends(get_current_user_id)):
    character = get_character_with_user_id_and_character_id(db, user_id, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Character not found")
    return get_all_character_info(db, character_id)
