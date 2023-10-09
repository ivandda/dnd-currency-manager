from fastapi import FastAPI

from app.models import character_model, wallet_model
from app.routers import wallets_requests, characters_requests
from app.database.database import engine

character_model.Base.metadata.create_all(bind=engine)
wallet_model.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(wallets_requests.router)
app.include_router(characters_requests.router)
