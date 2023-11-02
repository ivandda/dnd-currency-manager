from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import wallets
from app.utils.checks import *
from app.utils.getters import *

router = APIRouter(
    prefix="/wallets",
    tags=["wallets"]
)


@router.get("/", response_model=List[wallets.WalletResponse])
async def get_all_wallets(db: Session = Depends(get_db)):
    all_wallets = db.query(models.Wallet).all()
    return all_wallets


@router.get("/{id}", response_model=wallets.WalletResponse)
async def get_one_wallet(id: int, db: Session = Depends(get_db)):
    check_wallet_id_exists(db, id)

    wallet_by_id = get_wallet_by_id(db, id).first()

    return wallet_by_id
