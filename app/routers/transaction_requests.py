from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.schemas import party_schema, characters_schema
from app.utils.utils import *
from app.utils.transactions import *

router = APIRouter(
    prefix="/transaction",
    tags=["transaction"]
)


@router.get("/getFounds/{id}")
async def check_founds(id: int, db: Session = Depends(get_db)):
    return get_money_in_character_wallet(db, id)


@router.get("/checkFounds/{id}/{amount}")
async def check_founds(id: int, amount: int, db: Session = Depends(get_db)):
    return character_has_founds(db, id, amount)
