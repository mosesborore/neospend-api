from enum import Enum

from sqlmodel import Field, SQLModel


class TransactionKind(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class CategoryBase(SQLModel):
    name: str = Field(min_length=1, max_length=64)
    kind: TransactionKind


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(SQLModel):
    name: str | None = None
