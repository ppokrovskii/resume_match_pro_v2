"""
Authentication utilities for Auth0 integration
"""

import uuid
import hashlib


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
    """
    try:
        uuid.UUID(uuid_string)
        return True
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
    """
    if is_valid_uuid(user_id):
        return user_id
    
    # Assume it's an Auth0 subject and convert
    return auth0_subject_to_uuid(user_id)
