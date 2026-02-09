from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlmodel import Session, and_, select
from typing_extensions import Literal

from api.core.security import get_current_active_user
from api.database import get_session
from api.database.models import Account, Category, Transaction, User
from api.database.schemas import TransactionCreate, TransactionKind

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
def get_accounts(user: AuthorizedUser, session: SessionDependency):
    statement = select(Transaction).where(Transaction.user_id == user.id)

    transactions = session.exec(statement).all()

    return transactions


@router.get("/{id}", response_model=Transaction)
def get_account(id: int, user: AuthorizedUser, session: SessionDependency):
    statement = select(Transaction).where(and_(Transaction.user_id == user.id, Transaction.id == id))
    transaction = session.exec(statement).first()

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not Found")
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
