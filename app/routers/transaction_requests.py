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


@router.put("/sum/{id}/{amount}", status_code=status.HTTP_200_OK)
async def sum_money_to_character(id: int, amount: int, db: Session = Depends(get_db)):
    add_money(db, id, amount)
    return {"message": "Character " + get_character_name(db, id)
                       + " (with id " + str(id) + ") has received " + str(amount)}


@router.put("/subtract/{id}/{amount}", status_code=status.HTTP_200_OK)
async def subtract_money_to_character(id: int, amount: int, db: Session = Depends(get_db)):
    subtract_money(db, id, amount)
    return {"message": "Character " + get_character_name(db, id)
                       + " (with id " + str(id) + ") has lost " + str(amount)}


@router.put("/transfer/{id}/{id2}/{amount}", status_code=status.HTTP_200_OK)
async def transfer_money(id: int, amount: int, id2: int, db: Session = Depends(get_db)):
    character_has_founds(db, id, amount)
    subtract_money(db, id, amount)
    add_money(db, id2, amount)
    return {"message": "Transfer completed"}

