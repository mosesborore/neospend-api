from sqlmodel import select

from .db import create_session
from .models import OutstandingToken


def get_outstanding_token_by_jti(jti: str):
    """Retrieves refresh token with `jti` if any"""
    with create_session() as session:
        statement = select(OutstandingToken).where(OutstandingToken.jti == jti)
        return session.exec(statement).first()
