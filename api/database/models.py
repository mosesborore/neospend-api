from sqlmodel import Field, Relationship, SQLModel

from api.database.schemas import UserBase


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    password: str
    account: list["Account"] | None = Relationship(back_populates="user")


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    name: str
    balance: float = 0.0
    user_id: int = Field(foreign_key="user.id", index=True)
    user: User = Relationship(back_populates="account")
