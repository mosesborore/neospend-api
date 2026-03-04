import datetime
from calendar import timegm
from hashlib import sha256


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


def get_hash(data: bytes):
    """returns the hash of the `data` using sha256 function"""
    return sha256(data).hexdigest()
