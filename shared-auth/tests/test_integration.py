"""
Integration tests for shared-auth package.

Test ID: AUTH-INT-001 to AUTH-INT-006
"""

import pytest
import os
import time
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from shared_auth import Auth0Middleware, AuthUser
from shared_auth.exceptions import InvalidTokenError, ExpiredTokenError


class TestAuth0Integration:
    """Integration tests with Auth0 services."""
    
    @pytest.mark.integration
    @patch("requests.get")
    def test_real_auth0_jwks_fetching(self, mock_get, mock_jwks):
        """AUTH-INT-001: Test real Auth0 JWKS fetching integration."""
        # Mock successful JWKS response
        mock_response = Mock()
        mock_response.json.return_value = mock_jwks
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.resumematch.com"
        )
        
        # Test JWKS fetching
        jwks = middleware._get_jwks()
        
        assert jwks == mock_jwks
        assert len(jwks["keys"]) > 0
        
        # Verify correct URL was called
        expected_url = "https://test.auth0.com/.well-known/jwks.json"
        mock_get.assert_called_with(expected_url, timeout=10)
    
    @pytest.mark.integration
    @patch("requests.get")
    def test_jwks_caching_performance(self, mock_get, mock_jwks):
        """AUTH-INT-002: Test JWKS caching for performance."""
        mock_response = Mock()
        mock_response.json.return_value = mock_jwks
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.resumematch.com"
        )
        
        # First call - should fetch from Auth0
        start_time = time.time()
        jwks1 = middleware._get_jwks()
        first_call_time = time.time() - start_time
        
        # Second call - should use cache
        start_time = time.time()
        jwks2 = middleware._get_jwks()
        second_call_time = time.time() - start_time
        
        # Verify caching worked
        assert jwks1 == jwks2
        assert mock_get.call_count == 1  # Only called once due to caching
        assert second_call_time < first_call_time  # Cache should be faster
    
    @pytest.mark.integration
    def test_jwt_token_validation_flow(self, rsa_private_key, valid_jwt_payload, mock_jwks):
        """AUTH-INT-003: Test complete JWT token validation flow."""
        with patch("requests.get") as mock_get:
            # Mock JWKS response
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Mock PyJWK to return our test key
            with patch("jwt.PyJWK") as mock_pyjwk:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.serialization import load_pem_private_key
                
                # Load the private key and get the public key
                private_key = load_pem_private_key(
                    rsa_private_key.encode(), 
                    password=None
                )
                public_key = private_key.public_key()
                
                mock_key_obj = Mock()
                mock_key_obj.key = public_key
                mock_pyjwk.return_value = mock_key_obj
                
                middleware = Auth0Middleware(
                    domain="test.auth0.com",
                    api_identifier="https://test-api.resumematch.com"
                )
                
                # Create a valid JWT token
                import jwt
                token = jwt.encode(
                    valid_jwt_payload,
                    rsa_private_key,
                    algorithm="RS256",
                    headers={"kid": "test-key-id"}
                )
                
                # Test token validation
                payload = middleware._verify_jwt_token(token)
                
                assert payload["sub"] == valid_jwt_payload["sub"]
                assert payload["email"] == valid_jwt_payload["email"]
                assert payload["aud"] == valid_jwt_payload["aud"]
    
    @pytest.mark.integration
    def test_user_extraction_integration(self, rsa_private_key, valid_jwt_payload, mock_jwks):
        """AUTH-INT-004: Test complete user extraction from JWT."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch("jwt.PyJWK") as mock_pyjwk:
                from cryptography.hazmat.primitives.serialization import load_pem_private_key
                
                private_key = load_pem_private_key(
                    rsa_private_key.encode(), 
                    password=None
                )
                public_key = private_key.public_key()
                
                mock_key_obj = Mock()
                mock_key_obj.key = public_key
                mock_pyjwk.return_value = mock_key_obj
                
                middleware = Auth0Middleware(
                    domain="test.auth0.com",
                    api_identifier="https://test-api.resumematch.com"
                )
                
                # Create and validate token
                import jwt
                token = jwt.encode(
                    valid_jwt_payload,
                    rsa_private_key,
                    algorithm="RS256",
                    headers={"kid": "test-key-id"}
                )
                
                payload = middleware._verify_jwt_token(token)
                user = middleware._extract_user_from_payload(payload)
                
                # Verify user extraction
                assert isinstance(user, AuthUser)
                assert user.email == "test@example.com"
                assert user.auth0_subject == "auth0|test-user-123"
                assert user.organization_id == "org-456"
                assert "member" in user.roles
                assert "read:documents" in user.scopes
                assert "write:documents" in user.scopes


class TestPerformanceRequirements:
    """Test performance requirements."""
    
    @pytest.mark.performance
    @patch("requests.get")
    def test_token_validation_performance(self, mock_get, mock_jwks, rsa_private_key, valid_jwt_payload):
        """AUTH-INT-002: Test token validation performance < 100ms."""
        mock_response = Mock()
        mock_response.json.return_value = mock_jwks
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch("jwt.PyJWK") as mock_pyjwk:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            
            private_key = load_pem_private_key(rsa_private_key.encode(), password=None)
            public_key = private_key.public_key()
            
            mock_key_obj = Mock()
            mock_key_obj.key = public_key
            mock_pyjwk.return_value = mock_key_obj
            
            middleware = Auth0Middleware(
                domain="test.auth0.com",
                api_identifier="https://test-api.resumematch.com"
            )
            
            # Create token
            import jwt
            token = jwt.encode(
                valid_jwt_payload,
                rsa_private_key,
                algorithm="RS256",
                headers={"kid": "test-key-id"}
            )
            
            # Warm up (first call fetches JWKS)
            middleware._verify_jwt_token(token)
            
            # Measure performance of subsequent calls
            start_time = time.time()
            for _ in range(10):
                middleware._verify_jwt_token(token)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 10
            
            # Should be well under 100ms (0.1 seconds)
            assert avg_time < 0.1, f"Token validation took {avg_time:.3f}s, should be < 0.1s"
    
    @pytest.mark.performance
    def test_concurrent_token_validation(self, mock_jwks, rsa_private_key, valid_jwt_payload):
        """AUTH-INT-003: Test concurrent token validation performance."""
        import concurrent.futures
        import threading
        
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch("jwt.PyJWK") as mock_pyjwk:
                from cryptography.hazmat.primitives.serialization import load_pem_private_key
                
                private_key = load_pem_private_key(rsa_private_key.encode(), password=None)
                public_key = private_key.public_key()
                
                mock_key_obj = Mock()
                mock_key_obj.key = public_key
                mock_pyjwk.return_value = mock_key_obj
                
                middleware = Auth0Middleware(
                    domain="test.auth0.com",
                    api_identifier="https://test-api.resumematch.com"
                )
                
                # Create token
                import jwt
                token = jwt.encode(
                    valid_jwt_payload,
                    rsa_private_key,
                    algorithm="RS256",
                    headers={"kid": "test-key-id"}
                )
                
                def validate_token():
                    return middleware._verify_jwt_token(token)
                
                # Test concurrent validation
                start_time = time.time()
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(validate_token) for _ in range(100)]
                    results = [future.result() for future in concurrent.futures.as_completed(futures)]
                end_time = time.time()
                
                # All validations should succeed
                assert len(results) == 100
                for result in results:
                    assert result["sub"] == valid_jwt_payload["sub"]
                
                # Should handle 100 concurrent requests reasonably fast
                total_time = end_time - start_time
                assert total_time < 5.0, f"100 concurrent validations took {total_time:.3f}s, should be < 5s"


class TestSecurityRequirements:
    """Test security requirements."""
    
    @pytest.mark.security
    def test_expired_token_rejection(self, rsa_private_key, expired_jwt_payload, mock_jwks):
        """AUTH-INT-004: Test expired token rejection."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch("jwt.PyJWK") as mock_pyjwk:
                from cryptography.hazmat.primitives.serialization import load_pem_private_key
                
                private_key = load_pem_private_key(rsa_private_key.encode(), password=None)
                public_key = private_key.public_key()
                
                mock_key_obj = Mock()
                mock_key_obj.key = public_key
                mock_pyjwk.return_value = mock_key_obj
                
                middleware = Auth0Middleware(
                    domain="test.auth0.com",
                    api_identifier="https://test-api.resumematch.com"
                )
                
                # Create expired token
                import jwt
                token = jwt.encode(
                    expired_jwt_payload,
                    rsa_private_key,
                    algorithm="RS256",
                    headers={"kid": "test-key-id"}
                )
                
                # Should reject expired token
                with pytest.raises(ExpiredTokenError):
                    middleware._verify_jwt_token(token)
    
    @pytest.mark.security
    def test_invalid_audience_rejection(self, rsa_private_key, invalid_audience_payload, mock_jwks):
        """AUTH-INT-005: Test invalid audience rejection."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch("jwt.PyJWK") as mock_pyjwk:
                from cryptography.hazmat.primitives.serialization import load_pem_private_key
                
                private_key = load_pem_private_key(rsa_private_key.encode(), password=None)
                public_key = private_key.public_key()
                
                mock_key_obj = Mock()
                mock_key_obj.key = public_key
                mock_pyjwk.return_value = mock_key_obj
                
                middleware = Auth0Middleware(
                    domain="test.auth0.com",
                    api_identifier="https://test-api.resumematch.com"
                )
                
                # Create token with wrong audience
                import jwt
                token = jwt.encode(
                    invalid_audience_payload,
                    rsa_private_key,
                    algorithm="RS256",
                    headers={"kid": "test-key-id"}
                )
                
                # Should reject token with wrong audience
                with pytest.raises(InvalidTokenError) as exc_info:
                    middleware._verify_jwt_token(token)
                
                assert "Invalid token audience" in str(exc_info.value)
    
    @pytest.mark.security
    def test_malformed_token_rejection(self, mock_jwks):
        """AUTH-INT-006: Test malformed token rejection."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            middleware = Auth0Middleware(
                domain="test.auth0.com",
                api_identifier="https://test-api.resumematch.com"
            )
            
            malformed_tokens = [
                "not.a.jwt",
                "invalid-token-format",
                "",
                "header.payload",  # Missing signature
                "too.many.parts.here.invalid",
            ]
            
            for token in malformed_tokens:
                with pytest.raises(InvalidTokenError):
                    middleware._verify_jwt_token(token)


