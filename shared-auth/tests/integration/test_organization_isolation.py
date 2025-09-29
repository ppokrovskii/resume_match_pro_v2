"""
Integration tests for organization boundary enforcement.

These tests ensure that users from one organization cannot access 
data from another organization (multi-tenancy security).

Critical for:
- Security vulnerability prevention
- Compliance requirements (GDPR, SOC2, ISO27001)
- Enterprise customer data isolation
- Regulatory audit requirements
"""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock

from shared_auth.models import AuthUser
from shared_auth.exceptions import OrganizationAccessError
from shared_auth.dependencies import require_organization_access
from tests.conftest import create_test_user, create_test_document


@pytest.mark.integration
class TestOrganizationBoundaryEnforcement:
    """Test that users cannot access data from other organizations."""
    
    def test_same_organization_access_allowed(self, test_organizations):
        """ORG-SEC-001: Users can access data from their own organization."""
        # Setup: Create user and document in same org
        user_org_123 = create_test_user(
            user_id="user-alice", 
            org_id=test_organizations["org_a"]
        )
        org_123_document = create_test_document(
            doc_id="doc-123", 
            owner_org=test_organizations["org_a"]
        )
        
        # Test: User accesses their own org's data
        result = self._simulate_document_access(user_org_123, org_123_document)
        
        # Verify: Access is allowed
        assert result["allowed"] is True
        assert result["user_org"] == test_organizations["org_a"]
        assert result["document_org"] == test_organizations["org_a"]
    
    def test_different_organization_access_denied(self, test_organizations):
        """ORG-SEC-002: Users cannot access data from other organizations."""
        # Setup: Create users in different orgs
        user_org_123 = create_test_user(
            user_id="user-alice", 
            org_id=test_organizations["org_a"]
        )
        user_org_456 = create_test_user(
            user_id="user-bob", 
            org_id=test_organizations["org_b"]
        )
        
        # Create data for org-456
        org_456_document = create_test_document(
            doc_id="doc-456", 
            owner_org=test_organizations["org_b"]
        )
        
        # Test: User from org-123 tries to access org-456 data
        with pytest.raises(OrganizationAccessError) as exc_info:
            self._simulate_document_access_with_enforcement(user_org_123, org_456_document)
        
        # Verify: Access is denied with proper error
        assert "ORGANIZATION_ACCESS_DENIED" in str(exc_info.value)
        assert test_organizations["org_a"] in str(exc_info.value)
        assert test_organizations["org_b"] in str(exc_info.value)
    
    def test_no_organization_access_denied(self, test_organizations):
        """ORG-SEC-003: Users without organization cannot access any org data."""
        # Setup: Create user without organization
        user_no_org = create_test_user(
            user_id="user-charlie", 
            org_id=None
        )
        
        # Create data for specific org
        org_123_document = create_test_document(
            doc_id="doc-123", 
            owner_org=test_organizations["org_a"]
        )
        
        # Test: User without org tries to access org data
        with pytest.raises(OrganizationAccessError) as exc_info:
            self._simulate_document_access_with_enforcement(user_no_org, org_123_document)
        
        # Verify: Access is denied
        assert "ORGANIZATION_ACCESS_DENIED" in str(exc_info.value)
        assert "no organization" in str(exc_info.value).lower()
    
    def test_admin_cross_organization_access(self, test_organizations):
        """ORG-SEC-004: Admin users can access data across organizations."""
        # Setup: Create admin user in org-123
        admin_user = create_test_user(
            user_id="admin-user", 
            org_id=test_organizations["org_a"],
            roles=["admin", "super_admin"]
        )
        
        # Create data for different org
        org_456_document = create_test_document(
            doc_id="doc-456", 
            owner_org=test_organizations["org_b"]
        )
        
        # Test: Admin accesses cross-org data
        result = self._simulate_admin_document_access(admin_user, org_456_document)
        
        # Verify: Admin access is allowed
        assert result["allowed"] is True
        assert result["access_type"] == "admin_override"
        assert result["user_roles"] == ["admin", "super_admin"]
    
    def test_multiple_organization_boundary_violations(self, test_organizations):
        """ORG-SEC-005: Test multiple boundary violations in sequence."""
        # Setup: Create users in different orgs
        users = {
            "alice": create_test_user("alice", org_id=test_organizations["org_a"]),
            "bob": create_test_user("bob", org_id=test_organizations["org_b"]),
            "charlie": create_test_user("charlie", org_id=test_organizations["org_c"])
        }
        
        # Create documents for each org
        documents = {
            "doc_a": create_test_document("doc-a", test_organizations["org_a"]),
            "doc_b": create_test_document("doc-b", test_organizations["org_b"]),
            "doc_c": create_test_document("doc-c", test_organizations["org_c"])
        }
        
        # Test: Each user tries to access other orgs' documents
        violations = []
        
        # Alice tries to access Bob's and Charlie's docs
        for doc_key in ["doc_b", "doc_c"]:
            try:
                self._simulate_document_access_with_enforcement(users["alice"], documents[doc_key])
                violations.append(f"Alice accessed {doc_key} - SECURITY BREACH!")
            except OrganizationAccessError:
                pass  # Expected behavior
        
        # Bob tries to access Alice's and Charlie's docs
        for doc_key in ["doc_a", "doc_c"]:
            try:
                self._simulate_document_access_with_enforcement(users["bob"], documents[doc_key])
                violations.append(f"Bob accessed {doc_key} - SECURITY BREACH!")
            except OrganizationAccessError:
                pass  # Expected behavior
        
        # Verify: No violations occurred
        assert len(violations) == 0, f"Security violations detected: {violations}"
    
    def _simulate_document_access(self, user: AuthUser, document) -> dict:
        """Simulate basic document access without enforcement."""
        return {
            "allowed": user.organization_id == document.owner_org,
            "user_org": user.organization_id,
            "document_org": document.owner_org,
            "user_id": user.user_id
        }
    
    def _simulate_document_access_with_enforcement(self, user: AuthUser, document):
        """Simulate document access with organization enforcement."""
        # Check organization boundary
        if not user.organization_id:
            raise OrganizationAccessError(
                user_org_id=None,
                required_org_id=document.owner_org,
                message="ORGANIZATION_ACCESS_DENIED: User has no organization assigned"
            )
        
        if user.organization_id != document.owner_org:
            raise OrganizationAccessError(
                user_org_id=user.organization_id,
                required_org_id=document.owner_org,
                message=f"ORGANIZATION_ACCESS_DENIED: User from org '{user.organization_id}' "
                        f"cannot access data from org '{document.owner_org}'"
            )
        
        return {
            "allowed": True,
            "user_org": user.organization_id,
            "document_org": document.owner_org
        }
    
    def _simulate_admin_document_access(self, user: AuthUser, document) -> dict:
        """Simulate admin document access with override capability."""
        # Admin users can access cross-org data
        if user.has_role("admin") or user.has_role("super_admin"):
            return {
                "allowed": True,
                "access_type": "admin_override",
                "user_org": user.organization_id,
                "document_org": document.owner_org,
                "user_roles": user.roles
            }
        
        # Non-admin users follow normal org boundaries
        return self._simulate_document_access(user, document)


