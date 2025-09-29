"""
Test configuration and fixtures for shared-auth tests.
"""

import os
import pytest
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

from shared_auth.models import AuthUser
from shared_auth.middleware import Auth0Middleware


@pytest.fixture
def auth_config():
    """Auth0 configuration for testing."""
    return {
        "domain": "test.auth0.com",
        "api_identifier": "https://test-api.resumematch.com",
        "algorithms": ["RS256"]
    }


@pytest.fixture
def mock_auth_user():
    """Mock AuthUser for testing."""
    return AuthUser(
        user_id="123e4567-e89b-12d3-a456-426614174000",
        email="test@example.com",
        organization_id="org-456",
        roles=["member"],
        auth0_subject="auth0|test-user-123",
        email_verified=True,
        scopes=["read:documents", "write:documents"]
    )


@pytest.fixture
def mock_admin_user():
    """Mock admin AuthUser for testing."""
    return AuthUser(
        user_id="admin-567-e89b-12d3-a456-426614174000",
        email="admin@example.com",
        organization_id="org-456",
        roles=["admin", "member"],
        auth0_subject="auth0|admin-user-456",
        email_verified=True,
        scopes=["read:documents", "write:documents", "delete:documents", "admin:all"]
    )


@pytest.fixture
def mock_org_user():
    """Mock organization user for testing."""
    return AuthUser(
        user_id="org-user-789-12d3-a456-426614174000",
        email="orguser@example.com",
        organization_id="org-789",
        roles=["member", "manager"],
        auth0_subject="auth0|org-user-789",
        email_verified=True,
        scopes=["read:documents", "write:documents"]
    )


@pytest.fixture
def mock_no_org_user():
    """Mock user without organization for testing."""
    return AuthUser(
        user_id="no-org-abc-12d3-a456-426614174000",
        email="noorg@example.com",
        organization_id=None,
        roles=["member"],
        auth0_subject="auth0|no-org-abc",
        email_verified=False,
        scopes=["read:documents"]
    )


