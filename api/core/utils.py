import datetime
from calendar import timegm

from .config import settings


def aware_utcnow():
    """Current time in UTC"""
    return datetime.datetime.now(datetime.UTC)


def datetime_to_epoch(dt: datetime.datetime):
    """Returns Unix timestamp from GMT"""
    if not isinstance(dt, datetime.datetime):
        raise TypeError("dt should an instance of datetime.datetime")

    return timegm(dt.timetuple())


def datetime_from_epoch(ts: float):
    return datetime.datetime.fromtimestamp(ts, tz=datetime.UTC)


def get_refresh_token_expiration():
    expire = aware_utcnow() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return datetime_to_epoch(expire)
