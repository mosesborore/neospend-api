from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from api.core.config import settings
from api.core.security import (
    Token,
    authenticate_user,
    get_current_active_user,
    get_password_hash,
    oauth2_scheme,
)
from api.core.tokens import RefreshToken, TokenError
from api.core.utils import aware_utcnow, datetime_from_epoch
from api.database.db import get_session
from api.database.models import OutstandingToken, User
from api.database.schemas import UserCreate, UserPublic

from .schemas import GenericResponse

router = APIRouter()


SessionDep = Annotated[Session, Depends(get_session)]
AuthorizedUser = Annotated[User, Depends(get_current_active_user)]


@router.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    user = authenticate_user(email=form_data.username, password=form_data.password, session=session)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create refresh token and save to database
    refresh = RefreshToken.create_for_user(user)
    refresh.save()  # Save to database for tracking

    refresh_token = str(refresh)
    access_token = str(refresh.access_token)

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post("/refresh", response_model=Token)
def refresh_token(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep):
    """
    Refresh access token using a valid refresh token.
    Validates the refresh token and returns new access and refresh tokens.
    """
    try:
        # Decode and validate the refresh token
        refresh_token = RefreshToken(token)

        # Check if token exists in database and is not revoked
        jti = refresh_token[settings.JTI_CLAIM]
        outstanding_token = session.query(OutstandingToken).filter_by(jti=jti).first()

        if not outstanding_token:
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
        user_id = refresh_token.get(settings.USER_ID_CLAIM)
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
        refresh_token.revoke()

        new_refresh_token = str(new_refresh)
        new_access_token = str(new_refresh.access_token)

        return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")

    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
async def read_own_items(user: AuthorizedUser):
    return [{"item_id": "Foo", "owner": user.email}]
