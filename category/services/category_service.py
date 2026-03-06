from sqlmodel import Session, and_, select

from ..models.category import Category
from ..schemas.category import CategoryCreate


def get_categories(session: Session, user_id: int):
    return session.exec(select(Category).where(Category.user_id == user_id)).all()


def get_categories_by_kind(session: Session, user_id: int, kind: str):
    return session.exec(
        select(Category).where(and_(Category.user_id == user_id, Category.kind == kind))
    ).all()


def get_category(session: Session, category_id: int, user_id: int):
    return session.exec(
        select(Category).where(and_(Category.id == category_id, Category.user_id == user_id))
    ).first()


def create_category(session: Session, new_category: CategoryCreate, user_id: int):
    payload = new_category.model_copy()
    payload_dict = payload.model_dump()

    payload_dict.update({"name": payload.name.strip().title(), "user_id": user_id})

    db_category = Category(**payload_dict)

    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


def delete_category(session: Session, category_id: int, user_id: int):
    category = get_category(session, category_id, user_id)
    if category is None:
        return False

    session.delete(category)
    session.commit()
    return True
