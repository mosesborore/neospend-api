from decimal import Decimal

from sqlmodel import Field, SQLModel
from typing_extensions import Literal

TYPE = Literal["expense", "income"]


class UserBase(SQLModel):
    name: str | None = Field(default=None)
    email: str = Field(index=True, unique=True)


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    id: int


class AccountBase(SQLModel):
    name: str
    balance: Decimal = Field(default=0, max_digits=12, decimal_places=2)


class AccountCreate(AccountBase):
    pass
