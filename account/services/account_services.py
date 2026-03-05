from sqlmodel import Session, and_, select

from ..models.account import Account
from ..schemas.account import AccountCreate


def get_accounts(session: Session, user_id: int):
    return session.exec(select(Account).where(Account.user_id == user_id)).all()


def get_account(session: Session, account_id: int, user_id: int):
    statement = select(Account).where(and_(Account.user_id == user_id, Account.id == account_id))
    return session.exec(statement).first()


def create_account(session: Session, new_account: AccountCreate, user_id: int):
    payload = new_account.model_dump()

    name = payload.get("name")
    initial_balance = payload.get("initial_balance")

    name = name.strip().title() if name else "No Title"

    payload.update(
        {
            "name": name,
            "user_id": user_id,
            "balance": initial_balance,
        }
    )

    account = Account(**payload)
    session.add(account)
    session.commit()
    session.refresh(account)

    return account


def delete_account(session: Session, account_id: int, user_id: int):
    statement = select(Account).where(and_(Account.user_id == user_id, Account.id == account_id))

    db_account = session.exec(statement).first()

    if db_account:
        session.delete(db_account)
        session.commit()
        return True

    return False
