import datetime
from decimal import Decimal

from sqlmodel import Field, Relationship, SQLModel

from api.database.schemas import AccountBase, CategoryBase, TransactionBase, UserBase


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    password: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    account: list["Account"] | None = Relationship(back_populates="user")
    categories: list["Category"] | None = Relationship(back_populates="user")
    transactions: list["Transaction"] | None = Relationship(back_populates="user")
    refresh_tokens: list["OutstandingToken"] | None = Relationship(back_populates="user")


class OutstandingToken(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token: str
    jti: str = Field(unique=True, max_length=255)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="refresh_tokens")
    issued_at: int = Field(default=datetime.datetime.now(datetime.UTC))
    expire_at: int = Field(nullable=False)
    revoked_at: int | None = Field(default=None)  # manual revocation
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=True)


class Account(AccountBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    balance: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: User = Relationship(back_populates="account")
    transactions: list["Transaction"] = Relationship(back_populates="account")


class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: User = Relationship(back_populates="categories")
    transactions: list["Transaction"] = Relationship(back_populates="category")


class Transaction(TransactionBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: User = Relationship(back_populates="transactions")
    account_id: int = Field(foreign_key="account.id", index=True, ondelete="CASCADE")
    account: Account = Relationship(back_populates="transactions")
    category_id: int = Field(foreign_key="category.id", index=True, ondelete="CASCADE")
    category: Category = Relationship(back_populates="transactions")
