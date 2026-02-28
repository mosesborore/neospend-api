from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlmodel import select

from api.core.config import settings
from api.database.db import create_session
from api.database.models import OutstandingToken, User
from api.database.utils import get_or_create

from .utils import aware_utcnow, datetime_to_epoch

# JWT claim constants
EXP_CLAIM = "exp"
IAT_CLAIM = "iat"


class TokenError(Exception):
    pass


class ExpiredTokenError(TokenError):
    pass


class Token:
    """Class to validate and wrap existing JWT or create new JWT"""

    token_type: Optional[None] = None
    lifetime: Optional[timedelta] = None

    def __init__(self, token: Optional["Token"] = None, verify: bool = True):
        if self.token_type is None or self.lifetime is None:
            raise TokenError("Cannot create token with not type or lifetime")

        self.token = token
        self.current_time = aware_utcnow()

        if token is not None:
            try:
                self.payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            except ExpiredSignatureError as e:
                raise ExpiredTokenError("Token is expired") from e
            except InvalidTokenError as e:
                raise TokenError("Token is invalid") from e

            if verify:
                self.verify()
        else:
            self.payload = {settings.TOKEN_TYPE_CLAIM: self.token_type}
            self.set_iat(at_time=self.current_time)
            self.set_exp(from_time=self.current_time, lifetime=self.lifetime)
            self.set_jti()

    def verify(self):
        """perform additional validation"""
        if settings.JTI_CLAIM is not None and settings.JTI_CLAIM not in self.payload:
            raise TokenError("Token has no id")

    def set_jti(self) -> None:
        """
        Populates the configured jti claim of a token with a UUID string that identifies the token
        """
        self.payload[settings.JTI_CLAIM] = uuid4().hex

    def set_exp(
        self,
        claim: str = EXP_CLAIM,
        from_time: Optional[datetime] = None,
        lifetime: Optional[timedelta] = None,
    ):
        """updates the expiration time of the token"""
        if from_time is None:
            from_time = self.current_time
        if lifetime is None:
            lifetime = self.lifetime

        exp = from_time + lifetime

        self.payload[claim] = datetime_to_epoch(exp)

    def set_iat(self, claim: str = IAT_CLAIM, at_time: Optional[datetime] = None):
        """Updates the time at which the token was issued."""
        if at_time is None:
            at_time = self.current_time
        self.payload[claim] = datetime_to_epoch(at_time)

    def _create(self):
        """Encodes the payload into JWT token"""
        try:
            token = jwt.encode(self.payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            return token
        except jwt.exceptions.PyJWTError as e:
            raise TokenError("Unable to encode the token") from e

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.payload.get(key, default)

    def __str__(self):
        """returns a token"""
        return self._create()

    def __repr__(self):
        return repr(self.payload)

    def __getitem__(self, key: str):
        return self.payload[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.payload[key] = value

    def __delitem__(self, key: str) -> None:
        del self.payload[key]

    def __contains__(self, key: str) -> Any:
        return key in self.payload

    @classmethod
    def create_for_user(cls, user: User) -> "Token":
        if user is None:
            raise TokenError("User cannot be None")

        # TODO: check if the user is active (add is_active field to User model)
        user_id = str(user.id)

        token = cls()
        token[settings.USER_ID_CLAIM] = user_id

        return token


class AccessToken(Token):
    token_type = "access_token"
    lifetime = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def get_user_by_id(user_id: int):
    with create_session() as session:
        return session.get(User, user_id)


class RefreshToken(Token):
    token_type = "refresh"
    lifetime = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token_class = AccessToken

    no_copy_claims = (settings.TOKEN_TYPE_CLAIM, settings.JTI_CLAIM, EXP_CLAIM, IAT_CLAIM)

    @property
    def access_token(self) -> AccessToken:
        access = self.access_token_class()

        access.set_exp(from_time=self.current_time)
        no_copy = self.no_copy_claims

        for claim, value in self.payload.items():
            if claim in no_copy:
                continue
            access[claim] = value

        return access

    def save(self) -> OutstandingToken:
        """
        Saves this token in the db
        """
        jti = self.payload[settings.JTI_CLAIM]
        exp = self.payload[EXP_CLAIM]
        user_id = int(self.payload.get(settings.USER_ID_CLAIM))

        user = get_user_by_id(user_id)

        if user is None:
            raise TokenError("Token must have a user")

        obj, _ = get_or_create(
            OutstandingToken,
            {"jti": jti},
            defaults={
                "jti": jti,
                "user_id": user.id,
                "token": str(self),
                "expire_at": exp,
            },
        )
        return obj

    def revoke(self) -> None:
        """
        Revokes this refresh token by marking it as revoked in the database
        """
        jti = self.payload[settings.JTI_CLAIM]

        with create_session() as session:
            statement = select(OutstandingToken).filter_by(jti=jti)
            token = session.exec(statement).first()
            if token:
                token.revoked_at = datetime_to_epoch(self.current_time)
                session.commit()
