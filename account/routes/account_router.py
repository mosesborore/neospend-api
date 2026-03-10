from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, and_, select

from auth.services.auth_service import get_current_active_user
from core.utils import aware_utcnow
from database.db import get_session
from user.models.user import User

from ..models.account import Account
from ..schemas.account import AccountCreate, AccountUpdate, DeleteResponse
from ..services.account_services import delete_account as delete_account_service
from ..services.account_services import get_account as get_account_service
from ..services.account_services import get_accounts as get_accounts_service

SessionDependency = Annotated[Session, Depends(get_session)]
AuthorizedUser = Annotated[User, Depends(get_current_active_user)]


account_router = APIRouter(prefix="/accounts", tags=["accounts"])


@account_router.post("", response_model=Account)
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


@account_router.get("", response_model=list[Account])
def get_accounts(user: AuthorizedUser, session: SessionDependency):
    accounts = get_accounts_service(session, user.id)  # type: ignore
    return accounts


@account_router.get("/{id}", response_model=Account)
def get_account(id: int, user: AuthorizedUser, session: SessionDependency):
    account = get_account_service(session, id, user.id)  # type: ignore

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not Found")
    return account


@account_router.put("/{id}")
def update_account(id: int, account_payload: AccountUpdate, user: AuthorizedUser, session: SessionDependency):
    statement = select(Account).where(and_(Account.user_id == user.id, Account.id == id))
    account = session.exec(statement).one()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not Found")

    account_data = account_payload.model_dump(exclude_unset=True)

    name = account_data.get("name")
    initial_balance = account_data.get("initial_balance")
    updated = False
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
        account_data.update({"updated_at": aware_utcnow()})
        account.sqlmodel_update(account_data)

        session.add(account)
        session.commit()
        session.refresh(account)
    return account


@account_router.delete("/{id}", response_model=DeleteResponse)
def delete_account(id: int, user: AuthorizedUser, session: SessionDependency):
    deleted = delete_account_service(session, id, user.id) # type: ignore

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unable to delete account.")

    return {"ok": True}