@pytest.fixture
def rsa_private_key():
    """RSA private key for JWT signing in tests."""
    return """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC5GpuUdbDyglFp
fyZAvSOXRX14A/Gy3j5Rks2CW/ok2UF9G3TkxaGUIR1Zb+EiCTDJCNyZNcCKI/dT
D2GLiS9WyzaFGeEDM4LC26ytkLUKVv4eu0+ROWLpNSd/AejxD/a7GHTYvZeLtyxf
8xPTN7tQ9X1LNxB1pFoTVf6otsBYt/e1TG8kgo9X9pSPkHvFQPI7WKn08jQYXdAc
JOFA4vnNuyFkaUc39NiyKJ72dD5yiM6idfMb9rDClaRGsloQV7iEwSqrjgK2Aox6
a1kwxhJsAdIdzv7rm7G89mSXEzKphQRpJPEgYJxZ/zSLiFknN/WE2WCtVOn+P21y
zlXqcEKxAgMBAAECggEACXo+WavMPGF96MF38GACy9C0+bV1fVWd4hw6saRTFqqJ
TO4gRkOkeBa5N4pn//+xl9SAY4eWGPiaFe6TXXMv6WEwpKBgZhMfzIl2AiHG9D1j
p+gKLRbPrL5CDEGpNzkMlnQsTOnpsc+WWgASnXmkuZKlOHn8ebKJYmSwfBvV1cD4
zLRKzmTMH5Ql2z2LH3VH2t2ut976yFK1LoYium+YlxP8FbGBZDxFj1lvawMn2O6B
rKe8zt3vGw3nxzwewwlfoF7ib6/vmGUmIp5zCrVYRry5v+1ShSecAMbyySQx9w5a
rZny204p4KhB3bvw8JnbJ8/oKypWj+sRyab+Ah+kAQKBgQDnRXCfHOie2/OIMy5g
+8mb5CdyVZXSbuv4AP0ol5N7FtaVp9CpqrIUuk5vZYXmw/OHARJKuLe9DoX/eR2y
Up1E1iuXn9ekmJKRW4YqCRyhU9GOMCXEsUqRYzACworCO7rTfNLlZLu0hhLfnnfH
xNl7glE+AkEZx2/jIdeGkke2sQKBgQDM5W984IvvEq0KJbzb1RCk+xxTfRJqOyll
TuiqnRHUoji+oOGZwJLCFv0wFwHa64lidBpUlBxtcPPc2OrtM621VfYtuIMhfZuU
PZdcEaL8nsB3YAo562wAkdpKE+TwXoHYKWL//4XSb+F6P1Xulcf0GK4Z79uytT5s
ZeAJ/6xMAQKBgCZjEkR2ye3EWHHc/O/AG0Cy6BFEP3AEVUp+74ZTUnl12vxQNIRU
/uYN3oMC+OzKzZs1BFI+wtCwnnE/Kzy0FcKdQfMS5vo9EObrqCNGC+iDPx84wqwZ
OWVUb12l6N5Ah8wexeqpg7Z9IpjXds5D0E193fpK6X9b6ShsL5f4o8qhAoGAU7wk
DtW5ek+YlgAMKY7uiW3yCpCfmPhql3NjFG6yXcKaDBW1fN89WsKIYEHWyT/e2nR2
WkBZScSSdJvVjnDDOctSmya/uE0b6r4tADxY7oJ2R5LhOwBiF+2DVyjANBd7Wvq2
8cXcS77bV9lQZfuiRrhbVlA26da2FxifMZbiNAECgYA4VQEkXK2/9aPsfHTEv+P2
/v3VxWCpkBZH+8NouhNhKWCgygk5/7Baj901v6MwhtkP2OkMvlLAwdmh1cIa/rFc
PWAsjyM4gs82mONCv3FOhRm9oNg90aiUdnCFQoZo1UKW6OrnNyf1iyAgFOAR9GBQ
OXZ5+opVIS+T4u7k4ApgNg==
-----END PRIVATE KEY-----"""


@pytest.fixture
def rsa_public_key():
    """RSA public key for JWT verification in tests."""
    return """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuRqblHWw8oJRaX8mQL0j
l0V9eAPxst4+UZLNglv6JNlBfRt05MWhlCEdWW/hIgkwyQjcmTXAiiP3Uw9hi4kv
Vss2hRnhAzOCwtusrZC1Clb+HrtPkTli6TUnfwHo8Q/2uxh02L2Xi7csX/MT0ze7
UPV9SzcQdaRaE1X+qLbAWLf3tUxvJIKPV/aUj5B7xUDyO1ip9PI0GF3QHCThQOL5
zbshZGlHN/TYsiie9nQ+cojOonXzG/awwpWkRrJaEFe4hMEqq44CtgKMemtZMMYS
bAHSHc7+65uxvPZklxMyqYUEaSTxIGCcWf80i4hZJzf1hNlgrVTp/j9tcs5V6nBC
sQIDAQAB
-----END PUBLIC KEY-----"""


@pytest.fixture
def mock_jwks():
    """Mock JWKS response for testing."""
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key-id",
                "use": "sig",
                "alg": "RS256",
                "n": "4f5wg5l2hKsTeNem_V41fGnJm6gOdrj8ym3rFkEjWT2btYhAz2R6rvAjPOr9EqXQQrAqJqsJFF7dw3NK3F5p6anKpz07hrxhbU9Wye2u5EzIukE7k2D_WjjHVx1pa4196-5EnQJiMuHaFLu5i5gQa4gyNb6d9UlyJZjvCpVKjNqKnKBHrAHGfbdHQQhcbPsKXjKWpliQHC6HrXrs5wPAOiYbxIGxYo5cPiMNU9hBXaLDk_XKHq1MHiKnlqHaLLjfHfqJmyQdtehHFe9KvQs7eKGSxDuHsxF9qatUa9Er4Dlz4AwV5mfpqUXzsjHnMZ_GVHptkHuHuHqk3hABfXsNXw",
                "e": "AQAB"
            }
        ]
    }


