"""
Contract tests for API Gateway to Internal Service authentication flow.

These tests validate the core microservice authentication pattern:
1. API Gateway validates JWT tokens
2. Extracts user context
3. Passes user info to internal services via headers
4. Internal services trust the headers and reconstruct user context

Critical for:
- Architectural validation of microservice pattern
- Integration point contracts
- Production deployment confidence
- Service communication reliability
"""

import pytest
from unittest.mock import Mock, patch

from shared_auth.middleware import Auth0Middleware
from shared_auth.dependencies import get_user_from_headers
from shared_auth.models import AuthUser
from shared_auth.exceptions import AuthenticationError
from tests.conftest import create_valid_jwt_token, create_test_user


@pytest.mark.contract
class TestAPIGatewayToInternalServiceContract:
    """Test complete auth flow from API Gateway to Internal Service."""
    
    @pytest.mark.asyncio
    async def test_complete_auth_flow_success(self, mock_auth_gateway):
        """CONTRACT-001: Test successful end-to-end auth flow."""
        # 1. Create valid JWT token (simulates client request)
        jwt_token = create_valid_jwt_token(
            user_id="test-user-123",
            org_id="org-456",
            roles=["member", "editor"]
        )
        
        # 2. Simulate API Gateway processing
        with patch.object(mock_auth_gateway.middleware, '_verify_jwt_token') as mock_verify:
            # Mock successful JWT verification
            mock_verify.return_value = {
                "sub": "auth0|test-user-123",
                "email": "test-user-123@example.com",
                "organization_id": "org-456",
                "roles": ["member", "editor"],
                "scope": "read:documents write:documents"
            }
            
            # Process request through gateway
            headers = await mock_auth_gateway.process_request(jwt_token)
        
        # 3. Verify gateway creates correct headers
        assert headers["X-User-ID"] is not None
        assert headers["X-User-Email"] == "test-user-123@example.com"
        assert headers["X-Organization-ID"] == "org-456"
        assert "member" in headers["X-User-Roles"]
        assert "editor" in headers["X-User-Roles"]
        assert "read:documents" in headers["X-User-Scopes"]
        
        # 4. Simulate internal service receiving headers
        reconstructed_user = get_user_from_headers(headers)
        
        # 5. Verify the round-trip works perfectly
        assert reconstructed_user.email == "test-user-123@example.com"
        assert reconstructed_user.organization_id == "org-456"
        assert "member" in reconstructed_user.roles
        assert "editor" in reconstructed_user.roles
        assert "read:documents" in reconstructed_user.scopes
        assert "write:documents" in reconstructed_user.scopes
    
    @pytest.mark.asyncio
    async def test_gateway_jwt_validation_failure(self, mock_auth_gateway):
        """CONTRACT-002: Test gateway handles invalid JWT tokens."""
        # 1. Create invalid JWT token
        invalid_token = "invalid.jwt.token"
        
        # 2. Simulate API Gateway processing invalid token
        with patch.object(mock_auth_gateway.middleware, '_verify_jwt_token') as mock_verify:
            from shared_auth.exceptions import InvalidTokenError
            mock_verify.side_effect = InvalidTokenError("Invalid token signature")
            
            # Test: Gateway should reject invalid token
            with pytest.raises(Exception) as exc_info:
                await mock_auth_gateway.process_request(invalid_token)
            
            # Verify: Proper error handling
            assert "Invalid token" in str(exc_info.value) or "401" in str(exc_info.value)
    
    def test_internal_service_header_processing(self):
        """CONTRACT-003: Test internal service processes gateway headers correctly."""
        # 1. Simulate headers from API Gateway
        gateway_headers = {
            "X-User-ID": "123e4567-e89b-12d3-a456-426614174000",
            "X-User-Email": "alice@company.com",
            "X-Organization-ID": "org-789",
            "X-User-Roles": "admin,member,editor",
            "X-User-Scopes": "read:documents write:documents delete:documents"
        }
        
        # 2. Internal service reconstructs user context
        user = get_user_from_headers(gateway_headers)
        
        # 3. Verify all user attributes are correctly reconstructed
        assert user.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert user.email == "alice@company.com"
        assert user.organization_id == "org-789"
        assert set(user.roles) == {"admin", "member", "editor"}
        assert set(user.scopes) == {"read:documents", "write:documents", "delete:documents"}
    
    def test_internal_service_missing_headers(self):
        """CONTRACT-004: Test internal service handles missing headers gracefully."""
        # 1. Simulate incomplete headers from gateway
        incomplete_headers = {
            "X-User-Email": "bob@company.com",
            # Missing X-User-ID, X-Organization-ID, etc.
        }
        
        # 2. Test: Internal service should return None for missing headers
        result = get_user_from_headers(incomplete_headers)
        
        # 3. Verify: None returned for incomplete headers
        assert result is None
    
    @pytest.mark.asyncio
    async def test_multi_role_user_flow(self, mock_auth_gateway):
        """CONTRACT-005: Test flow with user having multiple roles."""
        # 1. Create JWT for user with multiple roles
        jwt_token = create_valid_jwt_token(
            user_id="multi-role-user",
            org_id="org-enterprise",
            roles=["member", "admin", "billing_manager", "support"]
        )
        
        # 2. Process through gateway
        with patch.object(mock_auth_gateway.middleware, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "auth0|multi-role-user",
                "email": "multi-role-user@example.com",
                "organization_id": "org-enterprise",
                "roles": ["member", "admin", "billing_manager", "support"],
                "scope": "read:documents write:documents admin:users billing:manage"
            }
            
            headers = await mock_auth_gateway.process_request(jwt_token)
        
        # 3. Verify all roles are preserved in headers
        roles_header = headers["X-User-Roles"]
        assert "member" in roles_header
        assert "admin" in roles_header
        assert "billing_manager" in roles_header
        assert "support" in roles_header
        
        # 4. Verify internal service reconstructs all roles
        user = get_user_from_headers(headers)
        assert len(user.roles) == 4
        assert user.has_role("admin")
        assert user.has_role("billing_manager")
        assert user.has_scope("admin:users")
        assert user.has_scope("billing:manage")
    
    def test_header_format_consistency(self):
        """CONTRACT-006: Test header format consistency between services."""
        # 1. Define expected header format contract
        expected_headers = [
            "X-User-ID",
            "X-User-Email", 
            "X-Organization-ID",
            "X-User-Roles",
            "X-User-Scopes"
        ]
        
        # 2. Create test user
        test_user = create_test_user(
            user_id="format-test-user",
            org_id="org-format-test",
            roles=["member", "tester"]
        )
        
        # 3. Simulate gateway creating headers
        gateway_headers = {
            "X-User-ID": test_user.user_id,
            "X-User-Email": test_user.email,
            "X-Organization-ID": test_user.organization_id,
            "X-User-Roles": ",".join(test_user.roles),
            "X-User-Scopes": " ".join(test_user.scopes)
        }
        
        # 4. Verify all expected headers are present
        for header in expected_headers:
            assert header in gateway_headers, f"Missing required header: {header}"
            assert gateway_headers[header] is not None, f"Header {header} is None"
        
        # 5. Verify internal service can parse all headers
        reconstructed_user = get_user_from_headers(gateway_headers)
        assert reconstructed_user.user_id == test_user.user_id
        assert reconstructed_user.email == test_user.email
        assert reconstructed_user.organization_id == test_user.organization_id
    
    @pytest.mark.asyncio
    async def test_performance_contract(self, mock_auth_gateway):
        """CONTRACT-007: Test performance characteristics of auth flow."""
        import time
        
        # 1. Create JWT token
        jwt_token = create_valid_jwt_token()
        
        # 2. Mock JWT verification to be fast
        with patch.object(mock_auth_gateway.middleware, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "auth0|perf-test-user",
                "email": "perf-test@example.com",
                "organization_id": "org-perf",
                "roles": ["member"],
                "scope": "read:documents"
            }
            
            # 3. Measure gateway processing time
            start_time = time.time()
            headers = await mock_auth_gateway.process_request(jwt_token)
            gateway_time = time.time() - start_time
            
            # 4. Measure internal service processing time
            start_time = time.time()
            user = get_user_from_headers(headers)
            service_time = time.time() - start_time
        
        # 5. Verify performance contract (should be very fast)
        assert gateway_time < 0.1, f"Gateway processing too slow: {gateway_time}s"
        assert service_time < 0.01, f"Service processing too slow: {service_time}s"
        assert user is not None, "User reconstruction failed"


