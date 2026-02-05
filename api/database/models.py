import datetime

from sqlmodel import Field, Relationship

from api.database.schemas import AccountBase, CategoryBase, UserBase


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    password: str
    account: list["Account"] | None = Relationship(back_populates="user")
    categories: list["Category"] | None = Relationship(back_populates="user")


class Account(AccountBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: User = Relationship(back_populates="account")


class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: User = Relationship(back_populates="categories")
