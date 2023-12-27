from fastapi import FastAPI, status
from starlette.responses import RedirectResponse

from app.database.database import engine
from app.dependencies import tags_metadata, swagger_ui_parameters
from app.models import domain
from app.routers import characters, parties, money_dm, money_character, auth
from app.routers import money_parties

domain.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DND currency manager",
    description="API to manage currency of DND characters and parties",
    version="0.1.8",
    openapi_tags=tags_metadata,
    swagger_ui_parameters=swagger_ui_parameters
)


@app.get("/")
async def redirect_to_home_page():
    return RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)


app.include_router(characters.router)
app.include_router(parties.router)
# app.include_router(money_parties.router)
app.include_router(money_dm.router)
app.include_router(money_character.router)
app.include_router(auth.router)
