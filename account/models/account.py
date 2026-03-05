from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from core.utils import aware_utcnow

from ..schemas.account import AccountBase

if TYPE_CHECKING:
    from user.models.user import User


class Account(AccountBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    balance: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    created_at: datetime = Field(default_factory=aware_utcnow)
    updated_at: datetime = Field(default_factory=aware_utcnow)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: "User" = Relationship(back_populates="accounts")
