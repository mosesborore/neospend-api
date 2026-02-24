from uuid import uuid4

from api.database.models import OutstandingToken
from api.database.utils import get_or_create


def test_get_or_create():
    jti = uuid4().hex
    token = uuid4().hex
    obj, created = get_or_create(
        OutstandingToken,
        {"jti": jti},
        defaults={
            "jti": jti,
            "user_id": 1,
            "token": token,
            "expire_at": 1799999,
        },
    )

    assert created
    assert obj.jti == jti

    obj_, created_ = get_or_create(
        OutstandingToken,
        {"jti": jti},
        defaults={
            "jti": jti,
            "user_id": 1,
            "token": token,
            "expire_at": 1799999,
        },
    )

    assert not created_
    assert obj_.jti == jti
