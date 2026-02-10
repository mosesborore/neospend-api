from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlmodel import Session, and_, select
from typing_extensions import Literal

from api.core.security import get_current_active_user
from api.database import get_session
from api.database.models import Account, Category, Transaction, User
from api.database.schemas import TransactionCreate, TransactionKind, TransactionUpdate

from .schemas import DeleteResponse

router = APIRouter(prefix="/transactions")

SessionDependency = Annotated[Session, Depends(get_session)]
AuthorizedUser = Annotated[User, Depends(get_current_active_user)]

KIND_QUERY_PARAM = Literal["income", "expense"]


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    *,
    payload: TransactionCreate,
    session: SessionDependency,
    user: AuthorizedUser,
    response: Response,
):
    account = session.get(Account, payload.account_id)
    category = session.get(Category, payload.category_id)

    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    name = payload.name.strip().title()

    if payload.kind == TransactionKind.INCOME:
        new_balance = account.balance + payload.amount
    else:
        new_balance = account.balance - payload.amount

    account.sqlmodel_update({"balance": new_balance})

    payload_dict = payload.model_dump()

    payload_dict.update({"name": name, "user_id": user.id, "category": category, "account": account})
    try:
        db_transaction = Transaction.model_validate(payload_dict)
        session.add(account)
        session.add(db_transaction)
        session.commit()
        session.refresh(db_transaction)

        return db_transaction
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=e)


@router.get("", response_model=list[Transaction])
def get_transactions(user: AuthorizedUser, session: SessionDependency):
    statement = select(Transaction).where(Transaction.user_id == user.id)

    transactions = session.exec(statement).all()

    return transactions


@router.get("/{id}", response_model=Transaction)
def get_transaction(id: int, user: AuthorizedUser, session: SessionDependency):
    statement = select(Transaction).where(and_(Transaction.user_id == user.id, Transaction.id == id))
    transaction = session.exec(statement).first()

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
    statement = select(Transaction).where(and_(Transaction.user_id == user.id, Transaction.id == id))
    transaction = session.exec(statement).first()

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    update_data = payload.model_dump(exclude_unset=True)

    update_kind = payload.kind if payload.kind is not None else transaction.kind
    update_amount = payload.amount if payload.amount is not None else transaction.amount

    # Validate category if provided
    if payload.category_id is not None:
        statement = select(Category).where(
            and_(
                Category.id == payload.category_id, Category.kind == update_kind, Category.user_id == user.id
            )
        )
        category = session.exec(statement).first()

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
    statement = select(Transaction).where(and_(Transaction.id == id, Transaction.user_id == user.id))
    try:
        transaction = session.exec(statement).first()

        if transaction is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

        session.delete(transaction)
        session.commit()
        return {"ok": True}
    except Exception:
        return {"ok": False}
