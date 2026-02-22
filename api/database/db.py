from sqlmodel import Session, SQLModel, create_engine, text

from api.core.config import settings

from . import models  # noqa: F401

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)


def init_db():
    SQLModel.metadata.create_all(engine)

    if "sqlite" in settings.DATABASE_URL:
        with engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_keys=ON"))
            connection.commit()


def get_session():
    """Returns a session to use which is within a context manager"""
    with Session(engine) as session:
        yield session


def create_session():
    """Returns bare Session object"""
    return Session(engine)
