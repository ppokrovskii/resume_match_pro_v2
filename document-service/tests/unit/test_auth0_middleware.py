"""
Unit tests for Auth0 middleware and authentication
Following TDD approach as per project requirements
"""

import os
import pytest
import jwt
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from middleware.auth0_middleware import (
    verify_token,
    get_current_user_id,
    get_current_user_email,
    require_scope,
    get_auth0_config,
    get_jwks,
    Auth0Middleware,
    get_user_info
)


class TestAuth0Configuration:
    """Test Auth0 configuration management"""
    
    def test_get_auth0_config_with_environment_variables(self):
        """Test Auth0 config retrieval with environment variables"""
        with patch.dict(os.environ, {
            'AUTH0_DOMAIN': 'test.auth0.com',
            'AUTH0_API_IDENTIFIER': 'https://api.test.com',
            'AUTH0_ALGORITHMS': 'RS256'
        }):
            config = get_auth0_config()
            
            assert config['domain'] == 'test.auth0.com'
            assert config['api_identifier'] == 'https://api.test.com'
            assert config['algorithms'] == ['RS256']
    
    def test_get_auth0_config_with_defaults(self):
        """Test Auth0 config with default values"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_auth0_config()
            
            assert config['domain'] is None
            assert config['api_identifier'] is None
            assert config['algorithms'] == ['RS256']
    
    def test_get_auth0_config_with_audience_fallback(self):
        """Test Auth0 config with AUTH0_AUDIENCE fallback"""
        with patch.dict(os.environ, {
            'AUTH0_AUDIENCE': 'https://api.fallback.com'
        }):
            config = get_auth0_config()
            
            assert config['api_identifier'] == 'https://api.fallback.com'


class TestJWKSRetrieval:
    """Test JWKS (JSON Web Key Set) retrieval"""
    
    @patch('middleware.auth0_middleware.requests.get')
    def test_get_jwks_success(self, mock_get):
        """Test successful JWKS retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "test-key-id",
                    "use": "sig",
                    "n": "test-n-value",
                    "e": "AQAB"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'AUTH0_DOMAIN': 'test.auth0.com'}):
            jwks = get_jwks()
            
            assert "keys" in jwks
            assert len(jwks["keys"]) == 1
            assert jwks["keys"][0]["kid"] == "test-key-id"
            mock_get.assert_called_once_with(
                "https://test.auth0.com/.well-known/jwks.json",
                timeout=10
            )
    
    def test_get_jwks_missing_domain(self):
        """Test JWKS retrieval with missing domain"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="AUTH0_DOMAIN environment variable is required"):
                get_jwks()
    
    @patch('middleware.auth0_middleware.requests.get')
    def test_get_jwks_request_failure(self, mock_get):
        """Test JWKS retrieval with request failure"""
        mock_get.side_effect = Exception("Network error")
        
        with patch.dict(os.environ, {'AUTH0_DOMAIN': 'test.auth0.com'}):
            with pytest.raises(HTTPException) as exc_info:
                get_jwks()
            
            assert exc_info.value.status_code == 500
            assert "Failed to fetch authentication keys" in str(exc_info.value.detail)


class TestTokenVerification:
    """Test JWT token verification"""
    
    def test_verify_token_missing_credentials(self):
        """Test token verification with missing credentials"""
        with pytest.raises(HTTPException) as exc_info:
            verify_token(None)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "AUTHENTICATION_REQUIRED"
    
    def test_verify_token_local_test_token(self):
        """Test verification with local test token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-local-token"
        )
        
        with patch.dict(os.environ, {
            'LOCAL_TEST_TOKEN': 'test-local-token',
            'AUTH0_API_IDENTIFIER': 'https://api.test.com'
        }):
            result = verify_token(credentials)
            
            assert result["sub"] == "test-user-123"
            assert result["email"] == "test@resumematch.local"
            assert "read:documents" in result["scope"]
    
    def test_verify_token_mock_token(self):
        """Test verification with mock token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="mock-test-token"
        )
        
        with patch.dict(os.environ, {'AUTH0_API_IDENTIFIER': 'https://api.test.com'}):
            result = verify_token(credentials)
            
            assert result["sub"] == "123e4567-e89b-12d3-a456-426614174000"
            assert result["email"] == "mock@test.local"
            assert "read:documents" in result["scope"]
    
    def test_verify_token_invalid_format(self):
        """Test token verification with invalid token format"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.format"
        )
        
        with patch.dict(os.environ, {
            'AUTH0_DOMAIN': 'test.auth0.com',
            'AUTH0_API_IDENTIFIER': 'https://api.test.com'
        }):
            with patch('middleware.auth0_middleware.jwt.get_unverified_header') as mock_header:
                mock_header.side_effect = jwt.DecodeError("Invalid token")
                
                with pytest.raises(HTTPException) as exc_info:
                    verify_token(credentials)
                
                assert exc_info.value.status_code == 401
                assert exc_info.value.detail["error"]["code"] == "INVALID_TOKEN_FORMAT"
    
    @patch('middleware.auth0_middleware.get_jwks')
    @patch('middleware.auth0_middleware.jwt.get_unverified_header')
    @patch('middleware.auth0_middleware.jwt.decode')
    def test_verify_token_success(self, mock_decode, mock_header, mock_jwks):
        """Test successful token verification"""
        # Mock token header
        mock_header.return_value = {"kid": "test-key-id", "alg": "RS256"}
        
        # Mock JWKS
        mock_jwks.return_value = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "test-key-id",
                    "use": "sig",
                    "n": "test-n-value",
                    "e": "AQAB"
                }
            ]
        }
        
        # Mock JWT decode
        mock_payload = {
            "sub": "auth0|user123",
            "email": "user@test.com",
            "scope": "read:documents write:documents",
            "aud": "https://api.test.com",
            "iss": "https://test.auth0.com/",
            "exp": 1234567890
        }
        mock_decode.return_value = mock_payload
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )
        
        with patch.dict(os.environ, {
            'AUTH0_DOMAIN': 'test.auth0.com',
            'AUTH0_API_IDENTIFIER': 'https://api.test.com'
        }):
            with patch('jwt.PyJWK') as mock_pyjwk:
                mock_key = Mock()
                mock_pyjwk.return_value.key = mock_key
                
                result = verify_token(credentials)
                
                assert result == mock_payload
                mock_decode.assert_called_once()
    
    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="expired.jwt.token"
        )
        
        with patch.dict(os.environ, {
            'AUTH0_DOMAIN': 'test.auth0.com',
            'AUTH0_API_IDENTIFIER': 'https://api.test.com'
        }):
            with patch('middleware.auth0_middleware.jwt.get_unverified_header'):
                with patch('middleware.auth0_middleware.get_jwks'):
                    with patch('middleware.auth0_middleware.jwt.decode') as mock_decode:
                        mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")
                        
                        with pytest.raises(HTTPException) as exc_info:
                            verify_token(credentials)
                        
                        assert exc_info.value.status_code == 401
                        assert exc_info.value.detail["error"]["code"] == "TOKEN_EXPIRED"
    
    def test_verify_token_invalid_claims(self):
        """Test token verification with invalid claims"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.claims.token"
        )
        
        with patch.dict(os.environ, {
            'AUTH0_DOMAIN': 'test.auth0.com',
            'AUTH0_API_IDENTIFIER': 'https://api.test.com'
        }):
            with patch('middleware.auth0_middleware.jwt.get_unverified_header'):
                with patch('middleware.auth0_middleware.get_jwks'):
                    with patch('middleware.auth0_middleware.jwt.decode') as mock_decode:
                        mock_decode.side_effect = jwt.InvalidAudienceError("Invalid audience")
                        
                        with pytest.raises(HTTPException) as exc_info:
                            verify_token(credentials)
                        
                        assert exc_info.value.status_code == 401
                        assert exc_info.value.detail["error"]["code"] == "INVALID_TOKEN_CLAIMS"


class TestUserExtraction:
    """Test user information extraction from tokens"""
    
    @patch('middleware.auth0_middleware.verify_token')
    @patch('utils.auth_utils.auth0_subject_to_uuid')
    def test_get_current_user_id_success(self, mock_auth0_to_uuid, mock_verify):
        """Test successful user ID extraction"""
        mock_verify.return_value = {"sub": "auth0|user123"}
        mock_auth0_to_uuid.return_value = "123e4567-e89b-12d3-a456-426614174000"
        
        result = get_current_user_id(mock_verify.return_value)
        
        assert result == "123e4567-e89b-12d3-a456-426614174000"
        mock_auth0_to_uuid.assert_called_once_with("auth0|user123")
    
    @patch('middleware.auth0_middleware.verify_token')
    def test_get_current_user_id_missing_subject(self, mock_verify):
        """Test user ID extraction with missing subject"""
        mock_verify.return_value = {}
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(mock_verify.return_value)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "MISSING_USER_ID"
    
    @patch('middleware.auth0_middleware.verify_token')
    @patch('utils.auth_utils.auth0_subject_to_uuid')
    def test_get_current_user_id_conversion_failure(self, mock_auth0_to_uuid, mock_verify):
        """Test user ID extraction with conversion failure"""
        mock_verify.return_value = {"sub": "auth0|user123"}
        mock_auth0_to_uuid.side_effect = Exception("Conversion failed")
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(mock_verify.return_value)
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["error"]["code"] == "USER_ID_CONVERSION_FAILED"
    
    @patch('middleware.auth0_middleware.verify_token')
    def test_get_current_user_email_success(self, mock_verify):
        """Test successful email extraction"""
        mock_verify.return_value = {"email": "user@test.com"}
        
        result = get_current_user_email(mock_verify.return_value)
        
        assert result == "user@test.com"
    
    @patch('middleware.auth0_middleware.verify_token')
    def test_get_current_user_email_missing(self, mock_verify):
        """Test email extraction with missing email"""
        mock_verify.return_value = {}
        
        result = get_current_user_email(mock_verify.return_value)
        
        assert result is None


class TestScopeRequirements:
    """Test scope-based authorization"""
    
    def test_require_scope_success(self):
        """Test successful scope requirement check"""
        token_payload = {"scope": "read:documents write:documents delete:documents"}
        
        check_scope = require_scope("read:documents")
        result = check_scope(token_payload)
        
        assert result == token_payload
    
    def test_require_scope_missing_scope(self):
        """Test scope requirement with missing scope"""
        token_payload = {"scope": "read:documents"}
        
        check_scope = require_scope("delete:documents")
        
        with pytest.raises(HTTPException) as exc_info:
            check_scope(token_payload)
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"]["code"] == "INSUFFICIENT_SCOPE"
    
    def test_require_scope_no_scopes(self):
        """Test scope requirement with no scopes in token"""
        token_payload = {}
        
        check_scope = require_scope("read:documents")
        
        with pytest.raises(HTTPException) as exc_info:
            check_scope(token_payload)
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"]["code"] == "INSUFFICIENT_SCOPE"


class TestAuth0Middleware:
    """Test Auth0 middleware initialization"""
    
    def test_middleware_initialization_success(self):
        """Test successful middleware initialization"""
        mock_app = Mock()
        
        with patch.dict(os.environ, {
            'AUTH0_DOMAIN': 'test.auth0.com',
            'AUTH0_API_IDENTIFIER': 'https://api.test.com'
        }):
            middleware = Auth0Middleware(mock_app)
            
            assert middleware.app == mock_app
    
    def test_middleware_initialization_missing_config(self, caplog):
        """Test middleware initialization with missing configuration"""
        mock_app = Mock()
        
        with patch.dict(os.environ, {}, clear=True):
            middleware = Auth0Middleware(mock_app)
            
            assert middleware.app == mock_app
            assert "AUTH0_DOMAIN not configured" in caplog.text
            assert "AUTH0_API_IDENTIFIER not configured" in caplog.text


class TestUserInfo:
    """Test user information helper"""
    
    @patch('middleware.auth0_middleware.verify_token')
    @patch('utils.auth_utils.auth0_subject_to_uuid')
    def test_get_user_info_success(self, mock_auth0_to_uuid, mock_verify):
        """Test successful user info retrieval"""
        mock_verify.return_value = {
            "sub": "auth0|user123",
            "email": "user@test.com",
            "email_verified": True,
            "scope": "read:documents write:documents",
            "aud": "https://api.test.com",
            "iss": "https://test.auth0.com/"
        }
        mock_auth0_to_uuid.return_value = "123e4567-e89b-12d3-a456-426614174000"
        
        result = get_user_info(mock_verify.return_value)
        
        assert result["user_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert result["auth0_subject"] == "auth0|user123"
        assert result["email"] == "user@test.com"
        assert result["email_verified"] is True
        assert result["scopes"] == ["read:documents", "write:documents"]
        assert result["audience"] == "https://api.test.com"
        assert result["issuer"] == "https://test.auth0.com/"
    
    @patch('middleware.auth0_middleware.verify_token')
    def test_get_user_info_minimal_token(self, mock_verify):
        """Test user info with minimal token data"""
        mock_verify.return_value = {"sub": ""}
        
        with patch('utils.auth_utils.auth0_subject_to_uuid') as mock_auth0_to_uuid:
            mock_auth0_to_uuid.return_value = ""
            
            result = get_user_info(mock_verify.return_value)
            
            assert result["user_id"] == ""
            assert result["auth0_subject"] == ""
            assert result["email"] is None
            assert result["email_verified"] is False
            assert result["scopes"] == []


# Integration test for the complete auth flow
class TestAuthenticationIntegration:
    """Integration tests for complete authentication flow"""
    
    @patch('middleware.auth0_middleware.get_jwks')
    @patch('middleware.auth0_middleware.jwt.get_unverified_header')
    @patch('middleware.auth0_middleware.jwt.decode')
    @patch('utils.auth_utils.auth0_subject_to_uuid')
    def test_complete_auth_flow(self, mock_auth0_to_uuid, mock_decode, mock_header, mock_jwks):
        """Test complete authentication and authorization flow"""
        # Setup mocks
        mock_header.return_value = {"kid": "test-key-id", "alg": "RS256"}
        mock_jwks.return_value = {
            "keys": [{"kty": "RSA", "kid": "test-key-id", "use": "sig", "n": "test-n", "e": "AQAB"}]
        }
        mock_decode.return_value = {
            "sub": "auth0|user123",
            "email": "user@test.com",
            "scope": "read:documents write:documents delete:documents",
            "aud": "https://api.test.com",
            "iss": "https://test.auth0.com/"
        }
        mock_auth0_to_uuid.return_value = "123e4567-e89b-12d3-a456-426614174000"
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )
        
        with patch.dict(os.environ, {
            'AUTH0_DOMAIN': 'test.auth0.com',
            'AUTH0_API_IDENTIFIER': 'https://api.test.com'
        }):
            with patch('jwt.PyJWK') as mock_pyjwk:
                mock_pyjwk.return_value.key = Mock()
                
                # Verify token
                token_payload = verify_token(credentials)
                assert token_payload["sub"] == "auth0|user123"
                
                # Extract user ID
                user_id = get_current_user_id(token_payload)
                assert user_id == "123e4567-e89b-12d3-a456-426614174000"
                
                # Extract email
                email = get_current_user_email(token_payload)
                assert email == "user@test.com"
                
                # Check scope
                check_read_scope = require_scope("read:documents")
                result = check_read_scope(token_payload)
                assert result == token_payload
                
                # Get user info
                user_info = get_user_info(token_payload)
                assert user_info["user_id"] == "123e4567-e89b-12d3-a456-426614174000"
                assert user_info["email"] == "user@test.com"
                assert "read:documents" in user_info["scopes"]

