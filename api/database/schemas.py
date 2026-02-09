import datetime
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel


class TransactionKind(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class UserBase(SQLModel):
    name: str | None = Field(default=None)
    email: str = Field(index=True, unique=True)


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    id: int


class AccountBase(SQLModel):
    name: str = Field(min_length=1, max_length=64)
    initial_balance: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    balance: Decimal = Field(default=0, max_digits=12, decimal_places=2)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(SQLModel):
    name: str | None = None
    initial_balance: Decimal | None = None


class CategoryBase(SQLModel):
    name: str = Field(min_length=1, max_length=64)
    kind: TransactionKind


class CategoryCreate(CategoryBase):
    pass


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
