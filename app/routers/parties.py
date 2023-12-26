import re
from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import parties, characters, auth_schemas
from app.utils.auth import get_current_user_id
from app.utils.checks import *
from app.utils.currency import *
from app.utils.getters import *
from app.models import auth, models

router = APIRouter(
    prefix="/parties",
    tags=["parties"]
)


@router.get("/", response_model=List[parties.PartyResponse])
async def get_all_parties(db: Session = Depends(get_db)):
    all_parties = db.query(models.Parties).all()

    return all_parties


@router.get("{id}", response_model=parties.PartyAllInfoResponse)
async def get_all_party_info(id: UUID, db: Session = Depends(get_db)):
    check_party_id_exists(db, id)
    return get_all_info_of_party(db, id)


@router.get("/{id}/characters", response_model=List[characters.CharacterResponse])
async def get_characters_in_party(id: UUID, db: Session = Depends(get_db)):
    check_party_id_exists(db, id)
    party = get_party_by_id(db, id)

    return party.characters


@router.post("/", response_model=parties.PartyResponse, status_code=status.HTTP_201_CREATED)
async def create_party(party: parties.PartyCreate, db: Session = Depends(get_db)):
    new_party = models.Parties(**party.model_dump())
    if not (re.match("^(?=.*[^0-9])[a-zA-Z0-9_.'&-]{4,}$", new_party.name)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid character name. Valid characters: a-z, A-Z, 0-9, _ , . , -, &,'. Contains "
                                   "at least one character that is not a number. Has a minimum length of four "
                                   "characters")

    check_party_name_exists(new_party.name, db)

    db.add(new_party)
    db.commit()
    db.refresh(new_party)

    return new_party


@router.put("/{party_id}/add-character/{character_id}", response_model=parties.PartyResponse)
async def add_characters_to_party(party_id: UUID, character_id: UUID, db: Session = Depends(get_db)):
    check_party_id_exists(db, party_id)
    check_character_id_exists(db, character_id)

    party = get_party_by_id(db, party_id)
    character = get_character_by_id(db, character_id)

    check_character_is_in_party(db, party_id, character_id)

    party.characters.append(character)
    db.commit()

    return party


@router.post("/{party_id}/assign-dm/", response_model=parties.PartyResponse)
async def assign_dm(party_id: UUID, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    check_party_id_exists(db, party_id)
    check_character_is_in_party(db, party_id, user_id)

    party = get_party_by_id(db, party_id)
    user = get_user_by_id(db, user_id)

    party.users.append(user)

    db.commit()
    return get_party_by_id(db, party_id)


@router.get("/{party_id}/get-dm/", response_model=List[auth_schemas.UserResponse])
async def get_dm(party_id: UUID, db: Session = Depends(get_db)):
    check_party_id_exists(db, party_id)
    dms = get_dms_of_party(db, party_id)
    return [dm for dm in dms]
