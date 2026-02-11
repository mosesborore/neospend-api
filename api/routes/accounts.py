from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, and_, select

from api.core.security import get_current_active_user
from api.database.db import get_session
from api.database.models import Account, User
from api.database.schemas import AccountCreate, AccountUpdate

from .schemas import DeleteResponse

router = APIRouter(prefix="/accounts")

SessionDependency = Annotated[Session, Depends(get_session)]
AuthorizedUser = Annotated[User, Depends(get_current_active_user)]


@router.post("", response_model=Account)
def create_account(new_account: AccountCreate, session: SessionDependency, user: AuthorizedUser):
    payload = new_account.model_dump()

    name = payload.get("name")
    initial_balance = payload.get("initial_balance")

    name = name.strip().title() if name else "No Title"

    payload.update(
        {
            "name": name,
            "user_id": user.id,
            "balance": initial_balance,
        }
    )

    account = Account(**payload)
    session.add(account)
    session.commit()
    session.refresh(account)

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


@router.put("/{id}")
def update_account(id: int, account_payload: AccountUpdate, user: AuthorizedUser, session: SessionDependency):
    statement = select(Account).where(and_(Account.user_id == user.id, Account.id == id))
    account = session.exec(statement).one()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not Found")

    account_data = account_payload.model_dump(exclude_unset=True)
    print("account data: ", account_data)

    name = account_data.get("name")
    initial_balance = account_data.get("initial_balance")
    if name:
        account_data.update({"name": name.strip().title()})
        updated = True
    if initial_balance:
        prev_initial_balance = account.initial_balance
        prev_balance = account.balance

        current_balance = (prev_balance - prev_initial_balance) + initial_balance

        account_data.update({"initial_balance": initial_balance, "balance": current_balance})
        updated = True

    if updated:
        account_data.update({"updated_at": datetime.now()})
        account.sqlmodel_update(account_data)

        session.add(account)
        session.commit()
        session.refresh(account)
    return account


@router.delete("/{id}", response_model=DeleteResponse)
def delete_account(id: int, user: AuthorizedUser, session: SessionDependency):
    statement = select(Account).where(and_(Account.user_id == user.id, Account.id == id))
    account = session.exec(statement).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not Found")

    session.delete(account)
    session.commit()
    return {"ok": True}
