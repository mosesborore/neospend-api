from typing import Any

from sqlmodel import Session, select

from auth.utils.auth_utils import get_password_hash
from user.models.user import User
from user.schemas.user import UserCreate


def get_users(session: Session):
    return session.exec(select(User)).all()


def get_user_by_email(session: Session, email: str):
    return session.exec(select(User).where(User.email == email)).first()


def get_user(session: Session, user_id: int):
    statement = select(User).where(User.id == user_id)
    return session.exec(statement).first()


def get_user_by_filters(filters: dict[str, Any], session: Session):
    """Retrieve the user using `filters` criteria

    :param filters: dict with filtering criteria
    :param session: db session to use

    :returns: User or None
    """
    statement = select(User).filter_by(**filters)
    return session.exec(statement).first()


def create_user(session: Session, user: UserCreate):
    payload = user.model_dump()
    data = payload.copy()

    data.update({"password": get_password_hash(data["password"])})
    db_user = User(**data)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


def delete_user(session: Session, user_id: int):
    db_user = session.exec(select(User).where(User.id == user_id)).first()

    if db_user:
        session.delete(db_user)
        session.commit()
