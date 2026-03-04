from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import Session

from core.config import settings
from database.db import get_session
from user.models.user import User
from user.services.user_service import get_user_by_email

from .tokens import AccessToken, TokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login", refreshUrl="/api/v1/refresh")
password_hash = PasswordHash.recommended()

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: int | None = None


def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return password_hash.hash(password)


async def get_current_user_cookie(request: Request, session: Session = Depends(get_session)):
    # add CSRF token checking, or use middleware
    token = request.cookies.get("auth_token")

    try:
        if not token:
            raise credentials_exception

        access_token = AccessToken(token=token)

        user_id = access_token.get(settings.USER_ID_CLAIM)

        if user_id is None:
            raise credentials_exception

        token_data = TokenData(user_id=int(user_id))

    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # get the user from db
    user = get_user_by_email({"id": token_data.user_id}, session=session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)
):
    try:
        access_token = AccessToken(token=token)

        user_id = access_token.get(settings.USER_ID_CLAIM)
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=int(user_id))

    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # get the user from db
    user = get_user_by_email({"id": token_data.user_id}, session=session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    # todos: get active user only
    return current_user
