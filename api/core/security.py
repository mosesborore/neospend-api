from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import Session

from api.core.config import settings
from api.database.db import get_session
from api.database.models import User
from api.database.utils import get_user

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


def authenticate_user(*, email: str, password: str, session: Session):
    """Authenticates the user"""
    user = get_user({"email": email}, session=session)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None

    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)
):
    try:
        access_token = AccessToken(token)

        user_id: str = access_token.get(settings.USER_ID_CLAIM)
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)

    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # get the user from db
    user = get_user({"id": token_data.user_id}, session=session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    # todos: get active user only
    return current_user
