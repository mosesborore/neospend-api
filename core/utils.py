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


def get_hash(
    data: bytes | str,
    algorithm: str = "sha256",
    encoding: str = "utf-8",
) -> str:
    """Return a hexadecimal digest of *data* using a cryptographic hash.

    Parameters
    ----------
    data : bytes | str
        The value to be hashed.  ``str`` objects are encoded using
        ``encoding`` before hashing.
    algorithm : str, optional
        Name of the hashlib algorithm to use (``"sha256"`` by default).
    encoding : str, optional
        Character encoding used when ``data`` is a ``str`` (default ``utf-8``).

    Returns
    -------
    str
        Hexadecimal representation of the hash digest.

    Raises
    ------
    TypeError
        If *data* is not ``bytes`` or ``str``.
    ValueError
        If the requested *algorithm* is not supported by :mod:`hashlib`.
    """

    # normalize input
    if isinstance(data, str):
        try:
            value = data.encode(encoding)
        except Exception as exc:  # pragma: no cover - very unlikely
            raise ValueError(f"failed to encode string: {exc}") from exc
    elif isinstance(data, (bytes, bytearray)):
        value = bytes(data)
    else:
        raise TypeError("data must be bytes or str")

    # select and run hash algorithm
    try:
        # ``sha256`` is the common case so we import it at top for speed
        if algorithm.lower() == "sha256":
            h = sha256()
        else:
            from hashlib import new

            h = new(algorithm)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"unsupported hash algorithm: {algorithm}") from exc

    h.update(value)
    return h.hexdigest()
