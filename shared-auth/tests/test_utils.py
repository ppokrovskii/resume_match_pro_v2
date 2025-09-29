"""
Unit tests for authentication utilities.

Test ID: AUTH-UNIT-044 to AUTH-UNIT-070
"""

import pytest
from shared_auth.utils import (
    auth0_subject_to_uuid,
    is_valid_uuid,
    normalize_user_id,
    extract_user_id_from_headers,
    extract_organization_id_from_headers,
    extract_user_email_from_headers,
    extract_user_roles_from_headers,
    extract_user_scopes_from_headers,
)


class TestAuth0SubjectToUuid:
    """Test auth0_subject_to_uuid functionality."""
    
    def test_auth0_subject_to_uuid_valid(self):
        """AUTH-UNIT-044: Test auth0_subject_to_uuid with valid Auth0 subject."""
        subject = "google-oauth2|107180533664024577076"
        result = auth0_subject_to_uuid(subject)
        
        # Should return a valid UUID string
        assert isinstance(result, str)
        assert len(result) == 36  # UUID format: 8-4-4-4-12
        assert result.count("-") == 4
        
        # Should be deterministic (same input -> same output)
        result2 = auth0_subject_to_uuid(subject)
        assert result == result2
    
    def test_auth0_subject_to_uuid_different_subjects(self):
        """AUTH-UNIT-045: Test auth0_subject_to_uuid with different subjects produces different UUIDs."""
        subject1 = "google-oauth2|107180533664024577076"
        subject2 = "auth0|user123"
        
        uuid1 = auth0_subject_to_uuid(subject1)
        uuid2 = auth0_subject_to_uuid(subject2)
        
        assert uuid1 != uuid2
    
    def test_auth0_subject_to_uuid_empty_string(self):
        """AUTH-UNIT-046: Test auth0_subject_to_uuid raises ValueError for empty string."""
        with pytest.raises(ValueError, match="Auth0 subject cannot be empty"):
            auth0_subject_to_uuid("")
    
    def test_auth0_subject_to_uuid_none(self):
        """AUTH-UNIT-047: Test auth0_subject_to_uuid raises ValueError for None."""
        with pytest.raises(ValueError, match="Auth0 subject cannot be empty"):
            auth0_subject_to_uuid(None)
    
    def test_auth0_subject_to_uuid_whitespace(self):
        """AUTH-UNIT-048: Test auth0_subject_to_uuid with whitespace-only string."""
        # Whitespace should be treated as valid input (not empty)
        result = auth0_subject_to_uuid("   ")
        assert isinstance(result, str)
        assert len(result) == 36


class TestIsValidUuid:
    """Test is_valid_uuid functionality."""
    
    def test_is_valid_uuid_valid_formats(self):
        """AUTH-UNIT-049: Test is_valid_uuid returns True for valid UUID formats."""
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
            "00000000-0000-0000-0000-000000000000",
        ]
        
        for uuid_str in valid_uuids:
            assert is_valid_uuid(uuid_str) is True
    
    def test_is_valid_uuid_invalid_formats(self):
        """AUTH-UNIT-050: Test is_valid_uuid returns False for invalid UUID formats."""
        invalid_uuids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456",  # Too short
            "123e4567-e89b-12d3-a456-426614174000-extra",  # Too long
            "123e4567-e89b-12d3-a456-42661417400g",  # Invalid character
            "123e4567e89b12d3a456426614174000",  # Missing dashes
            "",  # Empty string
            "123e4567-e89b-12d3-a456-42661417400",  # One character short
        ]
        
        for uuid_str in invalid_uuids:
            assert is_valid_uuid(uuid_str) is False
    
    def test_is_valid_uuid_none(self):
        """AUTH-UNIT-051: Test is_valid_uuid returns False for None."""
        assert is_valid_uuid(None) is False
    
    def test_is_valid_uuid_non_string(self):
        """AUTH-UNIT-052: Test is_valid_uuid returns False for non-string types."""
        assert is_valid_uuid(123) is False
        assert is_valid_uuid([]) is False
        assert is_valid_uuid({}) is False