def create_jwt_token(
    payload: Dict[str, Any],
    private_key: str,
    algorithm: str = "RS256",
    kid: str = "test-key-id"
) -> str:
    """Create a JWT token for testing."""
    headers = {"kid": kid, "alg": algorithm}
    return jwt.encode(payload, private_key, algorithm=algorithm, headers=headers)


@pytest.fixture
def valid_jwt_payload():
    """Valid JWT payload for testing."""
    now = datetime.utcnow()
    return {
        "sub": "auth0|test-user-123",
        "email": "test@example.com",
        "email_verified": True,
        "aud": "https://test-api.resumematch.com",
        "iss": "https://test.auth0.com/",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "scope": "read:documents write:documents",
        "roles": ["member"],
        "organization_id": "org-456"
    }


@pytest.fixture
def test_organizations():
    """Create test organizations for isolation testing."""
    return {
        "org_a": "org-123",
        "org_b": "org-456",
        "org_c": "org-789"
    }


@pytest.fixture
def mock_auth_gateway():
    """Simulate API Gateway auth processing."""
    class MockAuthGateway:
        def __init__(self):
            self.middleware = Auth0Middleware(
                domain="test.auth0.com",
                api_identifier="https://test-api.resumematch.com"
            )
        
        async def process_request(self, jwt_token: str) -> dict:
            """Simulate gateway processing a request with JWT token."""
            from unittest.mock import Mock
            
            # Mock credentials
            credentials = Mock()
            credentials.credentials = jwt_token
            
            # Process through middleware
            user_context = await self.middleware.verify_token_from_credentials(credentials)
            
            # Return headers that would be passed to internal service
            return {
                "X-User-ID": user_context.user_id,
                "X-User-Email": user_context.email,
                "X-Organization-ID": user_context.organization_id,
                "X-User-Roles": ",".join(user_context.roles),
                "X-User-Scopes": " ".join(user_context.scopes)
            }
    
    return MockAuthGateway()


def create_test_user(user_id: str = None, email: str = None, org_id: str = "DEFAULT", roles: list = None):
    """Create a test user with specified attributes."""
    from shared_auth.models import AuthUser
    from shared_auth.utils import auth0_subject_to_uuid
    
    user_id = user_id or "test-user-123"
    email = email or f"{user_id}@example.com"
    # Use sentinel value to distinguish between None and not provided
    if org_id == "DEFAULT":
        org_id = "org-123"
    roles = roles or ["member"]
    
    return AuthUser(
        user_id=auth0_subject_to_uuid(f"auth0|{user_id}"),
        email=email,
        organization_id=org_id,
        roles=roles,
        auth0_subject=f"auth0|{user_id}",
        email_verified=True,
        scopes=["read:documents", "write:documents"]
    )


def create_valid_jwt_token(user_id: str = None, org_id: str = None, roles: list = None):
    """Create a valid JWT token for testing."""
    import jwt
    from datetime import datetime, timedelta
    
    user_id = user_id or "test-user-123"
    org_id = org_id or "org-123"
    roles = roles or ["member"]
    
    now = datetime.utcnow()
    payload = {
        "sub": f"auth0|{user_id}",
        "email": f"{user_id}@example.com",
        "email_verified": True,
        "aud": "https://test-api.resumematch.com",
        "iss": "https://test.auth0.com/",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "scope": "read:documents write:documents",
        "roles": roles,
        "organization_id": org_id
    }
    
    # Use a simple symmetric key for testing
    return jwt.encode(payload, "test-secret", algorithm="HS256")


class MockDocument:
    """Mock document for testing organization boundaries."""
    def __init__(self, doc_id: str, owner_org: str, content: str = "test content"):
        self.id = doc_id
        self.owner_org = owner_org
        self.content = content
        self.created_at = datetime.utcnow()


