"""
Unit tests for authentication exceptions.

Test ID: AUTH-UNIT-025 to AUTH-UNIT-040
"""

import pytest
from shared_auth.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    ExpiredTokenError,
    InsufficientScopeError,
    InsufficientRoleError,
    MissingClaimError,
    OrganizationAccessError,
    ConfigurationError,
)


class TestAuthenticationError:
    """Test base AuthenticationError functionality."""
    
    def test_authentication_error_creation_minimal(self):
        """AUTH-UNIT-025: Test AuthenticationError creation with minimal parameters."""
        error = AuthenticationError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.details == {}
    
    def test_authentication_error_creation_full(self):
        """AUTH-UNIT-026: Test AuthenticationError creation with all parameters."""
        details = {"key": "value", "number": 42}
        error = AuthenticationError(
            message="Custom error message",
            error_code="CUSTOM_ERROR",
            details=details
        )
        
        assert str(error) == "Custom error message"
        assert error.message == "Custom error message"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.details == details
    
    def test_authentication_error_to_dict(self):
        """AUTH-UNIT-027: Test AuthenticationError to_dict method."""
        details = {"user_id": "123", "action": "login"}
        error = AuthenticationError(
            message="Authentication failed",
            error_code="AUTH_FAILED",
            details=details
        )
        
        expected_dict = {
            "success": False,
            "error": {
                "code": "AUTH_FAILED",
                "message": "Authentication failed",
                "details": details
            }
        }
        
        assert error.to_dict() == expected_dict


class TestInvalidTokenError:
    """Test InvalidTokenError functionality."""
    
    def test_invalid_token_error_default(self):
        """AUTH-UNIT-028: Test InvalidTokenError with default message."""
        error = InvalidTokenError()
        
        assert error.message == "Invalid authentication token"
        assert error.error_code == "INVALID_TOKEN"
        assert error.details == {}
    
    def test_invalid_token_error_custom(self):
        """AUTH-UNIT-029: Test InvalidTokenError with custom message and details."""
        details = {"token_type": "JWT", "issue": "malformed"}
        error = InvalidTokenError(
            message="Token is malformed",
            details=details
        )
        
        assert error.message == "Token is malformed"
        assert error.error_code == "INVALID_TOKEN"
        assert error.details == details


class TestExpiredTokenError:
    """Test ExpiredTokenError functionality."""
    
    def test_expired_token_error_default(self):
        """AUTH-UNIT-030: Test ExpiredTokenError with default message."""
        error = ExpiredTokenError()
        
        assert error.message == "Authentication token has expired"
        assert error.error_code == "TOKEN_EXPIRED"
        assert error.details == {}
    
    def test_expired_token_error_custom(self):
        """AUTH-UNIT-031: Test ExpiredTokenError with custom message and details."""
        details = {"expired_at": "2023-01-01T00:00:00Z"}
        error = ExpiredTokenError(
            message="Token expired at specific time",
            details=details
        )
        
        assert error.message == "Token expired at specific time"
        assert error.error_code == "TOKEN_EXPIRED"
        assert error.details == details


class TestInsufficientScopeError:
    """Test InsufficientScopeError functionality."""
    
    def test_insufficient_scope_error_minimal(self):
        """AUTH-UNIT-032: Test InsufficientScopeError with minimal parameters."""
        error = InsufficientScopeError("write:documents")
        
        assert error.message == "Required scope 'write:documents' not found in token"
        assert error.error_code == "INSUFFICIENT_SCOPE"
        assert error.required_scope == "write:documents"
        assert error.user_scopes == []
        assert error.details == {
            "required_scope": "write:documents",
            "user_scopes": []
        }
    
    def test_insufficient_scope_error_full(self):
        """AUTH-UNIT-033: Test InsufficientScopeError with all parameters."""
        user_scopes = ["read:documents", "search:documents"]
        error = InsufficientScopeError(
            required_scope="write:documents",
            user_scopes=user_scopes,
            message="Custom scope error message"
        )
        
        assert error.message == "Custom scope error message"
        assert error.error_code == "INSUFFICIENT_SCOPE"
        assert error.required_scope == "write:documents"
        assert error.user_scopes == user_scopes
        assert error.details == {
            "required_scope": "write:documents",
            "user_scopes": user_scopes
        }


