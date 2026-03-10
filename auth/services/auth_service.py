from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from core.config import settings
from core.tokens import AccessToken, OutstandingToken, RefreshToken, TokenError
from database.db import create_session, get_session
from user.services.user_service import User, get_user, get_user_by_email

from ..models.token import Token, TokenData
from ..utils.auth_utils import verify_password

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", refreshUrl="/api/v1/auth/refresh")


def authenticate_user(email: str, password: str, session: Session):
    user = get_user_by_email(session, email)

    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_tokens(user: User):
    refresh_token = RefreshToken.create_for_user(user)
    refresh_token.save()
    access_token = refresh_token.access_token

    return Token(access_token=str(access_token), refresh_token=str(refresh_token), token_type="bearer")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)
):

    try:
        access_token = AccessToken(token=token)

        user_id = access_token.get(settings.USER_ID_CLAIM)
        if user_id is None:
            raise CREDENTIALS_EXCEPTION
        token_data = TokenData(user_id=int(user_id))

    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not token_data.user_id:
        raise CREDENTIALS_EXCEPTION

    # get the user from db
    user = get_user(session, token_data.user_id)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


async def get_current_user_cookie(request: Request, session: Session = Depends(get_session)):
    # add CSRF token checking, or use middleware
    token = request.cookies.get("auth_token")

    try:
        if not token:
            raise CREDENTIALS_EXCEPTION

        access_token = AccessToken(token=token)

        user_id = access_token.get(settings.USER_ID_CLAIM)

        if user_id is None:
            raise CREDENTIALS_EXCEPTION

        token_data = TokenData(user_id=int(user_id))

    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.user_id is None:
        raise CREDENTIALS_EXCEPTION

    # get the user from db
    user = get_user(session, token_data.user_id)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    # todos: get active user only
    return current_user


def get_outstanding_token_by_jti(jti: str):
    """Retrieves refresh token with `jti` if any"""
    with create_session() as session:
        statement = select(OutstandingToken).where(OutstandingToken.jti == jti)
        return session.exec(statement).first()
