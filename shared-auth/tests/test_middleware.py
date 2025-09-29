"""
Unit tests for Auth0 middleware.

Test ID: AUTH-UNIT-081 to AUTH-UNIT-120
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from shared_auth.middleware import Auth0Middleware
from shared_auth.models import AuthUser
from shared_auth.exceptions import (
    InvalidTokenError,
    ExpiredTokenError,
    MissingClaimError,
    ConfigurationError,
)


class TestAuth0MiddlewareInitialization:
    """Test Auth0Middleware initialization."""
    
    def test_middleware_init_with_parameters(self):
        """AUTH-UNIT-081: Test middleware initialization with parameters."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com",
            algorithms=["RS256", "HS256"]
        )
        
        assert middleware.domain == "test.auth0.com"
        assert middleware.api_identifier == "https://test-api.example.com"
        assert middleware.algorithms == ["RS256", "HS256"]
        assert middleware.jwks_url == "https://test.auth0.com/.well-known/jwks.json"
        assert middleware.issuer == "https://test.auth0.com/"
    
    def test_middleware_init_from_environment(self):
        """AUTH-UNIT-082: Test middleware initialization from environment variables."""
        with patch.dict(os.environ, {
            "AUTH0_DOMAIN": "env.auth0.com",
            "AUTH0_API_IDENTIFIER": "https://env-api.example.com",
            "AUTH0_ALGORITHMS": "HS256"
        }):
            middleware = Auth0Middleware()
            
            assert middleware.domain == "env.auth0.com"
            assert middleware.api_identifier == "https://env-api.example.com"
            assert middleware.algorithms == ["HS256"]
    
    def test_middleware_init_missing_domain(self):
        """AUTH-UNIT-083: Test middleware initialization fails without domain."""
        with pytest.raises(ConfigurationError) as exc_info:
            Auth0Middleware(api_identifier="https://test-api.example.com")
        
        assert "AUTH0_DOMAIN is required" in str(exc_info.value)
        assert exc_info.value.error_code == "CONFIGURATION_ERROR"
    
    def test_middleware_init_missing_api_identifier(self):
        """AUTH-UNIT-084: Test middleware initialization fails without API identifier."""
        with pytest.raises(ConfigurationError) as exc_info:
            Auth0Middleware(domain="test.auth0.com")
        
        assert "AUTH0_API_IDENTIFIER is required" in str(exc_info.value)
        assert exc_info.value.error_code == "CONFIGURATION_ERROR"
    
    def test_middleware_init_default_values(self):
        """AUTH-UNIT-085: Test middleware initialization with default values."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        assert middleware.algorithms == ["RS256"]
        assert middleware.cache_jwks is True
        assert middleware.jwks_cache_ttl == 3600


class TestJWKSHandling:
    """Test JWKS fetching and caching."""
    
    @patch("requests.get")
    def test_get_jwks_success(self, mock_get, mock_jwks):
        """AUTH-UNIT-086: Test successful JWKS fetching."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_jwks
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        result = middleware._get_jwks()
        
        assert result == mock_jwks
        mock_get.assert_called_once_with(
            "https://test.auth0.com/.well-known/jwks.json",
            timeout=10
        )
    
    @patch("requests.get")
    def test_get_jwks_request_failure(self, mock_get):
        """AUTH-UNIT-087: Test JWKS fetching handles request failures."""
        mock_get.side_effect = Exception("Network error")
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        with pytest.raises(ConfigurationError) as exc_info:
            middleware._get_jwks()
        
        assert "Failed to fetch authentication keys from Auth0" in str(exc_info.value)
    
    @patch("requests.get")
    def test_get_jwks_caching(self, mock_get, mock_jwks):
        """AUTH-UNIT-088: Test JWKS caching functionality."""
        mock_response = Mock()
        mock_response.json.return_value = mock_jwks
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        # First call
        result1 = middleware._get_jwks()
        # Second call should use cache
        result2 = middleware._get_jwks()
        
        assert result1 == result2
        # Should only call requests.get once due to caching
        assert mock_get.call_count == 1


