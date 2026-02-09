from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlmodel import Session, and_, select
from typing_extensions import Literal

from api.core.security import get_current_active_user
from api.database import get_session
from api.database.models import Category, User
from api.database.schemas import CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/categories")

SessionDependency = Annotated[Session, Depends(get_session)]
AuthorizedUser = Annotated[User, Depends(get_current_active_user)]


TYPE_QUERY_PARAM = Literal["all", "income", "expense"]


@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    new_category: CategoryCreate, user: AuthorizedUser, session: SessionDependency, response: Response
):
    payload = new_category.model_dump()

    name = payload.get("name")
    payload.update({"name": name.strip().title(), "user_id": user.id})

    category = Category(**payload)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.get("", response_model=list[Category])
def get_categories(*, t: TYPE_QUERY_PARAM = "all", user: AuthorizedUser, session: SessionDependency):
    if t == "all":
        filter = Category.user_id == user.id
    else:
        filter = and_(Category.user_id == user.id, Category.type_ == t)

    statement = select(Category).where(filter)
    categories = session.exec(statement)
    return categories


@router.get("/{id}")
def get_category(id: int, user: AuthorizedUser, session: SessionDependency):
    statement = select(Category).where(and_(Category.user_id == user.id, Category.id == id))
    category = session.exec(statement).first()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not Found")

    return category


@router.put("/{id}", response_model=Category)
def update_category(
    id: int, category_payload: CategoryUpdate, user: AuthorizedUser, session: SessionDependency
):
    statement = select(Category).where(and_(Category.user_id == user.id, Category.id == id))
    category = session.exec(statement).first()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not Found")
    category_data = category_payload.model_dump(exclude_unset=True)

    name = category_data.get("name")

    if name:
        category_data.update({"name": name.strip().title()})

    category_data.update({"updated_at": datetime.now()})

    category.sqlmodel_update(category_data)

    session.add(category)
    session.commit()
    session.refresh(category)

    return category


class DeleteResp(BaseModel):
    ok: bool


@router.delete("/{id}", response_model=DeleteResp)
def delete_category(id: int, user: AuthorizedUser, session: SessionDependency):
    statement = select(Category).where(and_(Category.user_id == user.id, Category.id == id))
    category = session.exec(statement).first()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not Found")

    session.delete(category)
    session.commit()
    return {"ok": True}
