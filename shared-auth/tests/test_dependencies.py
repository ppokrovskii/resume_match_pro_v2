"""
Unit tests for FastAPI dependencies.

Test ID: AUTH-UNIT-116 to AUTH-UNIT-150
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from shared_auth.dependencies import (
    get_auth0_middleware,
    verify_token,
    get_user_from_headers,
    get_user_from_request_headers,
    require_auth,
    require_admin,
    require_organization_member,
    require_role,
    require_any_role,
    require_all_roles,
    require_scope,
    require_organization_access,
)
from shared_auth.models import AuthUser
from shared_auth.exceptions import InsufficientRoleError, OrganizationAccessError


class TestGetAuth0Middleware:
    """Test get_auth0_middleware function."""
    
    def test_get_auth0_middleware_singleton(self):
        """AUTH-UNIT-116: Test get_auth0_middleware returns singleton instance."""
        # Clear any existing instance
        import shared_auth.dependencies
        shared_auth.dependencies._auth0_middleware = None
        
        middleware1 = get_auth0_middleware()
        middleware2 = get_auth0_middleware()
        
        assert middleware1 is middleware2  # Same instance


class TestVerifyToken:
    """Test verify_token dependency."""
    
    @pytest.mark.asyncio
    @patch("shared_auth.dependencies.get_auth0_middleware")
    async def test_verify_token_success(self, mock_get_middleware, mock_auth_user):
        """AUTH-UNIT-117: Test successful token verification."""
        mock_middleware = Mock()
        mock_middleware.verify_token_from_credentials = AsyncMock(return_value=mock_auth_user)
        mock_get_middleware.return_value = mock_middleware
        
        credentials = Mock()
        credentials.credentials = "valid-token"
        
        result = await verify_token(credentials)
        
        assert result == mock_auth_user
        mock_middleware.verify_token_from_credentials.assert_called_once_with(credentials)
    
    @pytest.mark.asyncio
    @patch("shared_auth.dependencies.get_auth0_middleware")
    async def test_verify_token_none_credentials(self, mock_get_middleware):
        """AUTH-UNIT-118: Test token verification with None credentials."""
        mock_middleware = Mock()
        mock_middleware.verify_token_from_credentials = AsyncMock(side_effect=Exception("No credentials"))
        mock_get_middleware.return_value = mock_middleware
        
        with pytest.raises(Exception):
            await verify_token(None)


class TestGetUserFromHeaders:
    """Test get_user_from_headers function."""
    
    def test_get_user_from_headers_complete(self):
        """AUTH-UNIT-119: Test extracting complete user context from headers."""
        headers = {
            "X-User-ID": "123e4567-e89b-12d3-a456-426614174000",
            "X-User-Email": "user@example.com",
            "X-Organization-ID": "org-456",
            "X-User-Roles": "admin,member",
            "X-User-Scopes": "read:documents write:documents"
        }
        
        user = get_user_from_headers(headers)
        
        assert user is not None
        assert user.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert user.email == "user@example.com"
        assert user.organization_id == "org-456"
        assert user.roles == ["admin", "member"]
        assert user.scopes == ["read:documents", "write:documents"]
        assert user.email_verified is True
    
    def test_get_user_from_headers_minimal(self):
        """AUTH-UNIT-120: Test extracting minimal user context from headers."""
        headers = {
            "X-User-ID": "123e4567-e89b-12d3-a456-426614174000",
            "X-User-Email": "user@example.com"
        }
        
        user = get_user_from_headers(headers)
        
        assert user is not None
        assert user.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert user.email == "user@example.com"
        assert user.organization_id is None
        assert user.roles == []
        assert user.scopes == []
    
    def test_get_user_from_headers_missing_user_id(self):
        """AUTH-UNIT-121: Test returns None when user ID is missing."""
        headers = {
            "X-User-Email": "user@example.com"
        }
        
        user = get_user_from_headers(headers)
        
        assert user is None
    
    def test_get_user_from_headers_missing_email(self):
        """AUTH-UNIT-122: Test returns None when email is missing."""
        headers = {
            "X-User-ID": "123e4567-e89b-12d3-a456-426614174000"
        }
        
        user = get_user_from_headers(headers)
        
        assert user is None
    
    def test_get_user_from_headers_empty(self):
        """AUTH-UNIT-123: Test returns None for empty headers."""
        user = get_user_from_headers({})
        
        assert user is None


class TestGetUserFromRequestHeaders:
    """Test get_user_from_request_headers dependency."""
    
    @pytest.mark.asyncio
    async def test_get_user_from_request_headers_success(self):
        """AUTH-UNIT-124: Test successful user extraction from request headers."""
        request = Mock()
        request.headers = {
            "X-User-ID": "123e4567-e89b-12d3-a456-426614174000",
            "X-User-Email": "user@example.com",
            "X-Organization-ID": "org-456"
        }
        
        user = await get_user_from_request_headers(request)
        
        assert user is not None
        assert user.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert user.email == "user@example.com"
        assert user.organization_id == "org-456"
    
    @pytest.mark.asyncio
    async def test_get_user_from_request_headers_none(self):
        """AUTH-UNIT-125: Test returns None when headers are insufficient."""
        request = Mock()
        request.headers = {"Content-Type": "application/json"}
        
        user = await get_user_from_request_headers(request)
        
        assert user is None


class TestRequireAuth:
    """Test require_auth dependency."""
    
    @pytest.mark.asyncio
    @patch("shared_auth.dependencies.get_user_from_request_headers")
    async def test_require_auth_from_headers(self, mock_get_user, mock_auth_user):
        """AUTH-UNIT-126: Test require_auth gets user from headers (internal service mode)."""
        mock_get_user.return_value = mock_auth_user
        
        request = Mock()
        request.headers = {}
        
        result = await require_auth(request)
        
        assert result == mock_auth_user
        mock_get_user.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    @patch("shared_auth.dependencies.get_user_from_request_headers")
    @patch("shared_auth.dependencies.get_auth0_middleware")
    async def test_require_auth_from_jwt(self, mock_get_middleware, mock_get_user, mock_auth_user):
        """AUTH-UNIT-127: Test require_auth validates JWT when no headers (API gateway mode)."""
        mock_get_user.return_value = None  # No user from headers
        
        mock_middleware = Mock()
        mock_middleware.verify_token_from_request = AsyncMock(return_value=mock_auth_user)
        mock_get_middleware.return_value = mock_middleware
        
        request = Mock()
        request.headers = {"authorization": "Bearer valid-token"}
        
        result = await require_auth(request)
        
        assert result == mock_auth_user
        mock_middleware.verify_token_from_request.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    @patch("shared_auth.dependencies.get_user_from_request_headers")
    async def test_require_auth_no_authentication(self, mock_get_user):
        """AUTH-UNIT-128: Test require_auth raises exception when no authentication."""
        mock_get_user.return_value = None
        
        request = Mock()
        request.headers = {}  # No authorization header
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            await require_auth(request)
        
        assert exc_info.value.status_code == 401


class TestRequireAdmin:
    """Test require_admin dependency."""
    
    @pytest.mark.asyncio
    async def test_require_admin_success(self, mock_admin_user):
        """AUTH-UNIT-129: Test require_admin succeeds for admin user."""
        result = await require_admin(mock_admin_user)
        
        assert result == mock_admin_user
    
    @pytest.mark.asyncio
    async def test_require_admin_failure(self, mock_auth_user):
        """AUTH-UNIT-130: Test require_admin fails for non-admin user."""
        # mock_auth_user has roles=["member"], not admin
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            await require_admin(mock_auth_user)
        
        assert exc_info.value.status_code == 403
        assert "INSUFFICIENT_ROLE" in str(exc_info.value.detail)


class TestRequireOrganizationMember:
    """Test require_organization_member dependency."""
    
    @pytest.mark.asyncio
    async def test_require_organization_member_success(self, mock_org_user):
        """AUTH-UNIT-131: Test require_organization_member succeeds for org member."""
        result = await require_organization_member(mock_org_user)
        
        assert result == mock_org_user
    
    @pytest.mark.asyncio
    async def test_require_organization_member_failure(self, mock_no_org_user):
        """AUTH-UNIT-132: Test require_organization_member fails for non-org user."""
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            await require_organization_member(mock_no_org_user)
        
        assert exc_info.value.status_code == 403
        assert "ORGANIZATION_ACCESS_DENIED" in str(exc_info.value.detail)


class TestRequireRole:
    """Test require_role dependency factory."""
    
    @pytest.mark.asyncio
    async def test_require_role_success(self, mock_admin_user):
        """AUTH-UNIT-133: Test require_role succeeds when user has required role."""
        require_admin_role = require_role("admin")
        
        result = await require_admin_role(mock_admin_user)
        
        assert result == mock_admin_user
    
    @pytest.mark.asyncio
    async def test_require_role_failure(self, mock_auth_user):
        """AUTH-UNIT-134: Test require_role fails when user lacks required role."""
        require_admin_role = require_role("admin")
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            await require_admin_role(mock_auth_user)
        
        assert exc_info.value.status_code == 403
        assert "INSUFFICIENT_ROLE" in str(exc_info.value.detail)


class TestRequireAnyRole:
    """Test require_any_role dependency factory."""
    
    @pytest.mark.asyncio
    async def test_require_any_role_success(self, mock_admin_user):
        """AUTH-UNIT-135: Test require_any_role succeeds when user has one of the roles."""
        require_staff = require_any_role(["admin", "manager", "staff"])
        
        result = await require_staff(mock_admin_user)
        
        assert result == mock_admin_user
    
    @pytest.mark.asyncio
    async def test_require_any_role_failure(self, mock_auth_user):
        """AUTH-UNIT-136: Test require_any_role fails when user has none of the roles."""
        require_staff = require_any_role(["admin", "manager", "staff"])
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            await require_staff(mock_auth_user)
        
        assert exc_info.value.status_code == 403
        assert "INSUFFICIENT_ROLE" in str(exc_info.value.detail)


class TestRequireAllRoles:
    """Test require_all_roles dependency factory."""
    
    @pytest.mark.asyncio
    async def test_require_all_roles_success(self, mock_admin_user):
        """AUTH-UNIT-137: Test require_all_roles succeeds when user has all roles."""
        require_admin_member = require_all_roles(["admin", "member"])
        
        result = await require_admin_member(mock_admin_user)
        
        assert result == mock_admin_user
    
    @pytest.mark.asyncio
    async def test_require_all_roles_failure(self, mock_auth_user):
        """AUTH-UNIT-138: Test require_all_roles fails when user lacks some roles."""
        require_admin_member = require_all_roles(["admin", "member"])
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            await require_admin_member(mock_auth_user)
        
        assert exc_info.value.status_code == 403
        assert "INSUFFICIENT_ROLE" in str(exc_info.value.detail)


class TestRequireScope:
    """Test require_scope dependency factory."""
    
    @pytest.mark.asyncio
    async def test_require_scope_success(self, mock_auth_user):
        """AUTH-UNIT-139: Test require_scope succeeds when user has required scope."""
        require_read = require_scope("read:documents")
        
        result = await require_read(mock_auth_user)
        
        assert result == mock_auth_user
    
    @pytest.mark.asyncio
    async def test_require_scope_failure(self, mock_auth_user):
        """AUTH-UNIT-140: Test require_scope fails when user lacks required scope."""
        require_admin = require_scope("admin:all")
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            await require_admin(mock_auth_user)
        
        assert exc_info.value.status_code == 403
        assert "INSUFFICIENT_SCOPE" in str(exc_info.value.detail)


class TestRequireOrganizationAccess:
    """Test require_organization_access dependency factory."""
    
    @pytest.mark.asyncio
    async def test_require_organization_access_success(self, mock_org_user):
        """AUTH-UNIT-141: Test require_organization_access succeeds for matching org."""
        require_org_access = require_organization_access("org-789")
        
        result = await require_org_access(mock_org_user)
        
        assert result == mock_org_user
    
    @pytest.mark.asyncio
    async def test_require_organization_access_failure(self, mock_org_user):
        """AUTH-UNIT-142: Test require_organization_access fails for different org."""
        require_org_access = require_organization_access("org-different")
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            await require_org_access(mock_org_user)
        
        assert exc_info.value.status_code == 403
        assert "ORGANIZATION_ACCESS_DENIED" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_require_organization_access_no_org(self, mock_no_org_user):
        """AUTH-UNIT-143: Test require_organization_access fails for user without org."""
        require_org_access = require_organization_access("org-456")
        
        with pytest.raises(Exception) as exc_info:  # Should raise HTTPException
            await require_org_access(mock_no_org_user)
        
        assert exc_info.value.status_code == 403
        assert "ORGANIZATION_ACCESS_DENIED" in str(exc_info.value.detail)


class TestCommonDependencies:
    """Test pre-defined common dependencies."""
    
    @pytest.mark.asyncio
    async def test_require_read_documents(self, mock_auth_user):
        """AUTH-UNIT-144: Test require_read_documents dependency."""
        from shared_auth.dependencies import require_read_documents
        
        result = await require_read_documents(mock_auth_user)
        
        assert result == mock_auth_user
    
    @pytest.mark.asyncio
    async def test_require_write_documents(self, mock_auth_user):
        """AUTH-UNIT-145: Test require_write_documents dependency."""
        from shared_auth.dependencies import require_write_documents
        
        result = await require_write_documents(mock_auth_user)
        
        assert result == mock_auth_user
    
    @pytest.mark.asyncio
    async def test_require_member(self, mock_auth_user):
        """AUTH-UNIT-146: Test require_member dependency."""
        from shared_auth.dependencies import require_member
        
        result = await require_member(mock_auth_user)
        
        assert result == mock_auth_user
    
    @pytest.mark.asyncio
    async def test_require_staff(self, mock_admin_user):
        """AUTH-UNIT-147: Test require_staff dependency (any of admin/manager/staff)."""
        from shared_auth.dependencies import require_staff
        
        result = await require_staff(mock_admin_user)
        
        assert result == mock_admin_user


class TestDependencyIntegration:
    """Test dependencies working together."""
    
    @pytest.mark.asyncio
    @patch("shared_auth.dependencies.get_user_from_request_headers")
    async def test_auth_flow_internal_service(self, mock_get_user, mock_org_user):
        """AUTH-UNIT-148: Test complete auth flow for internal service."""
        mock_get_user.return_value = mock_org_user
        
        request = Mock()
        request.headers = {}
        
        # Test the flow: require_auth -> require_organization_member
        user = await require_auth(request)
        result = await require_organization_member(user)
        
        assert result == mock_org_user
    
    @pytest.mark.asyncio
    async def test_role_and_scope_combination(self, mock_admin_user):
        """AUTH-UNIT-149: Test combining role and scope requirements."""
        require_admin_with_delete = require_all_roles(["admin"])
        require_delete_scope = require_scope("delete:documents")
        
        # First check role
        user_with_role = await require_admin_with_delete(mock_admin_user)
        # Then check scope
        result = await require_delete_scope(user_with_role)
        
        assert result == mock_admin_user
    
    @pytest.mark.asyncio
    async def test_organization_and_role_combination(self, mock_org_user):
        """AUTH-UNIT-150: Test combining organization and role requirements."""
        require_org_member = require_organization_member
        require_manager = require_role("manager")
        
        # First check organization membership
        user_in_org = await require_org_member(mock_org_user)
        # Then check role
        result = await require_manager(user_in_org)
        
        assert result == mock_org_user