class TestSigningKeyExtraction:
    """Test JWT signing key extraction."""
    
    @patch("shared_auth.middleware.Auth0Middleware._get_jwks")
    def test_get_signing_key_success(self, mock_get_jwks, mock_jwks, rsa_private_key):
        """AUTH-UNIT-089: Test successful signing key extraction."""
        mock_get_jwks.return_value = mock_jwks
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        # Create a token with the test key ID
        import jwt
        token = jwt.encode(
            {"test": "payload"}, 
            rsa_private_key, 
            algorithm="RS256",
            headers={"kid": "test-key-id"}
        )
        
        with patch("jwt.PyJWK") as mock_pyjwk:
            mock_key_obj = Mock()
            mock_key_obj.key = "mock-key"
            mock_pyjwk.return_value = mock_key_obj
            
            result = middleware._get_signing_key(token)
            
            assert result == "mock-key"
            mock_pyjwk.assert_called_once()
    
    def test_get_signing_key_invalid_token(self):
        """AUTH-UNIT-090: Test signing key extraction with invalid token."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        with pytest.raises(InvalidTokenError) as exc_info:
            middleware._get_signing_key("invalid-token")
        
        assert "Invalid token format" in str(exc_info.value)
    
    def test_get_signing_key_missing_kid(self, rsa_private_key):
        """AUTH-UNIT-091: Test signing key extraction with missing kid."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        # Create token without kid in header
        import jwt
        token = jwt.encode(
            {"test": "payload"}, 
            rsa_private_key, 
            algorithm="RS256"
        )
        
        with pytest.raises(InvalidTokenError) as exc_info:
            middleware._get_signing_key(token)
        
        assert "Token header missing 'kid' claim" in str(exc_info.value)
    
    @patch("shared_auth.middleware.Auth0Middleware._get_jwks")
    def test_get_signing_key_kid_not_found(self, mock_get_jwks, mock_jwks, rsa_private_key):
        """AUTH-UNIT-092: Test signing key extraction with unknown kid."""
        mock_get_jwks.return_value = mock_jwks
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        # Create token with unknown kid
        import jwt
        token = jwt.encode(
            {"test": "payload"}, 
            rsa_private_key, 
            algorithm="RS256",
            headers={"kid": "unknown-key-id"}
        )
        
        with pytest.raises(InvalidTokenError) as exc_info:
            middleware._get_signing_key(token)
        
        assert "Unable to find signing key with kid: unknown-key-id" in str(exc_info.value)


class TestJWTTokenVerification:
    """Test JWT token verification."""
    
    @patch("shared_auth.middleware.Auth0Middleware._get_signing_key")
    @patch("jwt.decode")
    def test_verify_jwt_token_success(self, mock_jwt_decode, mock_get_signing_key, valid_jwt_payload):
        """AUTH-UNIT-093: Test successful JWT token verification."""
        mock_get_signing_key.return_value = "mock-key"
        mock_jwt_decode.return_value = valid_jwt_payload
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        result = middleware._verify_jwt_token("valid-token")
        
        assert result == valid_jwt_payload
        mock_jwt_decode.assert_called_once_with(
            "valid-token",
            "mock-key",
            algorithms=["RS256"],
            audience="https://test-api.example.com",
            issuer="https://test.auth0.com/"
        )
    
    @patch("shared_auth.middleware.Auth0Middleware._get_signing_key")
    @patch("jwt.decode")
    def test_verify_jwt_token_expired(self, mock_jwt_decode, mock_get_signing_key):
        """AUTH-UNIT-094: Test JWT token verification with expired token."""
        mock_get_signing_key.return_value = "mock-key"
        mock_jwt_decode.side_effect = __import__("jwt").ExpiredSignatureError()
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        with pytest.raises(ExpiredTokenError) as exc_info:
            middleware._verify_jwt_token("expired-token")
        
        assert "Token has expired" in str(exc_info.value)
    
    @patch("shared_auth.middleware.Auth0Middleware._get_signing_key")
    @patch("jwt.decode")
    def test_verify_jwt_token_invalid_audience(self, mock_jwt_decode, mock_get_signing_key):
        """AUTH-UNIT-095: Test JWT token verification with invalid audience."""
        mock_get_signing_key.return_value = "mock-key"
        mock_jwt_decode.side_effect = __import__("jwt").InvalidAudienceError()
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        with pytest.raises(InvalidTokenError) as exc_info:
            middleware._verify_jwt_token("invalid-audience-token")
        
        assert "Invalid token audience" in str(exc_info.value)
    
    @patch("shared_auth.middleware.Auth0Middleware._get_signing_key")
    @patch("jwt.decode")
    def test_verify_jwt_token_missing_claim(self, mock_jwt_decode, mock_get_signing_key):
        """AUTH-UNIT-096: Test JWT token verification with missing required claim."""
        mock_get_signing_key.return_value = "mock-key"
        mock_jwt_decode.side_effect = __import__("jwt").MissingRequiredClaimError("sub")
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        with pytest.raises(MissingClaimError) as exc_info:
            middleware._verify_jwt_token("missing-claim-token")
        
        assert exc_info.value.claim_name == "sub"


