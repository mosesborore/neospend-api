from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import Session, select

from api.core.config import settings
from api.database.db import get_session
from api.database.models import User

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
    email: str | None = None


def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return password_hash.hash(password)


def get_user(*, email: str, session: Session):
    get_user_expression = select(User).where(User.email == email)
    user = session.exec(get_user_expression).first()

    return user


def authenticate_user(*, email: str, password: str, session: Session):
    """Authenticates the user"""
    user = get_user(email=email, session=session)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None

    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        print(payload)

        user_id: str = payload.get(settings.USER_ID_CLAIM)
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(email=user_id)

    except InvalidTokenError:
        raise credentials_exception

    # get the user from db
    user = get_user(email=token_data.email, session=session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    # todos: get active user only
    return current_user
