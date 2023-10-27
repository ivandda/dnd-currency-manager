from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

from app.models import models
from app.database.database import get_db
from app.schemas import party_schema, characters_schema

router = APIRouter(
    prefix="/party",
    tags=["party"]
)


@router.get("/", response_model=List[party_schema.PartyResponse])
async def get_all_wallets(db: Session = Depends(get_db)):
    all_parties = db.query(models.Parties).all()

    return all_parties


@router.get("/{id}", response_model=party_schema.PartyResponse)
async def get_one_wallet(id: int, db: Session = Depends(get_db)):
    party_by_id = query_get_party_by_id(db, id).first()
    check_if_exists(party_by_id)

    return party_by_id


@router.get("/{id}/characters", response_model=List[characters_schema.CharacterResponse])
async def get_characters_in_party(id: int, db: Session = Depends(get_db)):
    party = query_get_party_by_id(db, id).first()
    check_if_exists(party)

    return get_characters_in_party(party)


@router.post("/", response_model=party_schema.PartyResponse, status_code=status.HTTP_201_CREATED)
async def create_party(party: party_schema.PartyCreate, db: Session = Depends(get_db)):
    new_party = models.Parties(**party.model_dump())
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
                                detail="No characters added, one is already in party")

        character = db.query(models.Characters).filter(models.Characters.id == character_id).first()
        check_if_exists(character)
        party.characters.append(character)

    db.commit()

    return party


def query_get_party_by_id(db, id):
    return db.query(models.Parties).filter(models.Parties.id == id)


def check_if_exists(exists):
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Does not exist")


def get_characters_in_party(party):
    return party.characters
