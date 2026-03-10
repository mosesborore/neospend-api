from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from core.utils import aware_utcnow
from user.models.user import User

from ..schemas.category import CategoryBase

if TYPE_CHECKING:
    from transaction.models.transaction import Transaction


class Category(CategoryBase, table=True):
    """Category Model"""

    id: int | None = Field(default=None, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=aware_utcnow)
    updated_at: datetime = Field(default_factory=aware_utcnow)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: User = Relationship(back_populates="categories")
    transactions: list["Transaction"] | None = Relationship(back_populates="category")
