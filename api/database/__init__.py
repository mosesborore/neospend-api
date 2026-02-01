from sqlmodel import Session, SQLModel, create_engine

from . import models

__all__ = [models]


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    """Returns a session to use"""
    with Session(engine) as session:
        yield session
        session.close()