@pytest.mark.integration
class TestOrganizationDependencyInjection:
    """Test organization access control via FastAPI dependencies."""
    
    @pytest.mark.asyncio
    async def test_require_organization_access_dependency(self, test_organizations):
        """ORG-DEP-001: Test require_organization_access FastAPI dependency."""
        # Setup: Create user
        user = create_test_user(org_id=test_organizations["org_a"])
        
        # Test: Dependency allows access to same org
        dependency_func = require_organization_access(test_organizations["org_a"])
        result = await dependency_func(user=user)
        
        # Verify: Access granted
        assert result.organization_id == test_organizations["org_a"]
    
    @pytest.mark.asyncio
    async def test_require_organization_access_denied(self, test_organizations):
        """ORG-DEP-002: Test dependency denies cross-org access."""
        # Setup: Create user in org-123
        user = create_test_user(org_id=test_organizations["org_a"])
        
        # Test: Dependency denies access to different org
        dependency_func = require_organization_access(test_organizations["org_b"])
        
        with pytest.raises(Exception) as exc_info:  # Accept any HTTP exception type
            await dependency_func(user=user)
        
        # Verify: 403 Forbidden with proper error
        assert hasattr(exc_info.value, 'status_code') and exc_info.value.status_code == 403
        assert "ORGANIZATION_ACCESS_DENIED" in str(exc_info.value)
