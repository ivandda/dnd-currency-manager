from fastapi import FastAPI, status
from starlette.responses import RedirectResponse

from app.database.database import engine
from app.dependencies import tags_metadata, swagger_ui_parameters
from app.models import models
from app.routers import home, characters, party, character_transaction, party_transaction

models.Base.metadata.create_all(bind=engine)

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


app.include_router(home.router)
app.include_router(characters.router)
app.include_router(party.router)
app.include_router(character_transaction.router)
app.include_router(party_transaction.router)