class TestUserExtractionFromPayload:
    """Test user extraction from JWT payload."""
    
    def test_extract_user_from_payload_success(self, valid_jwt_payload):
        """AUTH-UNIT-097: Test successful user extraction from JWT payload."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        user = middleware._extract_user_from_payload(valid_jwt_payload)
        
        assert isinstance(user, AuthUser)
        assert user.email == "test@example.com"
        assert user.auth0_subject == "auth0|test-user-123"
        assert user.email_verified is True
        assert user.roles == ["member"]
        assert user.organization_id == "org-456"
        assert "read:documents" in user.scopes
        assert "write:documents" in user.scopes
    
    def test_extract_user_missing_sub(self):
        """AUTH-UNIT-098: Test user extraction fails with missing sub claim."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        payload = {"email": "test@example.com"}
        
        with pytest.raises(MissingClaimError) as exc_info:
            middleware._extract_user_from_payload(payload)
        
        assert exc_info.value.claim_name == "sub"
    
    def test_extract_user_missing_email(self):
        """AUTH-UNIT-099: Test user extraction fails with missing email claim."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        payload = {"sub": "auth0|test-user-123"}
        
        with pytest.raises(MissingClaimError) as exc_info:
            middleware._extract_user_from_payload(payload)
        
        assert exc_info.value.claim_name == "email"
    
    def test_extract_user_with_custom_role_claims(self):
        """AUTH-UNIT-100: Test user extraction with custom role claims."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        payload = {
            "sub": "auth0|test-user-123",
            "email": "test@example.com",
            "https://resumematch.com/roles": ["admin", "member"]
        }
        
        user = middleware._extract_user_from_payload(payload)
        
        assert user.roles == ["admin", "member"]
    
    def test_extract_user_with_string_role(self):
        """AUTH-UNIT-101: Test user extraction converts string role to list."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        payload = {
            "sub": "auth0|test-user-123",
            "email": "test@example.com",
            "roles": "admin"  # String instead of list
        }
        
        user = middleware._extract_user_from_payload(payload)
        
        assert user.roles == ["admin"]


class TestTestTokenHandling:
    """Test handling of test tokens."""
    
    def test_handle_local_test_token(self):
        """AUTH-UNIT-102: Test handling of local test token."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        with patch.dict(os.environ, {"LOCAL_TEST_TOKEN": "local-test-123"}):
            user = middleware._handle_test_tokens("local-test-123")
            
            assert user is not None
            assert isinstance(user, AuthUser)
            assert user.email == "test@resumematch.local"
            assert "member" in user.roles
    
    def test_handle_mock_test_token_with_user_id(self):
        """AUTH-UNIT-103: Test handling of mock test token with user ID."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        user = middleware._handle_test_tokens("mock-test-user-456")
        
        assert user is not None
        assert isinstance(user, AuthUser)
        assert "test-user-456@example.com" in user.email
        assert "member" in user.roles
    
    def test_handle_legacy_mock_token(self):
        """AUTH-UNIT-104: Test handling of legacy mock token."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        user = middleware._handle_test_tokens("mock-legacy-token")
        
        assert user is not None
        assert isinstance(user, AuthUser)
        assert user.email == "mock@test.local"
        assert "member" in user.roles
    
    def test_handle_test_tokens_production_env(self):
        """AUTH-UNIT-105: Test test tokens are ignored in production."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        with patch.dict(os.environ, {"FASTAPI_ENV": "production"}):
            user = middleware._handle_test_tokens("mock-test-user-123")
            
            assert user is None
    
    def test_handle_test_tokens_invalid_format(self):
        """AUTH-UNIT-106: Test invalid test token format returns None."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        user = middleware._handle_test_tokens("invalid-token-format")
        
        assert user is None


