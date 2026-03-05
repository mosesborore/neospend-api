import datetime
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel


class TransactionKind(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class CategoryUpdate(SQLModel):
    name: str | None = None


class TransactionBase(SQLModel):
    name: str = Field(min_length=1, max_length=64)
    date: datetime.date
    amount: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=256)
    account_id: int = Field(foreign_key="account.id", index=True, ondelete="CASCADE")
    category_id: int = Field(foreign_key="category.id", index=True, ondelete="CASCADE")
    kind: TransactionKind  # used kind instead of 'type' since it's a Python keyword


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(SQLModel):
    name: str | None = None
    date: datetime.date | None = None
    amount: Decimal | None = None
    notes: str | None = None
    account_id: int | None = None
    category_id: int | None = None
    kind: TransactionKind | None = None
