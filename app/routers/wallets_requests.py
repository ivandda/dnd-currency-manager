from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

from app.models import models
from app.database.database import get_db
from app.schemas import wallets_schema
from app.utils.utils import *

router = APIRouter(
    prefix="/wallets",
    tags=["wallets"]
)


@router.get("/", response_model=List[wallets_schema.WalletResponse])
async def get_all_wallets(db: Session = Depends(get_db)):
    all_wallets = db.query(models.Wallet).all()
    return all_wallets


@router.get("/{id}", response_model=wallets_schema.WalletResponse)
async def get_one_wallet(id: int, db: Session = Depends(get_db)):
    wallet_by_id = query_get_wallet_by_id(db, id).first()
    check_if_exists(wallet_by_id)

    return wallet_by_id


@router.post("/", response_model=wallets_schema.WalletResponse, status_code=status.HTTP_201_CREATED)
async def post_wallet(wallet: wallets_schema.WalletCreate, db: Session = Depends(get_db)):
    new_wallet = models.Wallet(**wallet.model_dump())
    db.add(new_wallet)
    db.commit()
    db.refresh(new_wallet)

    return new_wallet


@router.delete("/{id}")
async def delete_wallet(id: int, db: Session = Depends(get_db)):
    query_wallet_to_delete = query_get_wallet_by_id(db, id)
    check_if_exists(query_wallet_to_delete.first())
    query_wallet_to_delete.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", response_model=wallets_schema.WalletResponse)
async def update_wallet(id: int, info_update: wallets_schema.WalletUpdate, bd: Session = Depends(get_db)):
    info = info_update.model_dump()
    query_wallet_to_modify = query_get_wallet_by_id(bd, id)
    check_if_exists(query_wallet_to_modify.first())
    query_wallet_to_modify.update(info, synchronize_session=False)
    bd.commit()

    return query_get_wallet_by_id(bd, id).first()

