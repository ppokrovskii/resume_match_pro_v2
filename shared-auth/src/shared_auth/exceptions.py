"""
Custom exceptions for authentication and authorization.
"""

from typing import Optional, Dict, Any


class AuthenticationError(Exception):
    """
    Base exception for all authentication-related errors.
    
    This is the parent class for all auth-specific exceptions,
    allowing for broad exception handling when needed.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "AUTHENTICATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize authentication error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API responses.
        
        Returns:
            Dictionary representation of the error
        """
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


class InvalidTokenError(AuthenticationError):
    """
    Raised when a JWT token is invalid or malformed.
    
    This includes cases where:
    - Token format is invalid
    - Token signature is invalid
    - Token claims are missing or invalid
    """
    
    def __init__(
        self, 
        message: str = "Invalid authentication token",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code="INVALID_TOKEN",
            details=details
        )


class ExpiredTokenError(AuthenticationError):
    """
    Raised when a JWT token has expired.
    
    This is a specific case of invalid token that can be handled
    differently (e.g., prompting for re-authentication).
    """
    
    def __init__(
        self, 
        message: str = "Authentication token has expired",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code="TOKEN_EXPIRED",
            details=details
        )


class InsufficientScopeError(AuthenticationError):
    """
    Raised when a user lacks required OAuth2 scopes.
    
    This is used for fine-grained permission control based on
    OAuth2 scopes granted to the user.
    """
    
    def __init__(
        self, 
        required_scope: str,
        user_scopes: Optional[list] = None,
        message: Optional[str] = None
    ) -> None:
        if message is None:
            message = f"Required scope '{required_scope}' not found in token"
        
        details = {
            "required_scope": required_scope,
            "user_scopes": user_scopes or []
        }
        
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_SCOPE",
            details=details
        )
        
        self.required_scope = required_scope
        self.user_scopes = user_scopes or []


class InsufficientRoleError(AuthenticationError):
    """
    Raised when a user lacks required roles.
    
    This is used for role-based access control (RBAC) where
    certain operations require specific user roles.
    """
    
    def __init__(
        self, 
        required_role: str,
        user_roles: Optional[list] = None,
        message: Optional[str] = None
    ) -> None:
        if message is None:
            message = f"Required role '{required_role}' not found for user"
        
        details = {
            "required_role": required_role,
            "user_roles": user_roles or []
        }
        
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_ROLE",
            details=details
        )
        
        self.required_role = required_role
        self.user_roles = user_roles or []


class MissingClaimError(AuthenticationError):
    """
    Raised when a required JWT claim is missing.
    
    This is used when the token is valid but lacks required
    claims for the specific operation.
    """
    
    def __init__(
        self, 
        claim_name: str,
        message: Optional[str] = None
    ) -> None:
        if message is None:
            message = f"Required claim '{claim_name}' not found in token"
        
        details = {"missing_claim": claim_name}
        
        super().__init__(
            message=message,
            error_code="MISSING_CLAIM",
            details=details
        )
        
        self.claim_name = claim_name


class OrganizationAccessError(AuthenticationError):
    """
    Raised when a user tries to access resources outside their organization.
    
    This enforces organization-level data isolation in multi-tenant
    applications.
    """
    
    def __init__(
        self, 
        user_org_id: Optional[str] = None,
        required_org_id: Optional[str] = None,
        message: Optional[str] = None
    ) -> None:
        if message is None:
            message = "Access denied: insufficient organization permissions"
        
        details = {
            "user_organization_id": user_org_id,
            "required_organization_id": required_org_id
        }
        
        super().__init__(
            message=message,
            error_code="ORGANIZATION_ACCESS_DENIED",
            details=details
        )
        
        self.user_org_id = user_org_id
        self.required_org_id = required_org_id


class ConfigurationError(AuthenticationError):
    """
    Raised when authentication configuration is invalid or missing.
    
    This is used for setup and configuration issues that prevent
    the authentication system from working properly.
    """
    
    def __init__(
        self, 
        message: str = "Authentication configuration error",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details
        )
