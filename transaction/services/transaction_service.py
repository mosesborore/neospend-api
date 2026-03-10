from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlmodel import Session, and_, select

from account.services import account_services
from category.services import category_service

from ..models.transaction import Transaction
from ..schemas.transaction import TransactionCreate, TransactionKind


def get_transactions(session: Session, user_id: int):
    return session.exec(select(Transaction).where(Transaction.user_id == user_id)).all()


def get_transaction(session: Session, transaction_id: int, user_id: int):
    return session.exec(
        select(Transaction).where(and_(Transaction.id == transaction_id, Transaction.user_id == user_id))
    ).first()


def create_transaction(session: Session, payload: TransactionCreate, user_id: int):

    account = account_services.get_account(session, payload.account_id, user_id)
    category = category_service.get_category(session, payload.category_id, user_id)

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

    payload_dict.update(
        {
            "name": name,
            "user_id": user_id,
            "category": category,
            "account": account,
        }
    )
    try:
        db_transaction = Transaction.model_validate(payload_dict)
        session.add(account)
        session.add(db_transaction)
        session.commit()
        session.refresh(db_transaction)

        return db_transaction
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=e)


def delete_transaction(session: Session, transaction_id: int, user_id: int):
    transaction = get_transaction(session, transaction_id, user_id)
    if transaction is None:
        return False

    session.delete(transaction)
    session.commit()
    return True
