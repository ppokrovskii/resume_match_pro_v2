"""
Unit tests for authentication models.

Test ID: AUTH-UNIT-001 to AUTH-UNIT-011
"""

import pytest
from shared_auth.models import AuthUser


class TestAuthUser:
    """Test AuthUser model functionality."""
    
    def test_auth_user_creation_minimal(self):
        """AUTH-UNIT-001: Test AuthUser creation with minimal required fields."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com"
        )
        
        assert user.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert user.email == "test@example.com"
        assert user.organization_id is None
        assert user.roles == []
        assert user.auth0_subject is None
        assert user.email_verified is False
        assert user.scopes == []
    
    def test_auth_user_creation_full(self):
        """AUTH-UNIT-002: Test AuthUser creation with all fields."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            organization_id="org-456",
            roles=["admin", "member"],
            auth0_subject="auth0|test-user-123",
            email_verified=True,
            scopes=["read:documents", "write:documents"]
        )
        
        assert user.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert user.email == "test@example.com"
        assert user.organization_id == "org-456"
        assert user.roles == ["admin", "member"]
        assert user.auth0_subject == "auth0|test-user-123"
        assert user.email_verified is True
        assert user.scopes == ["read:documents", "write:documents"]
    
    def test_is_admin_property_true(self):
        """AUTH-UNIT-003: Test is_admin property returns True for admin users."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="admin@example.com",
            roles=["admin", "member"]
        )
        
        assert user.is_admin is True
    
    def test_is_admin_property_false(self):
        """AUTH-UNIT-004: Test is_admin property returns False for non-admin users."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            roles=["member"]
        )
        
        assert user.is_admin is False
    
    def test_is_organization_member_true(self):
        """AUTH-UNIT-005: Test is_organization_member returns True when user has org."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            organization_id="org-456"
        )
        
        assert user.is_organization_member is True
    
    def test_is_organization_member_false(self):
        """AUTH-UNIT-006: Test is_organization_member returns False when user has no org."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            organization_id=None
        )
        
        assert user.is_organization_member is False
    
    def test_has_verified_email_true(self):
        """AUTH-UNIT-007: Test has_verified_email returns True for verified users."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            email_verified=True
        )
        
        assert user.has_verified_email is True
    
    def test_has_verified_email_false(self):
        """AUTH-UNIT-008: Test has_verified_email returns False for unverified users."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            email_verified=False
        )
        
        assert user.has_verified_email is False
    
    def test_has_role_true(self):
        """AUTH-UNIT-009: Test has_role returns True when user has the role."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            roles=["admin", "member", "staff"]
        )
        
        assert user.has_role("admin") is True
        assert user.has_role("member") is True
        assert user.has_role("staff") is True
    
    def test_has_role_false(self):
        """AUTH-UNIT-010: Test has_role returns False when user doesn't have the role."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            roles=["member"]
        )
        
        assert user.has_role("admin") is False
        assert user.has_role("staff") is False
        assert user.has_role("manager") is False
    
    def test_has_scope_true(self):
        """AUTH-UNIT-011: Test has_scope returns True when user has the scope."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            scopes=["read:documents", "write:documents", "delete:documents"]
        )
        
        assert user.has_scope("read:documents") is True
        assert user.has_scope("write:documents") is True
        assert user.has_scope("delete:documents") is True
    
    def test_has_scope_false(self):
        """AUTH-UNIT-012: Test has_scope returns False when user doesn't have the scope."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            scopes=["read:documents"]
        )
        
        assert user.has_scope("write:documents") is False
        assert user.has_scope("delete:documents") is False
        assert user.has_scope("admin:all") is False
    
    def test_has_any_role_true(self):
        """AUTH-UNIT-013: Test has_any_role returns True when user has at least one role."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            roles=["member"]
        )
        
        assert user.has_any_role(["admin", "member"]) is True
        assert user.has_any_role(["member", "staff"]) is True
        assert user.has_any_role(["member"]) is True
    
    def test_has_any_role_false(self):
        """AUTH-UNIT-014: Test has_any_role returns False when user has none of the roles."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            roles=["member"]
        )
        
        assert user.has_any_role(["admin", "staff"]) is False
        assert user.has_any_role(["manager", "supervisor"]) is False
        assert user.has_any_role([]) is False
    
    def test_has_all_roles_true(self):
        """AUTH-UNIT-015: Test has_all_roles returns True when user has all roles."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            roles=["admin", "member", "staff"]
        )
        
        assert user.has_all_roles(["admin", "member"]) is True
        assert user.has_all_roles(["member", "staff"]) is True
        assert user.has_all_roles(["admin"]) is True
        assert user.has_all_roles([]) is True  # Empty list should return True
    
    def test_has_all_roles_false(self):
        """AUTH-UNIT-016: Test has_all_roles returns False when user doesn't have all roles."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            roles=["member"]
        )
        
        assert user.has_all_roles(["admin", "member"]) is False
        assert user.has_all_roles(["member", "staff"]) is False
        assert user.has_all_roles(["admin", "staff", "manager"]) is False
    
    def test_to_dict(self):
        """AUTH-UNIT-017: Test to_dict method returns correct dictionary."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            organization_id="org-456",
            roles=["admin", "member"],
            auth0_subject="auth0|test-user-123",
            email_verified=True,
            scopes=["read:documents", "write:documents"]
        )
        
        expected_dict = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "organization_id": "org-456",
            "roles": ["admin", "member"],
            "auth0_subject": "auth0|test-user-123",
            "email_verified": True,
            "scopes": ["read:documents", "write:documents"]
        }
        
        assert user.to_dict() == expected_dict
    
    def test_from_dict(self):
        """AUTH-UNIT-018: Test from_dict class method creates correct AuthUser."""
        user_data = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "organization_id": "org-456",
            "roles": ["admin", "member"],
            "auth0_subject": "auth0|test-user-123",
            "email_verified": True,
            "scopes": ["read:documents", "write:documents"]
        }
        
        user = AuthUser.from_dict(user_data)
        
        assert user.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert user.email == "user@example.com"
        assert user.organization_id == "org-456"
        assert user.roles == ["admin", "member"]
        assert user.auth0_subject == "auth0|test-user-123"
        assert user.email_verified is True
        assert user.scopes == ["read:documents", "write:documents"]
    
    def test_from_dict_minimal(self):
        """AUTH-UNIT-019: Test from_dict with minimal data."""
        user_data = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com"
        }
        
        user = AuthUser.from_dict(user_data)
        
        assert user.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert user.email == "user@example.com"
        assert user.organization_id is None
        assert user.roles == []
        assert user.auth0_subject is None
        assert user.email_verified is False
        assert user.scopes == []
    
    def test_str_representation(self):
        """AUTH-UNIT-020: Test string representation of AuthUser."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            organization_id="org-456"
        )
        
        expected_str = "AuthUser(id=123e4567-e89b-12d3-a456-426614174000, email=user@example.com (org: org-456))"
        assert str(user) == expected_str
    
    def test_str_representation_no_org(self):
        """AUTH-UNIT-021: Test string representation without organization."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com"
        )
        
        expected_str = "AuthUser(id=123e4567-e89b-12d3-a456-426614174000, email=user@example.com)"
        assert str(user) == expected_str
    
    def test_repr_representation(self):
        """AUTH-UNIT-022: Test repr representation of AuthUser."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            organization_id="org-456",
            roles=["member"],
            auth0_subject="auth0|test-user-123",
            email_verified=True,
            scopes=["read:documents"]
        )
        
        expected_repr = (
            "AuthUser("
            "user_id='123e4567-e89b-12d3-a456-426614174000', "
            "email='user@example.com', "
            "organization_id='org-456', "
            "roles=['member'], "
            "auth0_subject='auth0|test-user-123', "
            "email_verified=True, "
            "scopes=['read:documents']"
            ")"
        )
        
        assert repr(user) == expected_repr
    
    def test_post_init_default_values(self):
        """AUTH-UNIT-023: Test __post_init__ sets default values for None fields."""
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            roles=None,
            scopes=None
        )
        
        assert user.roles == []
        assert user.scopes == []
    
    def test_post_init_preserves_existing_values(self):
        """AUTH-UNIT-024: Test __post_init__ preserves existing non-None values."""
        roles = ["admin", "member"]
        scopes = ["read:documents", "write:documents"]
        
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            roles=roles,
            scopes=scopes
        )
        
        assert user.roles is roles  # Same object reference
        assert user.scopes is scopes  # Same object reference
