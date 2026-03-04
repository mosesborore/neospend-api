from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from core.utils import aware_utcnow
from user.models.user import User


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: int | None = None


class OutstandingToken(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token: str
    jti: str = Field(unique=True, max_length=255)
    issued_at: int = Field(default=aware_utcnow())
    expire_at: int = Field(nullable=False)
    revoked_at: int | None = Field(default=None)  # manual revocation
    created_at: datetime = Field(default_factory=aware_utcnow, nullable=True)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="refresh_tokens")
