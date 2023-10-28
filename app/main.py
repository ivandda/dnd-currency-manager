from fastapi import FastAPI

from app.models import models
from app.routers import (wallets_requests, characters_requests,
                         party_requests, home_requests, transaction_requests)
from app.database.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(wallets_requests.router)
app.include_router(characters_requests.router)
app.include_router(home_requests.router)
app.include_router(party_requests.router)
app.include_router(transaction_requests.router)
