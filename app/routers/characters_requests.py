from http.client import HTTPException

import re

from fastapi import status, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

from app.schemas import characters_schema
from app.database.database import get_db
from app.utils.transactions import *
from app.utils.utils import *

router = APIRouter(
    prefix="/characters",
    tags=["characters"]
)


@router.post("/", response_model=characters_schema.CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(character: characters_schema.CharacterCreate, db: Session = Depends(get_db)):
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


@router.get("/", response_model=List[characters_schema.CharacterResponse], status_code=status.HTTP_200_OK)
async def get_characters(db: Session = Depends(get_db)):
    return get_all_characters(db)


@router.get("/{id}", response_model=characters_schema.CharacterResponse, status_code=status.HTTP_200_OK)
async def get_one_character(id: int, db: Session = Depends(get_db)):
    await check_character_id_exists(db, id)
    character = query_get_character_by_id(db, id)

    return character


@router.get("/get-all-character-info/{id}", response_model=characters_schema.CharacterInfoResponse)
async def get_all_character_info(id: int, db: Session = Depends(get_db)):
    await check_character_id_exists(db, id)
    character = query_get_character_by_id(db, id)

    money_simplified = convert_to_simplified(get_money_in_character_wallet(db, id))

    character_parties_info = [get_info_of_party_with_character(db, party.id)
                              for party in get_all_parties_character_is_in(db, id)]

    return characters_schema.CharacterInfoResponse(id=character.id,
                                                   name=character.name,
                                                   created_at=character.created_at,
                                                   wallet=money_simplified,
                                                   parties=character_parties_info)
