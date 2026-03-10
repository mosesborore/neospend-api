from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing_extensions import Literal

from account.models.account import Account
from auth.services.auth_service import get_current_active_user
from category.services import category_service
from core.schemas import DeleteResponse
from database.db import get_session
from transaction.models.transaction import Transaction
from transaction.schemas.transaction import TransactionCreate, TransactionKind, TransactionUpdate
from user.schemas.user import UserPublic

from ..services import transaction_service

router = APIRouter(prefix="/transactions")

SessionDependency = Annotated[Session, Depends(get_session)]
AuthorizedUser = Annotated[UserPublic, Depends(get_current_active_user)]

KIND_QUERY_PARAM = Literal["income", "expense"]


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(*, payload: TransactionCreate, session: SessionDependency, user: AuthorizedUser):
    return transaction_service.create_transaction(session, payload, user.id)


@router.get("", response_model=list[Transaction])
def get_transactions(user: AuthorizedUser, session: SessionDependency):
    return transaction_service.get_transactions(session, user.id)


@router.get("/{id}", response_model=Transaction)
def get_transaction(id: int, user: AuthorizedUser, session: SessionDependency):
    transaction = transaction_service.get_transaction(session, id, user.id)

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not Found")
    return transaction


@router.put("/{id}", response_model=Transaction)
def update_transaction(
    id: int,
    payload: TransactionUpdate,
    user: AuthorizedUser,
    session: SessionDependency,
):

    transaction = transaction_service.get_transaction(session, id, user.id)

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    update_data = payload.model_dump(exclude_unset=True)

    update_kind = payload.kind if payload.kind is not None else transaction.kind
    update_amount = payload.amount if payload.amount is not None else transaction.amount

    # Validate category if provided
    if payload.category_id is not None:
        category = category_service.get_category(session, payload.category_id, user.id)

        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    # Validate account if provided
    if payload.account_id is not None and payload.account_id != transaction.account_id:
        update_account = session.get(Account, payload.account_id)
        if update_account is None or update_account.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account you are updating to, can not found."
            )

        # account has change, update the previous account
        prev_account = session.get(Account, transaction.account_id)
        if prev_account is None or prev_account.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account you are updating from, can not found.",
            )
        if transaction.kind == TransactionKind.INCOME:
            prev_account_balance = prev_account.balance - transaction.amount
        else:
            prev_account_balance = prev_account.balance + transaction.amount

        prev_account.sqlmodel_update({"balance": prev_account_balance, "updated_at": datetime.now()})
        session.add(prev_account)

        # update the new account
        if update_kind == TransactionKind.INCOME:
            update_account_balance = update_account.balance + update_amount
        else:
            update_account_balance = update_account.balance - update_amount

        update_account.sqlmodel_update({"balance": update_account_balance, "updated_at": datetime.now()})
        session.add(update_account)
    else:
        # account has not changed, check if the amount has changed
        # account is the same; compute net delta based on old and new kind/amount
        prev_effect = (
            transaction.amount if transaction.kind == TransactionKind.INCOME else -transaction.amount
        )
        new_effect = update_amount if update_kind == TransactionKind.INCOME else -update_amount
        delta = new_effect - prev_effect
        if delta != 0:
            update_account_balance = transaction.account.balance + delta
            transaction.account.sqlmodel_update(
                {"balance": update_account_balance, "updated_at": datetime.now()}
            )
        session.add(transaction.account)

    # Handle name capitalization
    if "name" in update_data and update_data["name"] is not None:
        update_data["name"] = update_data["name"].strip().title()

    update_data.update({"updated_at": datetime.now()})
    transaction.sqlmodel_update(update_data)

    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    return transaction


@router.delete("{id}", response_model=DeleteResponse)
def delete_transaction(id: int, session: SessionDependency, user: AuthorizedUser):
    deleted = transaction_service.delete_transaction(session, id, user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unable to delete. Transaction not found."
        )

    return {"ok": deleted}