class TestUserDataIsolation:
    """Test user data isolation requirements."""
    
    def test_organization_boundary_enforcement(self):
        """AUTH-INT-005: Test organization boundary enforcement."""
        from shared_auth.dependencies import require_organization_access
        
        # User from org-123
        user_org_123 = AuthUser(
            user_id="user-123",
            email="user@org123.com",
            organization_id="org-123"
        )
        
        # User from org-456
        user_org_456 = AuthUser(
            user_id="user-456",
            email="user@org456.com",
            organization_id="org-456"
        )
        
        # Test access to org-123 resources
        require_org_123_access = require_organization_access("org-123")
        
        # User from org-123 should have access
        result = require_org_123_access(user_org_123)
        assert result == user_org_123
        
        # User from org-456 should be denied
        with pytest.raises(Exception) as exc_info:
            require_org_123_access(user_org_456)
        
        assert exc_info.value.status_code == 403
        assert "ORGANIZATION_ACCESS_DENIED" in str(exc_info.value.detail)
    
    def test_user_isolation_via_headers(self):
        """Test user isolation when extracting from headers."""
        from shared_auth.dependencies import get_user_from_headers
        
        # Headers for user 1
        headers_user_1 = {
            "X-User-ID": "user-123",
            "X-User-Email": "user1@example.com",
            "X-Organization-ID": "org-123"
        }
        
        # Headers for user 2
        headers_user_2 = {
            "X-User-ID": "user-456",
            "X-User-Email": "user2@example.com",
            "X-Organization-ID": "org-456"
        }
        
        user_1 = get_user_from_headers(headers_user_1)
        user_2 = get_user_from_headers(headers_user_2)
        
        # Users should be completely isolated
        assert user_1.user_id != user_2.user_id
        assert user_1.email != user_2.email
        assert user_1.organization_id != user_2.organization_id


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.integration
    @patch("shared_auth.dependencies.get_user_from_request_headers")
    async def test_complete_auth_flow_internal_service(self, mock_get_user):
        """Test complete authentication flow for internal service."""
        from shared_auth.dependencies import require_auth, require_organization_member
        
        # Mock user from headers (internal service mode)
        mock_user = AuthUser(
            user_id="user-123",
            email="user@example.com",
            organization_id="org-456",
            roles=["member"],
            scopes=["read:documents", "write:documents"]
        )
        mock_get_user.return_value = mock_user
        
        # Mock request
        request = Mock()
        request.headers = {}
        
        # Test complete flow
        authenticated_user = await require_auth(request)
        org_member = await require_organization_member(authenticated_user)
        
        assert org_member == mock_user
        assert org_member.is_organization_member
    
    @pytest.mark.integration
    def test_package_import_and_usage(self):
        """Test package can be imported and used as intended."""
        # Test main imports work
        from shared_auth import (
            Auth0Middleware,
            AuthUser,
            require_auth,
            require_admin,
            auth0_subject_to_uuid,
        )
        
        # Test middleware can be created
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        assert middleware.domain == "test.auth0.com"
        
        # Test user model works
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            roles=["admin"]
        )
        assert user.is_admin
        
        # Test utility functions work
        uuid_result = auth0_subject_to_uuid("google-oauth2|12345")
        assert len(uuid_result) == 36  # UUID format
