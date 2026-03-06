from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session
from typing_extensions import Literal

from auth.services.auth_service import get_current_active_user
from core.schemas import DeleteResponse
from database.db import get_session
from user.schemas.user import UserPublic

from ..models.category import Category
from ..schemas.category import CategoryCreate, CategoryUpdate
from ..services import category_service

category_router = APIRouter(prefix="/categories", tags=["categories"])


SessionDependency = Annotated[Session, Depends(get_session)]
AuthorizedUser = Annotated[UserPublic, Depends(get_current_active_user)]


KIND_QUERY_PARAM = Literal["all", "income", "expense"]


@category_router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    new_category: CategoryCreate, user: AuthorizedUser, session: SessionDependency, response: Response
):

    category = category_service.create_category(session, new_category, user.id)
    return category


@category_router.get("", response_model=list[Category])
def get_categories(
    *, kind: Annotated[KIND_QUERY_PARAM, Query()] = "all", user: AuthorizedUser, session: SessionDependency
):
    if kind == "all":
        return category_service.get_categories(session, user.id)

    return category_service.get_categories_by_kind(session, user.id, kind)


@category_router.get("/{id}")
def get_category(id: int, user: AuthorizedUser, session: SessionDependency):
    category = category_service.get_category(session, id, user.id)

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not Found")

    return category


@category_router.put("/{id}", response_model=Category)
def update_category(
    id: int, category_payload: CategoryUpdate, user: AuthorizedUser, session: SessionDependency
):
    category = category_service.get_category(session, id, user.id)

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


@category_router.delete("/{id}", response_model=DeleteResponse)
def delete_category(id: int, user: AuthorizedUser, session: SessionDependency):
    deleted = category_service.delete_category(session, id, user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unable to delete: Category not Found"
        )

    return {"ok": deleted}
