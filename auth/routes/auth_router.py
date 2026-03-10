from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from auth.models.token import Token
from auth.schemas.token import PrevRefreshToken
from auth.services.auth_service import authenticate_user, create_tokens, get_outstanding_token_by_jti
from core.config import settings
from core.schemas import GenericResponse
from core.tokens import RefreshToken, TokenError
from core.utils import aware_utcnow, datetime_from_epoch, get_hash
from database.db import get_session
from user.models.user import User
from user.schemas.user import UserCreate
from user.services.user_service import create_user

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

SessionDependency = Annotated[Session, Depends(get_session)]


@auth_router.post("/register", response_model=GenericResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, response: Response, session: Session = Depends(get_session)):
    try:
        create_user(session, user_data)
        response.status_code = status.HTTP_201_CREATED
        return {"success": True, "msg": "User registered."}
    except IntegrityError:
        response.status_code = status.HTTP_200_OK
        return {"success": False, "msg": "User already exists."}


@auth_router.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDependency):
    user = authenticate_user(form_data.username, form_data.password, session)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = create_tokens(user)

    # set the token in the session
    return tokens


@auth_router.post("/refresh", response_model=Token)
def refresh_token(prev_refresh_token: PrevRefreshToken, session: SessionDependency):
    """
    Refresh access token using a valid refresh token.
    Validates the refresh token and returns new access and refresh tokens.
    """
    try:
        # Decode and validate the refresh token
        refresh_token_obj = RefreshToken(prev_refresh_token.refresh_token)
        refresh_token = refresh_token_obj.token

        # Check if token exists in database and is not revoked
        jti = refresh_token_obj[settings.JTI_CLAIM]
        outstanding_token = get_outstanding_token_by_jti(jti)

        if not outstanding_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # check the hash
        if refresh_token is None:
            refresh_token = prev_refresh_token.refresh_token

        hash_refresh_token = get_hash(refresh_token.encode())

        if hash_refresh_token != outstanding_token.token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if outstanding_token.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if token is expired
        current_time = aware_utcnow()
        if datetime_from_epoch(outstanding_token.expire_at) < current_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get the user
        user_id = refresh_token_obj.get(settings.USER_ID_CLAIM)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = session.get(User, int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create new refresh token (token rotation for security)
        new_refresh = RefreshToken.create_for_user(user)
        new_refresh.save()

        # Revoke the old refresh token
        refresh_token_obj.revoke()

        new_refresh_token = str(new_refresh)
        new_access_token = str(new_refresh.access_token)

        return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")

    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
