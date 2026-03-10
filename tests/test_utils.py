import pytest

from core.utils import get_hash


def test_get_hash_basic_string():
    # known sha256 of "hello" from online generators
    expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert get_hash("hello") == expected


def test_get_hash_basic_bytes():
    same = get_hash(b"hello")
    assert same == get_hash("hello")


def test_get_hash_with_different_algorithm():
    # md5 of "abc" is well known
    assert get_hash("abc", algorithm="md5") == "900150983cd24fb0d6963f7d28e17f72"


def test_get_hash_encoding():
    # use latin-1 to encode a character not in ascii
    value = "\u00e9"  # 'é'
    # latin1 encodes it as single byte 0xe9
    expected_sha = get_hash(value.encode("latin1"))
    assert get_hash(value, encoding="latin1") == expected_sha


def test_get_hash_invalid_type():
    with pytest.raises(TypeError):
        get_hash(123)


def test_get_hash_invalid_algorithm():
    with pytest.raises(ValueError):
        get_hash(b"data", algorithm="not-a-real-algo")
