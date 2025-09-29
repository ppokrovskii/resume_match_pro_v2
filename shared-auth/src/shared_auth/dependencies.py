"""
FastAPI dependencies for authentication and authorization.

This module provides ready-to-use FastAPI dependencies for common
authentication and authorization patterns.
"""

import os
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import AuthUser
from .middleware import Auth0Middleware
from .exceptions import InsufficientRoleError, OrganizationAccessError
from .utils import (
    extract_user_id_from_headers,
    extract_organization_id_from_headers,
    extract_user_email_from_headers,
    extract_user_roles_from_headers,
    extract_user_scopes_from_headers,
)

# Global Auth0 middleware instance
# This will be initialized when first used
_auth0_middleware: Optional[Auth0Middleware] = None

# HTTP Bearer security for token extraction
security = HTTPBearer(auto_error=False)


def get_auth0_middleware() -> Auth0Middleware:
    """
    Get or create the global Auth0Middleware instance.
    
    Returns:
        Auth0Middleware instance
    """
    global _auth0_middleware
    
    if _auth0_middleware is None:
        _auth0_middleware = Auth0Middleware()
    
    return _auth0_middleware


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthUser:
    """
    FastAPI dependency to verify JWT token and return user context.
    
    This dependency should be used in API Gateway services that need
    to validate JWT tokens directly.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        AuthUser instance with user context
        
    Raises:
        HTTPException: If authentication fails (401/403)
        
    Example:
        @app.get("/protected")
        async def protected_endpoint(user: AuthUser = Depends(verify_token)):
            return {"user_id": user.user_id}
    """
    auth = get_auth0_middleware()
    return await auth.verify_token_from_credentials(credentials)


def get_user_from_headers(headers: Dict[str, str]) -> Optional[AuthUser]:
    """
    Extract user context from HTTP headers set by API Gateway.
    
    This function is used by internal services that trust the API Gateway
    to have already validated the JWT token and added user context to headers.
    
    Args:
        headers: HTTP headers dictionary
        
    Returns:
        AuthUser instance if user context found, None otherwise
        
    Example:
        headers = {"X-User-ID": "123", "X-User-Email": "user@example.com"}
        user = get_user_from_headers(headers)
    """
    user_id = extract_user_id_from_headers(headers)
    if not user_id:
        return None
    
    email = extract_user_email_from_headers(headers)
    if not email:
        return None
    
    organization_id = extract_organization_id_from_headers(headers)
    roles = extract_user_roles_from_headers(headers)
    scopes = extract_user_scopes_from_headers(headers)
    
    return AuthUser(
        user_id=user_id,
        email=email,
        organization_id=organization_id,
        roles=roles,
        scopes=scopes,
        email_verified=True,  # Assume verified if coming from gateway
    )


async def get_user_from_request_headers(request: Request) -> Optional[AuthUser]:
    """
    FastAPI dependency to extract user context from request headers.
    
    This dependency should be used in internal services that trust
    the API Gateway to have validated tokens and added user context.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        AuthUser instance if user context found, None otherwise
        
    Example:
        @app.get("/internal")
        async def internal_endpoint(
            user: Optional[AuthUser] = Depends(get_user_from_request_headers)
        ):
            if user:
                return {"user_id": user.user_id}
            return {"error": "No user context"}
    """
    return get_user_from_headers(dict(request.headers))


async def require_auth(request: Request) -> AuthUser:
    """
    FastAPI dependency that requires authentication.
    
    This dependency works in two modes:
    1. API Gateway mode: Validates JWT tokens directly
    2. Internal service mode: Extracts user from headers
    
    The mode is determined by environment variables or the presence of headers.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        AuthUser instance with user context
        
    Raises:
        HTTPException: If authentication fails or user not found (401)
        
    Example:
        @app.get("/protected")
        async def protected_endpoint(user: AuthUser = Depends(require_auth)):
            return {"user_id": user.user_id}
    """
    # Check if we're in internal service mode (headers from gateway)
    user = await get_user_from_request_headers(request)
    if user:
        return user
    
    # Fall back to JWT validation (API Gateway mode)
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        auth = get_auth0_middleware()
        return await auth.verify_token_from_request(request)
    
    # No authentication found
    raise HTTPException(
        status_code=401,
        detail={
            "success": False,
            "error": {
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Authentication is required to access this resource"
            }
        }
    )


