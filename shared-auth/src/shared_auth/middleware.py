"""
Auth0 JWT middleware for FastAPI applications.

This module provides the main Auth0Middleware class for validating
JWT tokens and extracting user context.
"""

import os
import jwt
import requests
import logging
import time
import re
from typing import Optional, Dict, Any, List
from functools import lru_cache
from urllib.parse import urlparse

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import AuthUser
from .exceptions import (
    InvalidTokenError,
    ExpiredTokenError,
    MissingClaimError,
    ConfigurationError,
)
from .utils import auth0_subject_to_uuid

logger = logging.getLogger(__name__)

# OpenTelemetry tracing
try:
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    TRACING_ENABLED = True
except ImportError:
    # Graceful fallback if OpenTelemetry is not installed
    tracer = None
    TRACING_ENABLED = False
    logger.debug("OpenTelemetry not available, tracing disabled")


def validate_auth0_config(
    domain: Optional[str] = None,
    api_identifier: Optional[str] = None,
    algorithms: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate Auth0 configuration at startup.
    
    Args:
        domain: Auth0 domain (optional, will check environment if not provided)
        api_identifier: API identifier (optional, will check environment if not provided)
        algorithms: JWT algorithms (optional, will check environment if not provided)
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    from .exceptions import ConfigurationError
    
    # Get configuration from parameters or environment
    config_domain = domain or os.getenv("AUTH0_DOMAIN")
    config_api_identifier = api_identifier or os.getenv("AUTH0_API_IDENTIFIER")
    config_algorithms = algorithms or [os.getenv("AUTH0_ALGORITHMS", "RS256")]
    
    # Validate required fields
    if not config_domain:
        raise ConfigurationError(
            "AUTH0_DOMAIN is required",
            details={"missing_config": "AUTH0_DOMAIN"}
        )
    
    if not config_api_identifier:
        raise ConfigurationError(
            "AUTH0_API_IDENTIFIER is required",
            details={"missing_config": "AUTH0_API_IDENTIFIER"}
        )
    
    # Validate domain format
    if not _is_valid_auth0_domain(config_domain):
        raise ConfigurationError(
            f"Invalid AUTH0_DOMAIN format: {config_domain}",
            details={
                "domain": config_domain,
                "expected_format": "your-tenant.auth0.com or your-tenant.us.auth0.com"
            }
        )
    
    # Validate API identifier format (should be a valid URL)
    if not _is_valid_api_identifier(config_api_identifier):
        raise ConfigurationError(
            f"Invalid AUTH0_API_IDENTIFIER format: {config_api_identifier}",
            details={
                "api_identifier": config_api_identifier,
                "expected_format": "https://your-api.example.com"
            }
        )
    
    # Validate algorithms
    supported_algorithms = ["RS256", "RS384", "RS512", "HS256", "HS384", "HS512"]
    for alg in config_algorithms:
        if alg not in supported_algorithms:
            raise ConfigurationError(
                f"Unsupported algorithm: {alg}",
                details={
                    "algorithm": alg,
                    "supported_algorithms": supported_algorithms
                }
            )
    
    logger.info("Auth0 configuration validation successful", extra={
        "event_type": "config_validation_success",
        "domain": config_domain,
        "api_identifier": config_api_identifier,
        "algorithms": config_algorithms
    })
    
    return {
        "domain": config_domain,
        "api_identifier": config_api_identifier,
        "algorithms": config_algorithms
    }


def _is_valid_auth0_domain(domain: str) -> bool:
    """
    Validate Auth0 domain format.
    
    Args:
        domain: Domain to validate
        
    Returns:
        True if valid Auth0 domain format
    """
    # Auth0 domain patterns:
    # - tenant.auth0.com
    # - tenant.us.auth0.com  
    # - tenant.eu.auth0.com
    # - tenant.au.auth0.com
    # - custom-domain.com (for custom domains)
    
    if not domain or not isinstance(domain, str):
        return False
    
    # Remove protocol if present
    domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
    
    # Standard Auth0 domain pattern
    auth0_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]\.(us\.|eu\.|au\.)?auth0\.com$'
    
    # Custom domain pattern (basic validation)
    custom_domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$'
    
    return (
        re.match(auth0_pattern, domain) is not None or
        re.match(custom_domain_pattern, domain) is not None
    )


