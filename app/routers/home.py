from fastapi import APIRouter

router = APIRouter(
    prefix="/home",
    tags=["home"]
)


@router.get("")
async def home():
    return {"message": "Welcome to the home page!"}
