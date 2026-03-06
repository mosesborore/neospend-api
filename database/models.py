import datetime

from sqlmodel import Field, Relationship

from database.schemas import TransactionBase


class Transaction(TransactionBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: User = Relationship(back_populates="transactions")
    account_id: int = Field(foreign_key="account.id", index=True, ondelete="CASCADE")
    account: Account = Relationship(back_populates="transactions")
    category_id: int = Field(foreign_key="category.id", index=True, ondelete="CASCADE")
    category: Category = Relationship(back_populates="transactions")
