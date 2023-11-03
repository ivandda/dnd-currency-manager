import re
from http.client import HTTPException
from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import characters
from app.utils.checks import *
from app.utils.currency import *
from app.utils.getters import *

router = APIRouter(
    prefix="/characters",
    tags=["characters"]
)


@router.post("/", response_model=characters.CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(character: characters.CharacterCreate, db: Session = Depends(get_db)):
    # new_character = models.Characters(**character.model_dump())
    character_name = character.name

    if not (re.match("^[a-zA-Z0-9_.-]+$", character_name)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid character name. Valid characters: a-z, A-Z, 0-9, _ , . , -")

    await check_character_name_exists(character_name, db)

    new_character = models.Characters(name=character_name)
    db.add(new_character)
    db.commit()
    db.refresh(new_character)

    # Add new wallet to character
    characterWallet = models.Wallet(character_owner_id=new_character.id)
    db.add(characterWallet)
    db.commit()
    db.refresh(characterWallet)

    return new_character


@router.get("/", response_model=List[characters.CharacterResponse], status_code=status.HTTP_200_OK)
async def get_characters(db: Session = Depends(get_db)):
    return get_all_characters(db)


@router.get("/{id}", response_model=characters.CharacterResponse, status_code=status.HTTP_200_OK)
async def get_one_character(id: int, db: Session = Depends(get_db)):
    await check_character_id_exists(db, id)
    character = get_character_by_id(db, id)

    return character


@router.get("/all-info/{id}", response_model=characters.CharacterAllInfoResponse, status_code=status.HTTP_200_OK)
async def all_character_info(id: int, db: Session = Depends(get_db)):
    await check_character_id_exists(db, id)
    return get_all_character_info(db, id)

