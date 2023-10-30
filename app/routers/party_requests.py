from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List
import re

from app.database.database import get_db
from app.schemas import party_schema, characters_schema
from app.utils.utils import *

router = APIRouter(
    prefix="/party",
    tags=["party"]
)


@router.get("/", response_model=List[party_schema.PartyResponse])
async def get_all_parties(db: Session = Depends(get_db)):
    all_parties = db.query(models.Parties).all()

    return all_parties


@router.get("/{id}", response_model=party_schema.PartyResponse)
async def get_one_party(id: int, db: Session = Depends(get_db)):
    party_by_id = query_get_party_by_id(db, id).first()
    check_if_exists(party_by_id)

    return party_by_id


@router.get("/{id}/characters", response_model=List[characters_schema.CharacterResponse])
async def get_characters_in_party(id: int, db: Session = Depends(get_db)):
    party = query_get_party_by_id(db, id).first()
    check_if_exists(party)

    return party.characters


@router.post("/", response_model=party_schema.PartyResponse, status_code=status.HTTP_201_CREATED)
async def create_party(party: party_schema.PartyCreate, db: Session = Depends(get_db)):
    new_party = models.Parties(**party.model_dump())
    if not (re.match("^[a-zA-Z0-9_.-]+$", new_party.name)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid party name")
    db.add(new_party)
    db.commit()
    db.refresh(new_party)

    return new_party


@router.put("/{id}", response_model=party_schema.PartyResponse)
async def add_characters_to_party(id: int, characters: party_schema.PartyAddCharacters, db: Session = Depends(get_db)):
    party = query_get_party_by_id(db, id).first()
    check_if_exists(party)

    for character_id in characters.characters_id:
        print(character_id)
        if character_id in [character.id for character in party.characters]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="No characters added, character "
                                       + get_character_name(db, character_id)
                                       + " (id: " + str(character_id)
                                       + ") is already in party")

        character = db.query(models.Characters).filter(models.Characters.id == character_id).first()
        check_if_exists(character)
        party.characters.append(character)

    db.commit()

    return party
