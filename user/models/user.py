from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from core.utils import aware_utcnow
from user.schemas.user import UserBase

if TYPE_CHECKING:
    from auth.models.token import OutstandingToken


class User(UserBase, table=True):
    """User Model"""

    id: int | None = Field(default=None, primary_key=True)
    password: str
    created_at: datetime = Field(default_factory=aware_utcnow)
    refresh_tokens: list["OutstandingToken"] | None = Relationship(back_populates="user")