class TestRequestTokenVerification:
    """Test token verification from requests."""
    
    @patch("shared_auth.middleware.Auth0Middleware._verify_jwt_token")
    @patch("shared_auth.middleware.Auth0Middleware._extract_user_from_payload")
    def test_verify_token_from_request_success(self, mock_extract_user, mock_verify_token, mock_auth_user):
        """AUTH-UNIT-107: Test successful token verification from request."""
        mock_verify_token.return_value = {"sub": "test", "email": "test@example.com"}
        mock_extract_user.return_value = mock_auth_user
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        # Mock request with authorization header
        request = Mock()
        request.headers = {"authorization": "Bearer valid-token"}
        
        result = middleware.verify_token_from_request(request)
        
        assert result == mock_auth_user
        mock_verify_token.assert_called_once_with("valid-token")
        mock_extract_user.assert_called_once()
    
    def test_verify_token_from_request_missing_header(self):
        """AUTH-UNIT-108: Test token verification fails with missing auth header."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        request = Mock()
        request.headers = {}
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            middleware.verify_token_from_request(request)
        
        assert exc_info.value.status_code == 401
    
    def test_verify_token_from_request_invalid_header_format(self):
        """AUTH-UNIT-109: Test token verification fails with invalid header format."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        request = Mock()
        request.headers = {"authorization": "Invalid token-format"}
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            middleware.verify_token_from_request(request)
        
        assert exc_info.value.status_code == 401
    
    @patch("shared_auth.middleware.Auth0Middleware._handle_test_tokens")
    def test_verify_token_from_request_test_token(self, mock_handle_test, mock_auth_user):
        """AUTH-UNIT-110: Test token verification with test token."""
        mock_handle_test.return_value = mock_auth_user
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        request = Mock()
        request.headers = {"authorization": "Bearer mock-test-user-123"}
        
        result = middleware.verify_token_from_request(request)
        
        assert result == mock_auth_user
        mock_handle_test.assert_called_once_with("mock-test-user-123")


class TestCredentialsTokenVerification:
    """Test token verification from credentials."""
    
    @patch("shared_auth.middleware.Auth0Middleware._verify_jwt_token")
    @patch("shared_auth.middleware.Auth0Middleware._extract_user_from_payload")
    def test_verify_token_from_credentials_success(self, mock_extract_user, mock_verify_token, mock_auth_user):
        """AUTH-UNIT-111: Test successful token verification from credentials."""
        mock_verify_token.return_value = {"sub": "test", "email": "test@example.com"}
        mock_extract_user.return_value = mock_auth_user
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        credentials = Mock()
        credentials.credentials = "valid-token"
        
        result = middleware.verify_token_from_credentials(credentials)
        
        assert result == mock_auth_user
        mock_verify_token.assert_called_once_with("valid-token")
        mock_extract_user.assert_called_once()
    
    def test_verify_token_from_credentials_none(self):
        """AUTH-UNIT-112: Test token verification fails with None credentials."""
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            middleware.verify_token_from_credentials(None)
        
        assert exc_info.value.status_code == 401
    
    @patch("shared_auth.middleware.Auth0Middleware._handle_test_tokens")
    def test_verify_token_from_credentials_test_token(self, mock_handle_test, mock_auth_user):
        """AUTH-UNIT-113: Test token verification from credentials with test token."""
        mock_handle_test.return_value = mock_auth_user
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        credentials = Mock()
        credentials.credentials = "mock-test-user-123"
        
        result = middleware.verify_token_from_credentials(credentials)
        
        assert result == mock_auth_user
        mock_handle_test.assert_called_once_with("mock-test-user-123")


class TestErrorHandling:
    """Test error handling in middleware."""
    
    @patch("shared_auth.middleware.Auth0Middleware._verify_jwt_token")
    def test_configuration_error_handling(self, mock_verify_token):
        """AUTH-UNIT-114: Test configuration error handling."""
        mock_verify_token.side_effect = ConfigurationError("Config error")
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        request = Mock()
        request.headers = {"authorization": "Bearer token"}
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            middleware.verify_token_from_request(request)
        
        assert exc_info.value.status_code == 500
    
    @patch("shared_auth.middleware.Auth0Middleware._verify_jwt_token")
    def test_unexpected_error_handling(self, mock_verify_token):
        """AUTH-UNIT-115: Test unexpected error handling."""
        mock_verify_token.side_effect = Exception("Unexpected error")
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        request = Mock()
        request.headers = {"authorization": "Bearer token"}
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            middleware.verify_token_from_request(request)
        
        assert exc_info.value.status_code == 500