def create_test_document(doc_id: str = None, owner_org: str = None, content: str = None):
    """Create a test document with specified attributes."""
    doc_id = doc_id or "doc-123"
    owner_org = owner_org or "org-123"
    content = content or "test document content"
    
    return MockDocument(doc_id, owner_org, content)


@pytest.fixture
def expired_jwt_payload():
    """Expired JWT payload for testing."""
    past_time = datetime.utcnow() - timedelta(hours=2)
    return {
        "sub": "auth0|test-user-123",
        "email": "test@example.com",
        "email_verified": True,
        "aud": "https://test-api.resumematch.com",
        "iss": "https://test.auth0.com/",
        "iat": int((past_time - timedelta(hours=1)).timestamp()),
        "exp": int(past_time.timestamp()),
        "scope": "read:documents write:documents",
        "roles": ["member"]
    }


@pytest.fixture
def invalid_audience_payload():
    """JWT payload with invalid audience for testing."""
    now = datetime.utcnow()
    return {
        "sub": "auth0|test-user-123",
        "email": "test@example.com",
        "email_verified": True,
        "aud": "https://wrong-api.example.com",
        "iss": "https://test.auth0.com/",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "scope": "read:documents write:documents"
    }


@pytest.fixture
def mock_auth0_middleware(auth_config):
    """Mock Auth0Middleware for testing."""
    return Auth0Middleware(
        domain=auth_config["domain"],
        api_identifier=auth_config["api_identifier"],
        algorithms=auth_config["algorithms"]
    )


@pytest.fixture
def mock_request():
    """Mock FastAPI Request object."""
    request = Mock()
    request.headers = {}
    return request


@pytest.fixture
def mock_request_with_auth(mock_request):
    """Mock FastAPI Request with authorization header."""
    mock_request.headers = {
        "authorization": "Bearer valid-jwt-token"
    }
    return mock_request


@pytest.fixture
def mock_request_with_headers(mock_request):
    """Mock FastAPI Request with user context headers."""
    mock_request.headers = {
        "X-User-ID": "123e4567-e89b-12d3-a456-426614174000",
        "X-User-Email": "test@example.com",
        "X-Organization-ID": "org-456",
        "X-User-Roles": "member,staff",
        "X-User-Scopes": "read:documents write:documents"
    }
    return mock_request


@pytest.fixture
def mock_credentials():
    """Mock HTTPAuthorizationCredentials."""
    credentials = Mock()
    credentials.credentials = "valid-jwt-token"
    return credentials


@pytest.fixture
def mock_test_credentials():
    """Mock test token credentials."""
    credentials = Mock()
    credentials.credentials = "mock-test-user-123"
    return credentials


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment
    os.environ["FASTAPI_ENV"] = "testing"
    os.environ["ALLOW_MOCK_TOKENS"] = "true"
    os.environ["AUTH0_DOMAIN"] = "test.auth0.com"
    os.environ["AUTH0_API_IDENTIFIER"] = "https://test-api.resumematch.com"
    os.environ["LOCAL_TEST_TOKEN"] = "local-test-token-123"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_jwks_response(mock_jwks):
    """Mock JWKS HTTP response."""
    response = Mock()
    response.json.return_value = mock_jwks
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def patch_requests_get(mock_jwks_response):
    """Patch requests.get to return mock JWKS."""
    with patch("requests.get", return_value=mock_jwks_response) as mock_get:
        yield mock_get


class MockHTTPException(Exception):
    """Mock HTTPException for testing."""
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


@pytest.fixture(autouse=True)
def patch_http_exception():
    """Patch HTTPException for testing."""
    with patch("shared_auth.middleware.HTTPException", MockHTTPException):
        with patch("shared_auth.dependencies.HTTPException", MockHTTPException):
            yield MockHTTPException
