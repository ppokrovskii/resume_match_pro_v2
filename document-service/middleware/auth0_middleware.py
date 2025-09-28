"""
Auth0 Authentication Middleware for FastAPI
Handles JWT token verification and user authentication
"""

import os
import jwt
import requests
from typing import Optional, Dict, Any
from functools import lru_cache
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token security
security = HTTPBearer(auto_error=False)

@lru_cache()
def get_auth0_config() -> Dict[str, Any]:
    """Get Auth0 configuration from environment variables"""
    return {
        "domain": os.getenv("AUTH0_DOMAIN"),
        "api_identifier": os.getenv("AUTH0_API_IDENTIFIER", os.getenv("AUTH0_AUDIENCE")),
        "algorithms": [os.getenv("AUTH0_ALGORITHMS", "RS256")]
    }

@lru_cache()
def get_jwks() -> Dict[str, Any]:
    """Get JSON Web Key Set from Auth0"""
    config = get_auth0_config()
    if not config["domain"]:
        raise ValueError("AUTH0_DOMAIN environment variable is required")
    
    jwks_url = f"https://{config['domain']}/.well-known/jwks.json"
    try:
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch JWKS from Auth0: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch authentication keys"
        )

def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Verify Auth0 JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Dict containing the decoded JWT payload
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    # Check for local test token first (for E2E testing)
    local_test_token = os.getenv("LOCAL_TEST_TOKEN")
    if local_test_token and credentials and credentials.credentials == local_test_token:
        logger.info("Using local test token for development")
        return {
            "sub": "test-user-123",
            "email": "test@resumematch.local",
            "scope": "read:documents write:documents delete:documents search:documents",
            "aud": get_auth0_config()["api_identifier"]
        }
    
    # Handle mock tokens for testing - allowed only in non-production test envs
    if credentials and credentials.credentials.startswith("mock-test-") and os.getenv("FASTAPI_ENV") in {"testing", "local", "development"}:
        # Extract user info from mock token format: mock-test-{user_id}
        token_parts = credentials.credentials.split("-")
        if len(token_parts) >= 3:
            user_id = "-".join(token_parts[2:])  # Handle UUIDs with dashes
            logger.info(f"Using mock test token for user: {user_id}")
            return {
                "sub": f"auth0|{user_id}",  # Auth0 subject format
                "email": f"test-{user_id}@example.com",
                "scope": "read:documents write:documents delete:documents search:documents",
                "aud": get_auth0_config()["api_identifier"]
            }
    
    # Handle legacy mock tokens for testing (non-production only)
    if (credentials and credentials.credentials.startswith("mock-") and 
        os.getenv("FASTAPI_ENV") in {"testing", "local", "development"}):
        logger.info("Using mock token for testing")
        return {
            "sub": "123e4567-e89b-12d3-a456-426614174000",  # Valid UUID format
            "email": "mock@test.local",
            "scope": "read:documents write:documents delete:documents search:documents",
            "aud": get_auth0_config()["api_identifier"]
        }
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "Authentication token is required"
                }
            }
        )
    
    try:
        config = get_auth0_config()
        
        if not config["domain"] or not config["api_identifier"]:
            raise HTTPException(
                status_code=500,
                detail="Auth0 configuration is incomplete"
            )
        
        # Decode token header to get key ID
        try:
            unverified_header = jwt.get_unverified_header(credentials.credentials)
        except jwt.DecodeError:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_TOKEN_FORMAT",
                        "message": "Invalid token format"
                    }
                }
            )
        
        # Get JWKS and find the correct key
        jwks = get_jwks()
        rsa_key = None
        
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header["kid"]:
                # Convert JWK to PyJWT key object
                from jwt import PyJWK
                rsa_key = PyJWK(key).key
                break
        
        if not rsa_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_TOKEN_KEY",
                        "message": "Unable to find appropriate key"
                    }
                }
            )
        
        # Verify and decode the token
        payload = jwt.decode(
            credentials.credentials,
            rsa_key,
            algorithms=config["algorithms"],
            audience=config["api_identifier"],
            issuer=f"https://{config['domain']}/"
        )
        
        logger.debug(f"Successfully verified token for user: {payload.get('sub', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Token has expired"
                }
            }
        )
    except (jwt.InvalidAudienceError, jwt.InvalidIssuerError, jwt.MissingRequiredClaimError) as e:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_TOKEN_CLAIMS",
                    "message": f"Invalid token claims: {str(e)}"
                }
            }
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "AUTHENTICATION_FAILED",
                    "message": f"Token verification failed: {str(e)}"
                }
            }
        )

