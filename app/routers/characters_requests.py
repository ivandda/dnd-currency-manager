from fastapi import status, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

from app.models import character_model
from app.schemas import characters_schema
from app.database.database import get_db

router = APIRouter(
    prefix="/characters",
    tags=["characters"]
)


@router.post("/", response_model=characters_schema.CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(character: characters_schema.CharacterCreate, db: Session = Depends(get_db)):
    new_character = character_model.Characters(**character.model_dump())
    db.add(new_character)
    db.commit()
    db.refresh(new_character)

    return new_character


@router.get("/", response_model=List[characters_schema.CharacterResponse], status_code=status.HTTP_200_OK)
async def get_all_characters(db: Session = Depends(get_db)):
    characters = db.query(character_model.Characters).all()
    return characters
