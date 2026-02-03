from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    name: str | None = Field(default=None)
    email: str = Field(index=True, unique=True)


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    id: int


class AccountBase(SQLModel):
    name: str
    balance: float = 0.0


class AccountCreate(AccountBase):
    pass
