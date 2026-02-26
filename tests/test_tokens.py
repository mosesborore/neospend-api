from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import jwt
import pytest

from api.core.config import settings
from api.core.tokens import (
    EXP_CLAIM,
    IAT_CLAIM,
    AccessToken,
    ExpiredTokenError,
    RefreshToken,
    Token,
    TokenError,
)
from api.database.models import OutstandingToken, User


class TestTokenError:
    """Test custom exception classes."""

    def test_token_error_inheritance(self):
        """Test that TokenError is a proper exception."""
        error = TokenError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_expired_token_error_inheritance(self):
        """Test that ExpiredTokenError inherits from TokenError."""
        error = ExpiredTokenError("Token expired")
        assert isinstance(error, TokenError)
        assert isinstance(error, Exception)


class TestToken:
    """Test the base Token class."""

    def test_token_requires_token_type_and_lifetime(self):
        """Test that Token cannot be instantiated without token_type and lifetime."""
        with pytest.raises(TokenError, match="Cannot create token with not type or lifetime"):
            Token()

    def test_token_creation_new_token(self):
        """Test creating a new token."""

        # Create a test token class
        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        token = TestToken()

        # Check payload structure
        assert token.payload[settings.TOKEN_TYPE_CLAIM] == "test"
        assert isinstance(token.payload[IAT_CLAIM], int)
        assert isinstance(token.payload[EXP_CLAIM], int)
        assert token.payload[EXP_CLAIM] > token.payload[IAT_CLAIM]
        assert settings.JTI_CLAIM in token.payload

    def test_token_creation_from_existing_valid_token(self):
        """Test creating a token from an existing valid token."""

        # Create a test token class
        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        original_token = TestToken()
        token_str = str(original_token)

        # Create new token from string
        new_token = TestToken(token=token_str)

        assert new_token.payload == original_token.payload

    def test_token_creation_from_expired_token(self):
        """Test that creating a token from an expired token raises ExpiredTokenError."""
        # Create an expired token manually
        expired_payload = {
            settings.TOKEN_TYPE_CLAIM: "test",
            EXP_CLAIM: 0,  # Expired timestamp
            IAT_CLAIM: 0,
            settings.JTI_CLAIM: uuid4().hex,
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        with pytest.raises(ExpiredTokenError, match="Token is expired"):
            TestToken(token=expired_token)

    def test_token_creation_from_invalid_token(self):
        """Test that creating a token from an invalid token raises TokenError."""

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        with pytest.raises(TokenError, match="Token is invalid"):
            TestToken(token="invalid.jwt.token")

    def test_token_get_method(self):
        """Test the get method for retrieving payload values."""

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        token = TestToken()
        token.payload["test_key"] = "test_value"

        assert token.get("test_key") == "test_value"
        assert token.get("nonexistent") is None
        assert token.get("nonexistent", "default") == "default"

    def test_token_magic_methods(self):
        """Test magic methods for payload manipulation."""

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        token = TestToken()

        # Test __getitem__
        token["test_key"] = "test_value"
        assert token["test_key"] == "test_value"

        # Test __setitem__
        token["another_key"] = "another_value"
        assert token.payload["another_key"] == "another_value"

        # Test __delitem__
        del token["another_key"]
        assert "another_key" not in token.payload

        # Test __contains__
        assert "test_key" in token
        assert "nonexistent" not in token

    def test_token_str_method(self):
        """Test that __str__ returns a valid JWT token."""

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        token = TestToken()
        token_str = str(token)

        # Should be able to decode it back
        decoded = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded[settings.TOKEN_TYPE_CLAIM] == "test"

    def test_token_repr_method(self):
        """Test that __repr__ returns payload representation."""

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        token = TestToken()
        assert repr(token) == repr(token.payload)

    def test_set_jti(self):
        """Test setting JTI claim."""

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        token = TestToken()
        original_jti = token.payload[settings.JTI_CLAIM]

        token.set_jti()
        new_jti = token.payload[settings.JTI_CLAIM]

        assert new_jti != original_jti
        assert len(new_jti) == 32  # UUID hex length

    @patch("api.core.tokens.aware_utcnow")
    def test_set_exp(self, mock_utcnow):
        """Test setting expiration time."""
        mock_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_utcnow.return_value = mock_time

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        token = TestToken()

        # Test with default parameters
        token.set_exp()
        expected_exp = int((mock_time + timedelta(hours=1)).timestamp())
        assert token.payload[EXP_CLAIM] == expected_exp

        # Test with custom claim and lifetime
        custom_time = datetime(2026, 1, 1, 13, 0, 0, tzinfo=UTC)
        token.set_exp(claim="custom_exp", from_time=custom_time, lifetime=timedelta(hours=2))
        expected_custom_exp = int((custom_time + timedelta(hours=2)).timestamp())
        assert token.payload["custom_exp"] == expected_custom_exp

    @patch("api.core.tokens.aware_utcnow")
    def test_set_iat(self, mock_utcnow):
        """Test setting issued at time."""
        mock_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_utcnow.return_value = mock_time

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        token = TestToken()

        # Test with default parameters
        token.set_iat()
        assert token.payload[IAT_CLAIM] == int(mock_time.timestamp())

        # Test with custom claim and time
        custom_time = datetime(2026, 1, 1, 13, 0, 0, tzinfo=UTC)
        token.set_iat(claim="custom_iat", at_time=custom_time)
        assert token.payload["custom_iat"] == int(custom_time.timestamp())

    def test_create_token_encoding_error(self):
        """Test that encoding errors are handled properly."""

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        token = TestToken()

        # Mock jwt.encode to raise an exception
        with patch("jwt.encode", side_effect=jwt.exceptions.PyJWTError("Encoding failed")):
            with pytest.raises(TokenError, match="Unable to encode the token"):
                str(token)

    @patch("api.core.tokens.aware_utcnow")
    def test_create_for_user(self, mock_utcnow):
        """Test creating a token for a user."""
        mock_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_utcnow.return_value = mock_time

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        # Create mock user
        mock_user = Mock()
        mock_user.id = 123

        token = TestToken.create_for_user(mock_user)

        assert token.payload[settings.USER_ID_CLAIM] == "123"
        assert token.payload[settings.TOKEN_TYPE_CLAIM] == "test"

    def test_create_for_user_none_user(self):
        """Test that create_for_user raises error for None user."""

        class TestToken(Token):
            token_type = "test"
            lifetime = timedelta(hours=1)

        with pytest.raises(TokenError, match="User cannot be None"):
            TestToken.create_for_user(None)


class TestAccessToken:
    """Test the AccessToken class."""

    @patch("api.core.tokens.aware_utcnow")
    def test_access_token_creation(self, mock_utcnow):
        """Test creating an access token."""
        mock_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_utcnow.return_value = mock_time

        token = AccessToken()

        assert token.payload[settings.TOKEN_TYPE_CLAIM] == "access_token"
        expected_exp = int((mock_time + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
        assert token.payload[EXP_CLAIM] == expected_exp


class TestRefreshToken:
    """Test the RefreshToken class."""

    @patch("api.core.tokens.aware_utcnow")
    def test_refresh_token_creation(self, mock_utcnow):
        """Test creating a refresh token."""
        mock_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_utcnow.return_value = mock_time

        token = RefreshToken()

        assert token.payload[settings.TOKEN_TYPE_CLAIM] == "refresh"
        expected_exp = int((mock_time + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).timestamp())
        assert token.payload[EXP_CLAIM] == expected_exp

    @patch("api.core.tokens.aware_utcnow")
    def test_refresh_token_access_token_property(self, mock_utcnow):
        """Test that refresh token can generate an access token."""
        mock_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_utcnow.return_value = mock_time

        refresh_token = RefreshToken()
        refresh_token[settings.USER_ID_CLAIM] = "123"
        refresh_token["custom_claim"] = "custom_value"

        access_token = refresh_token.access_token

        # Check that access token has the correct type
        assert access_token.payload[settings.TOKEN_TYPE_CLAIM] == "access_token"

        # Check that user_id is copied
        assert access_token.payload[settings.USER_ID_CLAIM] == "123"

        # Check that custom claims are copied
        assert access_token.payload["custom_claim"] == "custom_value"

        assert settings.JTI_CLAIM in access_token.payload
        assert EXP_CLAIM in access_token.payload
        assert IAT_CLAIM in access_token.payload
        assert access_token.payload[settings.TOKEN_TYPE_CLAIM] == "access_token"

    @patch("api.core.tokens.aware_utcnow")
    @patch("api.core.tokens.get_user_by_id")
    @patch("api.core.tokens.get_or_create")
    def test_refresh_token_save(self, mock_get_or_create, mock_get_user, mock_utcnow):
        """Test saving a refresh token to the database."""
        mock_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_utcnow.return_value = mock_time

        # Create mock user
        mock_user = Mock()
        mock_user.id = 123

        # Create mock outstanding token
        mock_outstanding = Mock()

        mock_get_user.return_value = mock_user
        mock_get_or_create.return_value = (mock_outstanding, True)

        refresh_token = RefreshToken()
        refresh_token[settings.USER_ID_CLAIM] = "123"

        result = refresh_token.save()

        # Check that get_user_by_id was called
        mock_get_user.assert_called_once_with(123)

        # Check that get_or_create was called with correct parameters
        mock_get_or_create.assert_called_once()
        call_args = mock_get_or_create.call_args
        assert call_args[0][0] == OutstandingToken
        assert "jti" in call_args[0][1]
        assert call_args[0][1]["jti"] == refresh_token.payload[settings.JTI_CLAIM]
        assert call_args[1]["defaults"]["user_id"] == 123
        assert call_args[1]["defaults"]["jti"] == refresh_token.payload[settings.JTI_CLAIM]
        assert call_args[1]["defaults"]["token"] == str(refresh_token)

        assert result == mock_outstanding

    @patch("api.core.tokens.get_user_by_id")
    def test_refresh_token_save_no_user(self, mock_get_user):
        """Test that save raises error when user doesn't exist."""
        mock_get_user.return_value = None

        refresh_token = RefreshToken()
        refresh_token[settings.USER_ID_CLAIM] = "123"

        with pytest.raises(TokenError, match="Token must have a user"):
            refresh_token.save()

    @patch("api.core.tokens.aware_utcnow")
    @patch("api.core.tokens.datetime_to_epoch")
    @patch("api.core.tokens.create_session")
    def test_refresh_token_revoke(self, mock_create_session, mock_datetime_to_epoch, mock_utcnow):
        """Test revoking a refresh token."""
        mock_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_utcnow.return_value = mock_time

        # Create mock session and token
        mock_session = Mock()
        mock_token = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_token

        mock_create_session.return_value.__enter__.return_value = mock_session
        mock_datetime_to_epoch.return_value = 1234567890

        refresh_token = RefreshToken()

        refresh_token.revoke()

        # Check that the token was marked as revoked
        assert mock_token.revoked_at == 1234567890
        mock_session.commit.assert_called_once()

    @patch("api.core.tokens.create_session")
    def test_refresh_token_revoke_no_token_found(self, mock_create_session):
        """Test revoking a token that doesn't exist in the database."""
        mock_session = Mock()
        refresh_token = RefreshToken()
        mock_session.query.return_value.filter_by.return_value.first.return_value = refresh_token

        mock_create_session.return_value.__enter__.return_value = mock_session

        # Should not raise an error if token doesn't exist
        refresh_token.revoke()

        # Commit should still be called (though it does nothing)
        mock_session.commit.assert_called_once()


class TestGetUserById:
    """Test the get_user_by_id function."""

    @patch("api.core.tokens.create_session")
    def test_get_user_by_id(self, mock_create_session):
        """Test retrieving a user by ID."""
        mock_user = Mock()
        mock_session = Mock()
        mock_session.get.return_value = mock_user

        mock_create_session.return_value.__enter__.return_value = mock_session

        from api.core.tokens import get_user_by_id

        result = get_user_by_id(123)

        mock_session.get.assert_called_once_with(User, 123)
        assert result == mock_user
