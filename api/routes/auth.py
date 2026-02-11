from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from api.core.security import (
    EXPIRE_MINUTES,
    Token,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)
from api.database.db import get_session
from api.database.models import User
from api.database.schemas import UserCreate, UserPublic

from .schemas import GenericResponse

router = APIRouter()


SessionDep = Annotated[Session, Depends(get_session)]
AuthorizedUser = Annotated[User, Depends(get_current_active_user)]


@router.post("/login")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    user = authenticate_user(email=form_data.username, password=form_data.password, session=session)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=GenericResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, response: Response, session: Session = Depends(get_session)):
    try:
        data = user_data.model_dump()

        data.update({"password": get_password_hash(data["password"])})
        new_user = User(**data)
        session.add(new_user)
        session.commit()
        response.status_code = status.HTTP_201_CREATED
        return {"msg": "User registered."}
    except IntegrityError:
        response.status_code = status.HTTP_200_OK
        return {"msg": "User already exists."}


@router.get("/users/me/", response_model=UserPublic)
async def read_users_me(
    user: AuthorizedUser,
):
    return user


@router.get("/users/me/items/")
async def read_own_items(
    user: AuthorizedUser,
):
    return [{"item_id": "Foo", "owner": user.email}]
