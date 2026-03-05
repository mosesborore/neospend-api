from decimal import Decimal

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class AccountBase(SQLModel):
    name: str = Field(min_length=1, max_length=64)
    initial_balance: Decimal = Field(default=0, max_digits=12, decimal_places=2)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(SQLModel):
    name: str | None = None
    initial_balance: Decimal | None = None


class DeleteResponse(BaseModel):
    ok: bool
