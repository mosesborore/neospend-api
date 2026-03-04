from typing import Annotated

from fastapi import APIRouter, Depends

from auth.services.auth_service import get_current_active_user

from ..models.user import User
from ..schemas.user import UserPublic

user_router = APIRouter(prefix="/users", tags=["users"])

AuthorizedUser = Annotated[User, Depends(get_current_active_user)]


@user_router.get("/me", response_model=UserPublic)
async def me(
    user: AuthorizedUser,
):
    return user
