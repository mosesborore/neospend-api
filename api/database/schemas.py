from decimal import Decimal

from sqlmodel import Field, SQLModel


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
    name: str | None
    initial_balance: Decimal | None


class CategoryBase(SQLModel):
    name: str = Field(min_length=1, max_length=64)
    type_: str = Field(
        title="type", serialization_alias="type", validation_alias="type", min_length=1, max_length=64
    )


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(SQLModel):
    name: str | None
    type_: str | None = Field(
        default=None,
        title="type",
        serialization_alias="type",
        validation_alias="type",
        min_length=1,
        max_length=64,
    )