def _is_valid_api_identifier(api_identifier: str) -> bool:
    """
    Validate API identifier format.
    
    Args:
        api_identifier: API identifier to validate
        
    Returns:
        True if valid API identifier format
    """
    if not api_identifier or not isinstance(api_identifier, str):
        return False
    
    try:
        parsed = urlparse(api_identifier)
        return (
            parsed.scheme in ["https", "http"] and
            parsed.netloc and
            len(parsed.netloc) > 0
        )
    except Exception:
        return False


class Auth0Middleware:
    """
    Auth0 JWT middleware for FastAPI applications.
    
    This middleware handles JWT token validation using Auth0's JWKS endpoint
    and provides user context extraction for authenticated requests.
    
    Usage:
        auth = Auth0Middleware(
            domain="your-tenant.auth0.com",
            api_identifier="https://your-api.com"
        )
        
        user = await auth.verify_token_from_request(request)
    """
    
    def __init__(
        self,
        domain: Optional[str] = None,
        api_identifier: Optional[str] = None,
        algorithms: Optional[List[str]] = None,
        cache_jwks: bool = True,
        jwks_cache_ttl: int = 3600,
    ) -> None:
        """
        Initialize Auth0 middleware.
        
        Args:
            domain: Auth0 domain (e.g., "tenant.auth0.com")
            api_identifier: Auth0 API identifier/audience
            algorithms: JWT algorithms to accept (default: ["RS256"])
            cache_jwks: Whether to cache JWKS responses
            jwks_cache_ttl: JWKS cache TTL in seconds
            
        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Validate and get configuration
        config = validate_auth0_config(domain, api_identifier, algorithms)
        self.domain = config["domain"]
        self.api_identifier = config["api_identifier"]
        self.algorithms = config["algorithms"]
        
        # JWKS configuration
        self.cache_jwks = cache_jwks
        self.jwks_cache_ttl = jwks_cache_ttl
        self.jwks_url = f"https://{self.domain}/.well-known/jwks.json"
        self.issuer = f"https://{self.domain}/"
        
        # HTTP Bearer security
        self.security = HTTPBearer(auto_error=False)
        
        # JWKS cache with TTL
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_time: float = 0
        
        logger.info(
            f"Auth0Middleware initialized for domain: {self.domain}, "
            f"audience: {self.api_identifier}"
        )
    
    def _get_jwks(self) -> Dict[str, Any]:
        """
        Get JSON Web Key Set from Auth0 with TTL-based caching.
        
        This method implements TTL-based caching to avoid repeated requests to Auth0
        while ensuring keys are refreshed periodically for security.
        
        Returns:
            JWKS dictionary from Auth0
            
        Raises:
            ConfigurationError: If JWKS cannot be fetched
        """
        if TRACING_ENABLED and tracer:
            with tracer.start_as_current_span("auth.get_jwks") as span:
                span.set_attribute("auth.jwks_url", self.jwks_url)
                span.set_attribute("auth.cache_enabled", self.cache_jwks)
                return self._get_jwks_impl()
        else:
            return self._get_jwks_impl()
    
    def _get_jwks_impl(self) -> Dict[str, Any]:
        """Implementation of JWKS fetching with caching."""
        current_time = time.time()
        
        # Check if cache is valid
        if (self._jwks_cache is not None and 
            self.cache_jwks and 
            (current_time - self._jwks_cache_time) < self.jwks_cache_ttl):
            logger.debug("Using cached JWKS")
            if TRACING_ENABLED and tracer:
                trace.get_current_span().set_attribute("auth.jwks_cache_hit", True)
            return self._jwks_cache
        
        try:
            logger.debug(f"Fetching JWKS from: {self.jwks_url}")
            if TRACING_ENABLED and tracer:
                trace.get_current_span().set_attribute("auth.jwks_cache_hit", False)
            
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()
            jwks = response.json()
            logger.debug(f"Successfully fetched JWKS with {len(jwks.get('keys', []))} keys")
            
            # Update cache
            if self.cache_jwks:
                self._jwks_cache = jwks
                self._jwks_cache_time = current_time
                logger.debug(f"JWKS cached for {self.jwks_cache_ttl} seconds")
            
            if TRACING_ENABLED and tracer:
                trace.get_current_span().set_attribute("auth.jwks_keys_count", len(jwks.get('keys', [])))
            
            return jwks
        except requests.RequestException as e:
            logger.error(f"Failed to fetch JWKS from Auth0: {e}")
            if TRACING_ENABLED and tracer:
                trace.get_current_span().record_exception(e)
                trace.get_current_span().set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise ConfigurationError(
                "Failed to fetch authentication keys from Auth0",
                details={"jwks_url": self.jwks_url, "error": str(e)}
            )
    
    def _get_signing_key(self, token: str) -> Any:
        """
        Get the signing key for a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            PyJWT key object for token verification
            
        Raises:
            InvalidTokenError: If token format is invalid or key not found
        """
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise InvalidTokenError(
                    "Token header missing 'kid' claim",
                    details={"header": unverified_header}
                )
            
        except jwt.DecodeError as e:
            raise InvalidTokenError(
                "Invalid token format",
                details={"decode_error": str(e)}
            )
        
        # Get JWKS and find the correct key
        jwks = self._get_jwks()
        
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Convert JWK to PyJWT key object
                try:
                    from jwt import PyJWK
                    return PyJWK(key).key
                except Exception as e:
                    raise InvalidTokenError(
                        "Failed to process signing key",
                        details={"kid": kid, "error": str(e)}
                    )
        
        raise InvalidTokenError(
            f"Unable to find signing key with kid: {kid}",
            details={"kid": kid, "available_kids": [k.get("kid") for k in jwks.get("keys", [])]}
        )
    
    def _verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded JWT payload
            
        Raises:
            InvalidTokenError: If token is invalid
            ExpiredTokenError: If token has expired
        """
        if TRACING_ENABLED and tracer:
            with tracer.start_as_current_span("auth.verify_jwt_token") as span:
                span.set_attribute("auth.audience", self.api_identifier)
                span.set_attribute("auth.issuer", self.issuer)
                span.set_attribute("auth.algorithms", ",".join(self.algorithms))
                return self._verify_jwt_token_impl(token)
        else:
            return self._verify_jwt_token_impl(token)
    
    def _verify_jwt_token_impl(self, token: str) -> Dict[str, Any]:
        """Implementation of JWT token verification."""
        try:
            # Get signing key
            signing_key = self._get_signing_key(token)
            
            # Verify and decode the token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.algorithms,
                audience=self.api_identifier,
                issuer=self.issuer,
            )
            
            logger.debug(f"Successfully verified token for user: {payload.get('sub', 'unknown')}")
            
            if TRACING_ENABLED and tracer:
                span = trace.get_current_span()
                span.set_attribute("auth.user_id", payload.get('sub', 'unknown'))
                span.set_attribute("auth.email", payload.get('email', 'unknown'))
                span.set_attribute("auth.verification_success", True)
            
            return payload
            
        except jwt.ExpiredSignatureError as e:
            if TRACING_ENABLED and tracer:
                span = trace.get_current_span()
                span.record_exception(e)
                span.set_attribute("auth.error_type", "expired_token")
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Token expired"))
            raise ExpiredTokenError("Token has expired")
        except jwt.InvalidAudienceError as e:
            if TRACING_ENABLED and tracer:
                span = trace.get_current_span()
                span.record_exception(e)
                span.set_attribute("auth.error_type", "invalid_audience")
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Invalid audience"))
            raise InvalidTokenError(
                "Invalid token audience",
                details={"expected_audience": self.api_identifier}
            )
        except jwt.InvalidIssuerError as e:
            if TRACING_ENABLED and tracer:
                span = trace.get_current_span()
                span.record_exception(e)
                span.set_attribute("auth.error_type", "invalid_issuer")
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Invalid issuer"))
            raise InvalidTokenError(
                "Invalid token issuer",
                details={"expected_issuer": self.issuer}
            )
        except jwt.MissingRequiredClaimError as e:
            if TRACING_ENABLED and tracer:
                span = trace.get_current_span()
                span.record_exception(e)
                span.set_attribute("auth.error_type", "missing_claim")
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Missing required claim"))
            raise MissingClaimError(str(e))
        except jwt.InvalidTokenError as e:
            if TRACING_ENABLED and tracer:
                span = trace.get_current_span()
                span.record_exception(e)
                span.set_attribute("auth.error_type", "invalid_token")
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Invalid token"))
            raise InvalidTokenError(f"Token validation failed: {str(e)}")
    
    def _extract_user_from_payload(self, payload: Dict[str, Any]) -> AuthUser:
        """
        Extract AuthUser from JWT payload.
        
        Args:
            payload: Decoded JWT payload
            
        Returns:
            AuthUser instance
            
        Raises:
            MissingClaimError: If required claims are missing
        """
        # Extract required claims
        auth0_subject = payload.get("sub")
        if not auth0_subject:
            raise MissingClaimError("sub")
        
        email = payload.get("email")
        if not email:
            raise MissingClaimError("email")
        
        # Convert Auth0 subject to UUID
        try:
            user_id = auth0_subject_to_uuid(auth0_subject)
        except ValueError as e:
            raise InvalidTokenError(
                f"Failed to convert Auth0 subject to UUID: {str(e)}",
                details={"auth0_subject": auth0_subject}
            )
        
        # Extract optional claims
        organization_id = payload.get("organization_id") or payload.get("org_id")
        email_verified = payload.get("email_verified", False)
        
        # Extract roles from custom claims or namespace
        roles = []
        role_claims = [
            "roles",
            "user_roles", 
            f"https://{self.domain}/roles",
            "https://resumematch.com/roles",
        ]
        for claim in role_claims:
            if claim in payload:
                roles = payload[claim]
                if isinstance(roles, str):
                    roles = [roles]
                break
        
        # Extract scopes
        scopes = []
        scope_str = payload.get("scope", "")
        if scope_str:
            scopes = scope_str.split()
        
        return AuthUser(
            user_id=user_id,
            email=email,
            organization_id=organization_id,
            roles=roles or [],
            auth0_subject=auth0_subject,
            email_verified=email_verified,
            scopes=scopes,
        )
    
    def _handle_test_tokens(self, token: str) -> Optional[AuthUser]:
        """
        Handle test tokens for development and testing environments.
        
        Args:
            token: Token string to check
            
        Returns:
            AuthUser if test token is valid, None otherwise
        """
        env = os.getenv("FASTAPI_ENV", "production").lower()
        allow_mock = os.getenv("ALLOW_MOCK_TOKENS", "false").lower() == "true"
        
        # Strict security: Only allow test tokens in testing with explicit flag
        if env != "testing" or not allow_mock:
            return None
        
        # Handle local test token
        local_test_token = os.getenv("LOCAL_TEST_TOKEN")
        if local_test_token and token == local_test_token:
            logger.info("Authentication event", extra={
                "event_type": "local_test_token_used",
                "user_id": "test-user-123",
                "environment": env,
                "token_type": "local_test"
            })
            return AuthUser(
                user_id=auth0_subject_to_uuid("test-user-123"),
                email="test@resumematch.local",
                organization_id=None,
                roles=["member"],
                auth0_subject="test-user-123",
                email_verified=True,
                scopes=["read:documents", "write:documents", "delete:documents", "search:documents"],
            )
        
        # Handle mock test tokens with user ID
        if token.startswith("mock-test-"):
            token_parts = token.split("-")
            if len(token_parts) >= 3:
                user_id = "-".join(token_parts[2:])  # Handle UUIDs with dashes
                logger.info("Authentication event", extra={
                    "event_type": "mock_test_token_used",
                    "user_id": user_id,
                    "environment": env,
                    "token_type": "mock_test"
                })
                return AuthUser(
                    user_id=auth0_subject_to_uuid(f"auth0|{user_id}"),
                    email=f"test-{user_id}@example.com",
                    organization_id=None,
                    roles=["member"],
                    auth0_subject=f"auth0|{user_id}",
                    email_verified=True,
                    scopes=["read:documents", "write:documents", "delete:documents", "search:documents"],
                )
        
        # Handle legacy mock tokens
        if token.startswith("mock-"):
            logger.info("Authentication event", extra={
                "event_type": "legacy_mock_token_used",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "environment": env,
                "token_type": "legacy_mock"
            })
            return AuthUser(
                user_id="123e4567-e89b-12d3-a456-426614174000",
                email="mock@test.local",
                organization_id=None,
                roles=["member"],
                auth0_subject="123e4567-e89b-12d3-a456-426614174000",
                email_verified=True,
                scopes=["read:documents", "write:documents", "delete:documents", "search:documents"],
            )
        
        return None
    
    async def verify_token_from_request(self, request: Request) -> AuthUser:
        """
        Verify JWT token from FastAPI request and return user context.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            AuthUser instance with user context
            
        Raises:
            HTTPException: If authentication fails (401/403)
        """
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "AUTHENTICATION_REQUIRED",
                            "message": "Authorization header is required"
                        }
                    }
                )
            
            # Parse Bearer token
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "INVALID_AUTH_HEADER",
                            "message": "Authorization header must start with 'Bearer '"
                        }
                    }
                )
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Check for test tokens first
            test_user = self._handle_test_tokens(token)
            if test_user:
                return test_user
            
            # Verify JWT token
            payload = self._verify_jwt_token(token)
            
            # Extract user from payload
            user = self._extract_user_from_payload(payload)
            
            return user
            
        except HTTPException:
            # Re-raise HTTPException as-is (already has correct status code)
            raise
        except (InvalidTokenError, ExpiredTokenError, MissingClaimError) as e:
            raise HTTPException(
                status_code=401,
                detail=e.to_dict()
            )
        except ConfigurationError as e:
            logger.error(f"Auth configuration error: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_UNAVAILABLE",
                        "message": "Authentication service is temporarily unavailable"
                    }
                }
            )
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": "An unexpected authentication error occurred"
                    }
                }
            )
    
    async def verify_token_from_credentials(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials]
    ) -> AuthUser:
        """
        Verify JWT token from HTTPAuthorizationCredentials.
        
        This method is designed to work with FastAPI's HTTPBearer security.
        
        Args:
            credentials: HTTPAuthorizationCredentials from FastAPI security
            
        Returns:
            AuthUser instance with user context
            
        Raises:
            HTTPException: If authentication fails (401/403)
        """
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
            token = credentials.credentials
            
            # Check for test tokens first
            test_user = self._handle_test_tokens(token)
            if test_user:
                return test_user
            
            # Verify JWT token
            payload = self._verify_jwt_token(token)
            
            # Extract user from payload
            user = self._extract_user_from_payload(payload)
            
            return user
            
        except HTTPException:
            # Re-raise HTTPException as-is (already has correct status code)
            raise
        except (InvalidTokenError, ExpiredTokenError, MissingClaimError) as e:
            raise HTTPException(
                status_code=401,
                detail=e.to_dict()
            )
        except ConfigurationError as e:
            logger.error(f"Auth configuration error: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_UNAVAILABLE",
                        "message": "Authentication service is temporarily unavailable"
                    }
                }
            )
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": "An unexpected authentication error occurred"
                    }
                }
            )
