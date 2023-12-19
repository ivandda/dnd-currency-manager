import os
from datetime import timedelta
from typing import Annotated

from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm


from app.database.database import SessionLocal
from app.dependencies import get_db
from app.models import auth
from app.schemas.auth import Token, CreateUser, User
from app.utils.auth import authenticate_user, create_access_token, get_password_hash, get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password, db=SessionLocal())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.post("/users/", response_model=User)
async def create_user(user: CreateUser, db: SessionLocal = Depends(get_db)):
    db_user = auth.User(username=user.username,
                        email=user.email,
                        hashed_password=get_password_hash(user.password),
                        role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