async def get_current_user_id(token_payload: Dict[str, Any] = Depends(verify_token)) -> str:
    """
    Extract user ID from Auth0 token and convert to UUID format
    
    Args:
        token_payload: Decoded JWT payload
        
    Returns:
        UUID string converted from Auth0 subject for database compatibility
    """
    auth0_subject = token_payload.get("sub", "")
    if not auth0_subject:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "MISSING_USER_ID",
                    "message": "User ID not found in token"
                }
            }
        )
    
    # Convert Auth0 subject to UUID format for database compatibility
    from utils.auth_utils import auth0_subject_to_uuid
    try:
        user_uuid = auth0_subject_to_uuid(auth0_subject)
        logger.debug(f"Converted Auth0 subject '{auth0_subject}' to UUID '{user_uuid}'")
        return user_uuid
    except Exception as e:
        logger.error(f"Failed to convert Auth0 subject to UUID: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "USER_ID_CONVERSION_FAILED",
                    "message": "Failed to convert user ID to required format"
                }
            }
        )

def get_current_org_id(token_payload: Dict[str, Any] = Depends(verify_token)) -> Optional[str]:
    """
    Extract organization ID from token claims if present. Returns string UUID or None.
    """
    org_claim = token_payload.get("organization_id") or token_payload.get("org_id")
    return org_claim or None

def get_current_user_email(token_payload: Dict[str, Any] = Depends(verify_token)) -> Optional[str]:
    """
    Extract user email from Auth0 token
    
    Args:
        token_payload: Decoded JWT payload
        
    Returns:
        User email from the token, if available
    """
    return token_payload.get("email")

def require_scope(required_scope: str):
    """
    Dependency factory to require specific Auth0 scope
    
    Args:
        required_scope: The scope required to access the endpoint
        
    Returns:
        FastAPI dependency function
    """
    def check_scope(token_payload: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
        scopes = token_payload.get("scope", "").split()
        
        if required_scope not in scopes:
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "error": {
                        "code": "INSUFFICIENT_SCOPE",
                        "message": f"Required scope '{required_scope}' not found in token"
                    }
                }
            )
        
        return token_payload
    
    return check_scope

# Common scope dependencies
require_read_documents = require_scope("read:documents")
require_write_documents = require_scope("write:documents")
require_delete_documents = require_scope("delete:documents")
require_search_documents = require_scope("search:documents")

class Auth0Middleware:
    """Auth0 authentication middleware for FastAPI applications"""
    
    def __init__(self, app):
        """Initialize Auth0 middleware"""
        self.app = app
        
        # Validate Auth0 configuration on startup
        config = get_auth0_config()
        if not config["domain"]:
            logger.warning("AUTH0_DOMAIN not configured - authentication will not work")
        if not config["api_identifier"]:
            logger.warning("AUTH0_API_IDENTIFIER not configured - authentication will not work")
        
        logger.info("Auth0 middleware initialized")
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware call method"""
        # For now, just pass through to the app
        # The actual authentication is handled by FastAPI dependencies
        await self.app(scope, receive, send)

# Optional: Auth0 user info helper
def get_user_info(token_payload: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Get user information from Auth0 token
    
    Args:
        token_payload: Decoded JWT payload
        
    Returns:
        Dictionary containing user information
    """
    # Get the original Auth0 subject for user info
    auth0_subject = token_payload.get("sub", "")
    
    # Get the UUID for database operations
    from utils.auth_utils import auth0_subject_to_uuid
    user_uuid = auth0_subject_to_uuid(auth0_subject) if auth0_subject else ""
    
    return {
        "user_id": user_uuid,  # UUID for database
        "auth0_subject": auth0_subject,  # Original Auth0 subject
        "email": token_payload.get("email"),
        "email_verified": token_payload.get("email_verified", False),
        "scopes": token_payload.get("scope", "").split(),
        "audience": token_payload.get("aud"),
        "issuer": token_payload.get("iss")
    }