class TestInsufficientRoleError:
    """Test InsufficientRoleError functionality."""
    
    def test_insufficient_role_error_minimal(self):
        """AUTH-UNIT-034: Test InsufficientRoleError with minimal parameters."""
        error = InsufficientRoleError("admin")
        
        assert error.message == "Required role 'admin' not found for user"
        assert error.error_code == "INSUFFICIENT_ROLE"
        assert error.required_role == "admin"
        assert error.user_roles == []
        assert error.details == {
            "required_role": "admin",
            "user_roles": []
        }
    
    def test_insufficient_role_error_full(self):
        """AUTH-UNIT-035: Test InsufficientRoleError with all parameters."""
        user_roles = ["member", "staff"]
        error = InsufficientRoleError(
            required_role="admin",
            user_roles=user_roles,
            message="Custom role error message"
        )
        
        assert error.message == "Custom role error message"
        assert error.error_code == "INSUFFICIENT_ROLE"
        assert error.required_role == "admin"
        assert error.user_roles == user_roles
        assert error.details == {
            "required_role": "admin",
            "user_roles": user_roles
        }


class TestMissingClaimError:
    """Test MissingClaimError functionality."""
    
    def test_missing_claim_error_minimal(self):
        """AUTH-UNIT-036: Test MissingClaimError with minimal parameters."""
        error = MissingClaimError("sub")
        
        assert error.message == "Required claim 'sub' not found in token"
        assert error.error_code == "MISSING_CLAIM"
        assert error.claim_name == "sub"
        assert error.details == {"missing_claim": "sub"}
    
    def test_missing_claim_error_custom_message(self):
        """AUTH-UNIT-037: Test MissingClaimError with custom message."""
        error = MissingClaimError(
            claim_name="email",
            message="Email claim is required for this operation"
        )
        
        assert error.message == "Email claim is required for this operation"
        assert error.error_code == "MISSING_CLAIM"
        assert error.claim_name == "email"
        assert error.details == {"missing_claim": "email"}


class TestOrganizationAccessError:
    """Test OrganizationAccessError functionality."""
    
    def test_organization_access_error_minimal(self):
        """AUTH-UNIT-038: Test OrganizationAccessError with minimal parameters."""
        error = OrganizationAccessError()
        
        assert error.message == "Access denied: insufficient organization permissions"
        assert error.error_code == "ORGANIZATION_ACCESS_DENIED"
        assert error.user_org_id is None
        assert error.required_org_id is None
        assert error.details == {
            "user_organization_id": None,
            "required_organization_id": None
        }
    
    def test_organization_access_error_full(self):
        """AUTH-UNIT-039: Test OrganizationAccessError with all parameters."""
        error = OrganizationAccessError(
            user_org_id="org-123",
            required_org_id="org-456",
            message="User cannot access resources from different organization"
        )
        
        assert error.message == "User cannot access resources from different organization"
        assert error.error_code == "ORGANIZATION_ACCESS_DENIED"
        assert error.user_org_id == "org-123"
        assert error.required_org_id == "org-456"
        assert error.details == {
            "user_organization_id": "org-123",
            "required_organization_id": "org-456"
        }


class TestConfigurationError:
    """Test ConfigurationError functionality."""
    
    def test_configuration_error_default(self):
        """AUTH-UNIT-040: Test ConfigurationError with default message."""
        error = ConfigurationError()
        
        assert error.message == "Authentication configuration error"
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details == {}
    
    def test_configuration_error_custom(self):
        """AUTH-UNIT-041: Test ConfigurationError with custom message and details."""
        details = {"missing_config": "AUTH0_DOMAIN", "service": "auth-service"}
        error = ConfigurationError(
            message="Missing required Auth0 configuration",
            details=details
        )
        
        assert error.message == "Missing required Auth0 configuration"
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details == details


class TestExceptionInheritance:
    """Test exception inheritance and polymorphism."""
    
    def test_all_exceptions_inherit_from_authentication_error(self):
        """AUTH-UNIT-042: Test all custom exceptions inherit from AuthenticationError."""
        exceptions = [
            InvalidTokenError(),
            ExpiredTokenError(),
            InsufficientScopeError("test"),
            InsufficientRoleError("test"),
            MissingClaimError("test"),
            OrganizationAccessError(),
            ConfigurationError(),
        ]
        
        for exception in exceptions:
            assert isinstance(exception, AuthenticationError)
            assert isinstance(exception, Exception)
    
    def test_exception_polymorphism(self):
        """AUTH-UNIT-043: Test exception polymorphism with to_dict method."""
        exceptions = [
            InvalidTokenError("Invalid token"),
            ExpiredTokenError("Token expired"),
            InsufficientScopeError("write:documents"),
            MissingClaimError("sub"),
            ConfigurationError("Config error"),
        ]
        
        for exception in exceptions:
            result = exception.to_dict()
            assert isinstance(result, dict)
            assert "success" in result
            assert result["success"] is False
            assert "error" in result
            assert "code" in result["error"]
            assert "message" in result["error"]
            assert "details" in result["error"]