async def require_admin(user: AuthUser = Depends(require_auth)) -> AuthUser:
    """
    FastAPI dependency that requires admin role.
    
    Args:
        user: Authenticated user from require_auth dependency
        
    Returns:
        AuthUser instance (guaranteed to have admin role)
        
    Raises:
        HTTPException: If user doesn't have admin role (403)
        
    Example:
        @app.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: str,
            admin: AuthUser = Depends(require_admin)
        ):
            return {"deleted": user_id}
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail=InsufficientRoleError(
                required_role="admin",
                user_roles=user.roles
            ).to_dict()
        )
    
    return user


async def require_organization_member(user: AuthUser = Depends(require_auth)) -> AuthUser:
    """
    FastAPI dependency that requires organization membership.
    
    Args:
        user: Authenticated user from require_auth dependency
        
    Returns:
        AuthUser instance (guaranteed to belong to an organization)
        
    Raises:
        HTTPException: If user doesn't belong to an organization (403)
        
    Example:
        @app.get("/org/documents")
        async def list_org_documents(
            user: AuthUser = Depends(require_organization_member)
        ):
            return get_documents_for_org(user.organization_id)
    """
    if not user.is_organization_member:
        raise HTTPException(
            status_code=403,
            detail=OrganizationAccessError(
                message="Organization membership is required to access this resource"
            ).to_dict()
        )
    
    return user


def require_role(required_role: str):
    """
    FastAPI dependency factory that requires a specific role.
    
    Args:
        required_role: The role required to access the endpoint
        
    Returns:
        FastAPI dependency function
        
    Example:
        require_manager = require_role("manager")
        
        @app.get("/manager/reports")
        async def get_reports(user: AuthUser = Depends(require_manager)):
            return get_manager_reports(user.user_id)
    """
    async def check_role(user: AuthUser = Depends(require_auth)) -> AuthUser:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=403,
                detail=InsufficientRoleError(
                    required_role=required_role,
                    user_roles=user.roles
                ).to_dict()
            )
        return user
    
    return check_role


def require_any_role(required_roles: list):
    """
    FastAPI dependency factory that requires any of the specified roles.
    
    Args:
        required_roles: List of roles, user must have at least one
        
    Returns:
        FastAPI dependency function
        
    Example:
        require_staff = require_any_role(["admin", "manager", "staff"])
        
        @app.get("/staff/dashboard")
        async def staff_dashboard(user: AuthUser = Depends(require_staff)):
            return get_staff_dashboard(user.user_id)
    """
    async def check_any_role(user: AuthUser = Depends(require_auth)) -> AuthUser:
        if not user.has_any_role(required_roles):
            raise HTTPException(
                status_code=403,
                detail=InsufficientRoleError(
                    required_role=f"any of: {', '.join(required_roles)}",
                    user_roles=user.roles
                ).to_dict()
            )
        return user
    
    return check_any_role


def require_all_roles(required_roles: list):
    """
    FastAPI dependency factory that requires all of the specified roles.
    
    Args:
        required_roles: List of roles, user must have all of them
        
    Returns:
        FastAPI dependency function
        
    Example:
        require_super_admin = require_all_roles(["admin", "super_user"])
        
        @app.delete("/admin/system/reset")
        async def system_reset(user: AuthUser = Depends(require_super_admin)):
            return perform_system_reset()
    """
    async def check_all_roles(user: AuthUser = Depends(require_auth)) -> AuthUser:
        if not user.has_all_roles(required_roles):
            raise HTTPException(
                status_code=403,
                detail=InsufficientRoleError(
                    required_role=f"all of: {', '.join(required_roles)}",
                    user_roles=user.roles
                ).to_dict()
            )
        return user
    
    return check_all_roles


def require_scope(required_scope: str):
    """
    FastAPI dependency factory that requires a specific OAuth2 scope.
    
    Args:
        required_scope: The scope required to access the endpoint
        
    Returns:
        FastAPI dependency function
        
    Example:
        require_write_docs = require_scope("write:documents")
        
        @app.post("/documents")
        async def create_document(
            document: dict,
            user: AuthUser = Depends(require_write_docs)
        ):
            return create_user_document(user.user_id, document)
    """
    async def check_scope(user: AuthUser = Depends(require_auth)) -> AuthUser:
        if not user.has_scope(required_scope):
            from .exceptions import InsufficientScopeError
            raise HTTPException(
                status_code=403,
                detail=InsufficientScopeError(
                    required_scope=required_scope,
                    user_scopes=user.scopes
                ).to_dict()
            )
        return user
    
    return check_scope


def require_organization_access(organization_id: str):
    """
    FastAPI dependency factory that requires access to a specific organization.
    
    Args:
        organization_id: The organization ID that the user must belong to
        
    Returns:
        FastAPI dependency function
        
    Example:
        @app.get("/org/{org_id}/documents")
        async def get_org_documents(
            org_id: str,
            user: AuthUser = Depends(require_organization_access(org_id))
        ):
            return get_documents_for_org(org_id)
    """
    async def check_organization_access(user: AuthUser = Depends(require_auth)) -> AuthUser:
        if user.organization_id != organization_id:
            raise HTTPException(
                status_code=403,
                detail=OrganizationAccessError(
                    user_org_id=user.organization_id,
                    required_org_id=organization_id
                ).to_dict()
            )
        return user
    
    return check_organization_access


# Common scope dependencies for convenience
require_read_documents = require_scope("read:documents")
require_write_documents = require_scope("write:documents")
require_delete_documents = require_scope("delete:documents")
require_search_documents = require_scope("search:documents")

# Common role dependencies for convenience
require_member = require_role("member")
require_manager = require_role("manager")
require_staff = require_any_role(["admin", "manager", "staff"])