class TestNormalizeUserId:
    """Test normalize_user_id functionality."""
    
    def test_normalize_user_id_valid_uuid(self):
        """AUTH-UNIT-053: Test normalize_user_id returns UUID as-is when already valid."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        result = normalize_user_id(uuid_str)
        
        assert result == uuid_str
    
    def test_normalize_user_id_auth0_subject(self):
        """AUTH-UNIT-054: Test normalize_user_id converts Auth0 subject to UUID."""
        auth0_subject = "google-oauth2|107180533664024577076"
        result = normalize_user_id(auth0_subject)
        
        # Should return a valid UUID
        assert is_valid_uuid(result) is True
        
        # Should be same as direct conversion
        expected = auth0_subject_to_uuid(auth0_subject)
        assert result == expected
    
    def test_normalize_user_id_empty_string(self):
        """AUTH-UNIT-055: Test normalize_user_id raises ValueError for empty string."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            normalize_user_id("")
    
    def test_normalize_user_id_none(self):
        """AUTH-UNIT-056: Test normalize_user_id raises ValueError for None."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            normalize_user_id(None)


class TestExtractUserIdFromHeaders:
    """Test extract_user_id_from_headers functionality."""
    
    def test_extract_user_id_standard_header(self):
        """AUTH-UNIT-057: Test extracting user ID from standard X-User-ID header."""
        headers = {"X-User-ID": "123e4567-e89b-12d3-a456-426614174000"}
        result = extract_user_id_from_headers(headers)
        
        assert result == "123e4567-e89b-12d3-a456-426614174000"
    
    def test_extract_user_id_case_variations(self):
        """AUTH-UNIT-058: Test extracting user ID from various header case variations."""
        test_cases = [
            {"X-User-ID": "user-123"},
            {"x-user-id": "user-123"},
            {"User-ID": "user-123"},
            {"user-id": "user-123"},
        ]
        
        for headers in test_cases:
            result = extract_user_id_from_headers(headers)
            assert result == "user-123"
    
    def test_extract_user_id_with_whitespace(self):
        """AUTH-UNIT-059: Test extracting user ID strips whitespace."""
        headers = {"X-User-ID": "  user-123  "}
        result = extract_user_id_from_headers(headers)
        
        assert result == "user-123"
    
    def test_extract_user_id_not_found(self):
        """AUTH-UNIT-060: Test extracting user ID returns None when not found."""
        headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
        result = extract_user_id_from_headers(headers)
        
        assert result is None
    
    def test_extract_user_id_empty_headers(self):
        """AUTH-UNIT-061: Test extracting user ID from empty headers."""
        result = extract_user_id_from_headers({})
        assert result is None


class TestExtractOrganizationIdFromHeaders:
    """Test extract_organization_id_from_headers functionality."""
    
    def test_extract_organization_id_standard_header(self):
        """AUTH-UNIT-062: Test extracting org ID from standard header."""
        headers = {"X-Organization-ID": "org-456"}
        result = extract_organization_id_from_headers(headers)
        
        assert result == "org-456"
    
    def test_extract_organization_id_variations(self):
        """AUTH-UNIT-063: Test extracting org ID from various header variations."""
        test_cases = [
            {"X-Organization-ID": "org-456"},
            {"x-organization-id": "org-456"},
            {"Organization-ID": "org-456"},
            {"organization-id": "org-456"},
            {"X-Org-ID": "org-456"},
            {"x-org-id": "org-456"},
            {"Org-ID": "org-456"},
            {"org-id": "org-456"},
        ]
        
        for headers in test_cases:
            result = extract_organization_id_from_headers(headers)
            assert result == "org-456"
    
    def test_extract_organization_id_not_found(self):
        """AUTH-UNIT-064: Test extracting org ID returns None when not found."""
        headers = {"X-User-ID": "user-123"}
        result = extract_organization_id_from_headers(headers)
        
        assert result is None


class TestExtractUserEmailFromHeaders:
    """Test extract_user_email_from_headers functionality."""
    
    def test_extract_user_email_standard_header(self):
        """AUTH-UNIT-065: Test extracting email from standard header."""
        headers = {"X-User-Email": "user@example.com"}
        result = extract_user_email_from_headers(headers)
        
        assert result == "user@example.com"
    
    def test_extract_user_email_variations(self):
        """AUTH-UNIT-066: Test extracting email from various header variations."""
        test_cases = [
            {"X-User-Email": "user@example.com"},
            {"x-user-email": "user@example.com"},
            {"User-Email": "user@example.com"},
            {"user-email": "user@example.com"},
        ]
        
        for headers in test_cases:
            result = extract_user_email_from_headers(headers)
            assert result == "user@example.com"
    
    def test_extract_user_email_not_found(self):
        """AUTH-UNIT-067: Test extracting email returns None when not found."""
        headers = {"X-User-ID": "user-123"}
        result = extract_user_email_from_headers(headers)
        
        assert result is None


class TestExtractUserRolesFromHeaders:
    """Test extract_user_roles_from_headers functionality."""
    
    def test_extract_user_roles_single_role(self):
        """AUTH-UNIT-068: Test extracting single role from headers."""
        headers = {"X-User-Roles": "admin"}
        result = extract_user_roles_from_headers(headers)
        
        assert result == ["admin"]
    
    def test_extract_user_roles_multiple_roles(self):
        """AUTH-UNIT-069: Test extracting multiple roles from headers."""
        headers = {"X-User-Roles": "admin,member,staff"}
        result = extract_user_roles_from_headers(headers)
        
        assert result == ["admin", "member", "staff"]
    
    def test_extract_user_roles_with_whitespace(self):
        """AUTH-UNIT-070: Test extracting roles strips whitespace."""
        headers = {"X-User-Roles": " admin , member , staff "}
        result = extract_user_roles_from_headers(headers)
        
        assert result == ["admin", "member", "staff"]
    
    def test_extract_user_roles_empty_values(self):
        """AUTH-UNIT-071: Test extracting roles filters out empty values."""
        headers = {"X-User-Roles": "admin,,member,"}
        result = extract_user_roles_from_headers(headers)
        
        assert result == ["admin", "member"]
    
    def test_extract_user_roles_not_found(self):
        """AUTH-UNIT-072: Test extracting roles returns empty list when not found."""
        headers = {"X-User-ID": "user-123"}
        result = extract_user_roles_from_headers(headers)
        
        assert result == []


class TestExtractUserScopesFromHeaders:
    """Test extract_user_scopes_from_headers functionality."""
    
    def test_extract_user_scopes_single_scope(self):
        """AUTH-UNIT-073: Test extracting single scope from headers."""
        headers = {"X-User-Scopes": "read:documents"}
        result = extract_user_scopes_from_headers(headers)
        
        assert result == ["read:documents"]
    
    def test_extract_user_scopes_multiple_scopes(self):
        """AUTH-UNIT-074: Test extracting multiple scopes from headers."""
        headers = {"X-User-Scopes": "read:documents write:documents delete:documents"}
        result = extract_user_scopes_from_headers(headers)
        
        assert result == ["read:documents", "write:documents", "delete:documents"]
    
    def test_extract_user_scopes_with_extra_whitespace(self):
        """AUTH-UNIT-075: Test extracting scopes handles extra whitespace."""
        headers = {"X-User-Scopes": "  read:documents   write:documents  "}
        result = extract_user_scopes_from_headers(headers)
        
        assert result == ["read:documents", "write:documents"]
    
    def test_extract_user_scopes_empty_values(self):
        """AUTH-UNIT-076: Test extracting scopes filters out empty values."""
        headers = {"X-User-Scopes": "read:documents  write:documents"}
        result = extract_user_scopes_from_headers(headers)
        
        assert result == ["read:documents", "write:documents"]
    
    def test_extract_user_scopes_not_found(self):
        """AUTH-UNIT-077: Test extracting scopes returns empty list when not found."""
        headers = {"X-User-ID": "user-123"}
        result = extract_user_scopes_from_headers(headers)
        
        assert result == []
    
    def test_extract_user_scopes_variations(self):
        """AUTH-UNIT-078: Test extracting scopes from various header variations."""
        test_cases = [
            {"X-User-Scopes": "read:documents"},
            {"x-user-scopes": "read:documents"},
            {"User-Scopes": "read:documents"},
            {"user-scopes": "read:documents"},
        ]
        
        for headers in test_cases:
            result = extract_user_scopes_from_headers(headers)
            assert result == ["read:documents"]


class TestHeaderExtractionIntegration:
    """Test header extraction functions working together."""
    
    def test_extract_all_user_context(self):
        """AUTH-UNIT-079: Test extracting complete user context from headers."""
        headers = {
            "X-User-ID": "123e4567-e89b-12d3-a456-426614174000",
            "X-User-Email": "user@example.com",
            "X-Organization-ID": "org-456",
            "X-User-Roles": "admin,member",
            "X-User-Scopes": "read:documents write:documents delete:documents"
        }
        
        user_id = extract_user_id_from_headers(headers)
        email = extract_user_email_from_headers(headers)
        org_id = extract_organization_id_from_headers(headers)
        roles = extract_user_roles_from_headers(headers)
        scopes = extract_user_scopes_from_headers(headers)
        
        assert user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert email == "user@example.com"
        assert org_id == "org-456"
        assert roles == ["admin", "member"]
        assert scopes == ["read:documents", "write:documents", "delete:documents"]
    
    def test_extract_partial_user_context(self):
        """AUTH-UNIT-080: Test extracting partial user context from headers."""
        headers = {
            "X-User-ID": "123e4567-e89b-12d3-a456-426614174000",
            "X-User-Email": "user@example.com",
            # Missing organization, roles, and scopes
        }
        
        user_id = extract_user_id_from_headers(headers)
        email = extract_user_email_from_headers(headers)
        org_id = extract_organization_id_from_headers(headers)
        roles = extract_user_roles_from_headers(headers)
        scopes = extract_user_scopes_from_headers(headers)
        
        assert user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert email == "user@example.com"
        assert org_id is None
        assert roles == []
        assert scopes == []
