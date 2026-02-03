from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, and_, select

from api.core.security import get_current_active_user
from api.database import get_session
from api.database.models import Account, User
from api.database.schemas import AccountCreate

router = APIRouter(prefix="/accounts")

SessionDependency = Annotated[Session, Depends(get_session)]
AuthorizedUser = Annotated[User, Depends(get_current_active_user)]


@router.post("", response_model=Account)
def create_account(new_account: AccountCreate, session: SessionDependency, user: AuthorizedUser):
    payload = new_account.model_dump()

    name = payload.get("name")

    name = name.strip().title() if name else "No Title"

    payload.update({"name": name, "user_id": user.id})

    account = Account(**payload)

    session.add(account)

    session.commit()

    session.refresh(account)
    print(payload, account.dict())

    return account


@router.get("", response_model=list[Account])
def get_accounts(user: AuthorizedUser, session: SessionDependency):
    statement = select(Account).where(Account.user_id == user.id)

    accounts = session.exec(statement).all()

    return accounts


@router.get("/{id}", response_model=Account)
def get_account(id: int, user: AuthorizedUser, session: SessionDependency):
    statement = select(Account).where(and_(Account.user_id == user.id, Account.id == id))
    account = session.exec(statement).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not Found")
    return account


class DeleteResp(BaseModel):
    ok: bool


@router.delete("/{id}", response_model=DeleteResp)
def delete_account(id: int, user: AuthorizedUser, session: SessionDependency):
    statement = select(Account).where(and_(Account.user_id == user.id, Account.id == id))
    account = session.exec(statement).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not Found")

    session.delete(account)
    session.commit()
    return {"ok": True}
