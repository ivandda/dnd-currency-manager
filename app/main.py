from fastapi import FastAPI, status
from starlette.responses import RedirectResponse

from app.models import models
from app.routers import (wallets_requests, characters_requests,
                         party_requests, home_requests, character_transaction_requests)
from app.database.database import engine

models.Base.metadata.create_all(bind=engine)
tags_metadata = [
    {
        "name": "characters",
        "description": "Operations with characters.",
    },
    {
        "name": "party",
        "description": "Operations with parties.",
    },
    {
        "name": "character transactions",
        "description": "Transaction between characters and currency info.",
    },
    {
        "name": "wallets",
        "description": "Operations with wallets.",
    },
]

# more swagger_ui_parameters :https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
swagger_ui_parameters = {"filter": True,
                         "operationsSorter": "method"}

app = FastAPI(
    title="DND currency manager",
    description="API to manage currency of DND characters and parties",
    version="0.0.1",
    openapi_tags=tags_metadata,
    swagger_ui_parameters=swagger_ui_parameters
)


@app.get("/")
async def redirect_to_home_page():
    return RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)


app.include_router(home_requests.router)
app.include_router(characters_requests.router)
app.include_router(party_requests.router)
app.include_router(wallets_requests.router)
app.include_router(character_transaction_requests.router)
