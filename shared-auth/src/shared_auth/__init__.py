"""
Resume Match Pro Shared Auth Package

Reusable Auth0 JWT middleware for FastAPI microservices.
Provides consistent authentication across all services.
"""

from .middleware import Auth0Middleware, validate_auth0_config
from .models import AuthUser, JWTPayload
from .exceptions import (
    AuthenticationError,
    InvalidTokenError,
    ExpiredTokenError,
    InsufficientScopeError,
    MissingClaimError,
)
from .dependencies import (
    require_auth,
    require_admin,
    require_organization_member,
    get_user_from_headers,
)
from .utils import auth0_subject_to_uuid, is_valid_uuid, normalize_user_id

__version__ = "0.1.0"
__all__ = [
    # Core classes
    "Auth0Middleware",
    "AuthUser",
    "JWTPayload",
    # Configuration
    "validate_auth0_config",
    # Exceptions
    "AuthenticationError",
    "InvalidTokenError", 
    "ExpiredTokenError",
    "InsufficientScopeError",
    "MissingClaimError",
    # Dependencies
    "require_auth",
    "require_admin", 
    "require_organization_member",
    "get_user_from_headers",
    # Utilities
    "auth0_subject_to_uuid",
    "is_valid_uuid",
    "normalize_user_id",
]