@pytest.mark.contract
class TestServiceCommunicationContract:
    """Test the communication contract between gateway and services."""
    
    def test_header_encoding_contract(self):
        """CONTRACT-008: Test header encoding handles special characters."""
        # 1. Create user with special characters
        special_user = create_test_user(
            user_id="user-with-special-chars",
            email="test+user@company-name.co.uk",
            org_id="org-special-123"
        )
        
        # 2. Create headers (simulate gateway)
        headers = {
            "X-User-ID": special_user.user_id,
            "X-User-Email": special_user.email,
            "X-Organization-ID": special_user.organization_id,
            "X-User-Roles": ",".join(special_user.roles),
            "X-User-Scopes": " ".join(special_user.scopes)
        }
        
        # 3. Verify internal service handles special characters
        reconstructed_user = get_user_from_headers(headers)
        assert reconstructed_user.email == "test+user@company-name.co.uk"
        assert reconstructed_user.organization_id == "org-special-123"
    
    def test_empty_values_contract(self):
        """CONTRACT-009: Test contract handles empty/null values."""
        # 1. Create headers with some empty values
        headers_with_empties = {
            "X-User-ID": "valid-user-id",
            "X-User-Email": "user@example.com",
            "X-Organization-ID": "",  # Empty org
            "X-User-Roles": "",       # No roles
            "X-User-Scopes": "read:documents"
        }
        
        # 2. Internal service should handle gracefully
        user = get_user_from_headers(headers_with_empties)
        
        # 3. Verify handling of empty values
        assert user.user_id == "valid-user-id"
        assert user.email == "user@example.com"
        assert user.organization_id is None or user.organization_id == ""
        assert len(user.roles) == 0
        assert "read:documents" in user.scopes
    
    def test_backwards_compatibility_contract(self):
        """CONTRACT-010: Test backwards compatibility with header changes."""
        # This test ensures that if we add new headers in the future,
        # existing services continue to work
        
        # 1. Simulate old-style headers (minimal set)
        legacy_headers = {
            "X-User-ID": "legacy-user-123",
            "X-User-Email": "legacy@example.com",
            # Missing newer headers like X-Organization-ID
        }
        
        # 2. Service should still work with minimal headers
        user = get_user_from_headers(legacy_headers)
        
        # 3. Verify basic functionality works
        assert user.user_id == "legacy-user-123"
        assert user.email == "legacy@example.com"
        # Organization and roles may be None/empty - that's acceptable
