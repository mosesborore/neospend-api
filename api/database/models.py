from sqlmodel import Field, Relationship

from api.database.schemas import AccountBase, UserBase


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    password: str
    account: list["Account"] | None = Relationship(back_populates="user")


class Account(AccountBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    user: User = Relationship(back_populates="account")
