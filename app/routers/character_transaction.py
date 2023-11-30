from fastapi import Depends, APIRouter, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.characters import CharacterIdLists
from app.schemas.money import Money
from app.utils.checks import *
from app.utils.currency import *
from app.utils.currency_convertions import convert_to_copper, convert_to_type

router = APIRouter(
    prefix="/character-transaction",
    tags=["character transactions"]
)



