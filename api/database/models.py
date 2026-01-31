import logging

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine

logger = logging.getLogger(__name__)


class UserBase(SQLModel):
    name: str | None = Field(default=None)
    email: str = Field(index=True, unique=True)
    password: str
    # active: bool = True


class AccountBase(SQLModel):
    pass


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    account: list["Account"] | None = Relationship(back_populates="user")


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    name: str
    balance: float = 0.0
    user_id: int = Field(foreign_key="user.id", index=True)
    user: User = Relationship(back_populates="account")


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        logger.info("Starting session")

        yield session

        logger.info("Closing session")
        session.close()


if __name__ == "__main__":
    init_db()
