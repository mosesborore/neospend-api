from datetime import datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import Session, select

from api.database import get_session
from api.database.models import User

SECRET_KEY = "328332cc7c45657a25beba138361da12c39ce9372f744e47f352a3cb31fbd9869c2bd8ea50d1c8fd32b16558563e3aab990d33de7a07324f6896c63640106cd107177334da3858a3e134aff16b087baf5199d217c3aa5528b32fc305f0e1501d1cf6bfb8ac476134e7f69edc59d89ece8a53bf7985517404aa1325f438a1e0"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
password_hash = PasswordHash.recommended()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=EXPIRE_MINUTES))

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class Token(BaseModel):
    access_token: str
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)

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
