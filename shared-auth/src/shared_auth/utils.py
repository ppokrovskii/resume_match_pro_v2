"""
Utility functions for authentication and user ID management.
"""

import uuid
import hashlib
from typing import Optional


def auth0_subject_to_uuid(auth0_subject: str) -> str:
    """
    Convert Auth0 subject (like 'google-oauth2|107180533664024577076') to a deterministic UUID.
    
    This is needed because:
    1. Auth0 subjects are strings like "google-oauth2|107180533664024577076"
    2. Our database expects user_id to be UUID type
    3. We need deterministic conversion (same subject -> same UUID)
    
    Args:
        auth0_subject: Auth0 subject string from JWT token
        
    Returns:
        UUID string that can be used as database user_id
        
    Raises:
        ValueError: If auth0_subject is empty or None
        
    Example:
        >>> auth0_subject_to_uuid("google-oauth2|107180533664024577076")
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    """
    if not auth0_subject:
        raise ValueError("Auth0 subject cannot be empty")
    
    # Use MD5 hash to create deterministic UUID from Auth0 subject
    # MD5 is sufficient here since we're not using this for security,
    # just for deterministic UUID generation
    hash_object = hashlib.md5(auth0_subject.encode('utf-8'))
    hash_hex = hash_object.hexdigest()
    
    # Convert hash to UUID format
    uuid_obj = uuid.UUID(hash_hex)
    
    return str(uuid_obj)


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if a string is a valid UUID format.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID, False otherwise
        
    Example:
        >>> is_valid_uuid("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        True
        >>> is_valid_uuid("not-a-uuid")
        False
    """
    if not isinstance(uuid_string, str):
        return False
    
    try:
        # Only accept properly formatted UUIDs with hyphens
        parsed_uuid = uuid.UUID(uuid_string)
        # Ensure the string representation matches (rejects malformed inputs)
        return str(parsed_uuid) == uuid_string.lower()
    except (ValueError, TypeError):
        return False


def normalize_user_id(user_id: str) -> str:
    """
    Normalize user ID to UUID format.
    
    If the user_id is already a valid UUID, return it as-is.
    If it's an Auth0 subject, convert it to UUID.
    
    Args:
        user_id: User ID string (could be UUID or Auth0 subject)
        
    Returns:
        UUID string
        
    Raises:
        ValueError: If user_id is empty or None
        
    Example:
        >>> normalize_user_id("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        >>> normalize_user_id("google-oauth2|107180533664024577076")
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    """
    if not user_id:
        raise ValueError("User ID cannot be empty")
        
    if is_valid_uuid(user_id):
        return user_id
    
    # Assume it's an Auth0 subject and convert
    return auth0_subject_to_uuid(user_id)


def extract_user_id_from_headers(headers: dict) -> Optional[str]:
    """
    Extract user ID from HTTP headers set by API Gateway.
    
    The API Gateway adds user context to headers after JWT validation.
    This function extracts the user ID from those headers.
    
    Args:
        headers: HTTP headers dictionary
        
    Returns:
        User ID string if found, None otherwise
        
    Example:
        >>> headers = {"X-User-ID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
        >>> extract_user_id_from_headers(headers)
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    """
    # Try different header names that might contain user ID
    possible_headers = [
        "X-User-ID",
        "x-user-id", 
        "User-ID",
        "user-id",
    ]
    
    for header_name in possible_headers:
        user_id = headers.get(header_name)
        if user_id:
            return user_id.strip()
    
    return None


def extract_organization_id_from_headers(headers: dict) -> Optional[str]:
    """
    Extract organization ID from HTTP headers set by API Gateway.
    
    Args:
        headers: HTTP headers dictionary
        
    Returns:
        Organization ID string if found, None otherwise
        
    Example:
        >>> headers = {"X-Organization-ID": "org-123"}
        >>> extract_organization_id_from_headers(headers)
        "org-123"
    """
    # Try different header names that might contain organization ID
    possible_headers = [
        "X-Organization-ID",
        "x-organization-id",
        "Organization-ID", 
        "organization-id",
        "X-Org-ID",
        "x-org-id",
        "Org-ID",
        "org-id",
    ]
    
    for header_name in possible_headers:
        org_id = headers.get(header_name)
        if org_id:
            return org_id.strip()
    
    return None


def extract_user_email_from_headers(headers: dict) -> Optional[str]:
    """
    Extract user email from HTTP headers set by API Gateway.
    
    Args:
        headers: HTTP headers dictionary
        
    Returns:
        User email string if found, None otherwise
        
    Example:
        >>> headers = {"X-User-Email": "user@example.com"}
        >>> extract_user_email_from_headers(headers)
        "user@example.com"
    """
    # Try different header names that might contain user email
    possible_headers = [
        "X-User-Email",
        "x-user-email",
        "User-Email",
        "user-email",
    ]
    
    for header_name in possible_headers:
        email = headers.get(header_name)
        if email:
            return email.strip()
    
    return None


def extract_user_roles_from_headers(headers: dict) -> list:
    """
    Extract user roles from HTTP headers set by API Gateway.
    
    Args:
        headers: HTTP headers dictionary
        
    Returns:
        List of role strings, empty list if none found
        
    Example:
        >>> headers = {"X-User-Roles": "admin,member"}
        >>> extract_user_roles_from_headers(headers)
        ["admin", "member"]
    """
    # Try different header names that might contain user roles
    possible_headers = [
        "X-User-Roles",
        "x-user-roles",
        "User-Roles",
        "user-roles",
    ]
    
    for header_name in possible_headers:
        roles_str = headers.get(header_name)
        if roles_str:
            # Split by comma and clean up whitespace
            roles = [role.strip() for role in roles_str.split(",")]
            return [role for role in roles if role]  # Filter out empty strings
    
    return []


def extract_user_scopes_from_headers(headers: dict) -> list:
    """
    Extract user OAuth2 scopes from HTTP headers set by API Gateway.
    
    Args:
        headers: HTTP headers dictionary
        
    Returns:
        List of scope strings, empty list if none found
        
    Example:
        >>> headers = {"X-User-Scopes": "read:documents write:documents"}
        >>> extract_user_scopes_from_headers(headers)
        ["read:documents", "write:documents"]
    """
    # Try different header names that might contain user scopes
    possible_headers = [
        "X-User-Scopes",
        "x-user-scopes",
        "User-Scopes",
        "user-scopes",
    ]
    
    for header_name in possible_headers:
        scopes_str = headers.get(header_name)
        if scopes_str:
            # Split by space (OAuth2 standard) and clean up
            scopes = [scope.strip() for scope in scopes_str.split()]
            return [scope for scope in scopes if scope]  # Filter out empty strings
    
    return []
