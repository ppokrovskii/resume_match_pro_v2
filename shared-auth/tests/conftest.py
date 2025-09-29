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
    return """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA4f5wg5l2hKsTeNem/V41fGnJm6gOdrj8ym3rFkEjWT2btYhA
z2R6rvAjPOr9EqXQQrAqJqsJFF7dw3NK3F5p6anKpz07hrxhbU9Wye2u5EzIukE7
k2D/WjjHVx1pa4196+5EnQJiMuHaFLu5i5gQa4gyNb6d9UlyJZjvCpVKjNqKnKBH
rAHGfbdHQQhcbPsKXjKWpliQHC6HrXrs5wPAOiYbxIGxYo5cPiMNU9hBXaLDk/XK
Hq1MHiKnlqHaLLjfHfqJmyQdtehHFe9KvQs7eKGSxDuHsxF9qatUa9Er4Dlz4AwV
5mfpqUXzsjHnMZ/GVHptkHuHuHqk3hABfXsNXwIDAQABAoIBAEYhObhC0fVdH24P
jh4/jjDUoEkEiEqp7kZ6T4Zc4KWDcEcsLiXhXobykJhidG/b6faUwcKZAbYxaaa0
Wy2u1hUYieUnzGPUBpbE2hRhFYs9/l2YQgQNMVtSB/IpNxnfnvqaXpbHDKFpG2AN
2o9qXRRJON2V3VvAXxRTsQs/P1JpAOI5B2yyHkqDTGR5+3Jh5fxFqHbmJ2HuMfMI
kVK4fEHyqFsF6NUhfvzYy69l0t2wyWZrVA7v/sO0AOznmDbduHBBlaOYkn9VBOb7
rjaulHsUHMiI22P9Xyp9J1qIuz7zZA8OQh4BQANCjV/EOE7kKaF3QmDNRRhqeQxy
ovxfuPECgYEA+vIxr4Fu4fyaDNy/wfWjiRCRx1V/H9pyoAiIYeiZpNp4fv4g5+ls
R8qdl7TC1m9l0l8IkqhPycE2k5LTmS/P7p+ARTbzI3/QQEh8Ck+gslcHrlxrUEyr
7L7/OTaLxjUZqK8eJnyeVyh+oz+KU/+HLp22HKxtLbfbx91WLMF1k9MCgYEA5x8q
Mf/FgQObgx+W6uCiuBiKwjQpIMi8hkr80b+CF+OZRQqJ2LiXpqhI1qGXiOaLjPXR
+dEzSqHBzpnTMRBe00CjBwLxz/cL8uGRzYlBUBVXfA5g4A8/kxgUdnRYfp2lPkmz
6wKBgGa3VGI2Uahkz/jc7p8i0VWwPgGRQ+6Uqmqage8GCJqbVbGh5Mn5Qx0YtGAd
n0/dMUrLu9Oz7nkqAA5qQJ0wXm0c/oeRNdyenlP0NDtfSVBnbRxhdWy2ArHjKAAa
rAhGxbDaMVvY7dhqRoKuNECrNYL5+Iw3flaABo4h5Lz0paTzAoGBAL9qUdY2/5n0
WKmfFx9e7abfxLOHI4HcBuJiLI8vhPdHlE5d4sgE0nqwxHPD6t8+LQzGxS2+ArTI
kOvRu4LrTXbmzxB0raUeNTOgprKjUBMjV8S/6aFHd+Zx5Qg5vTm9jGMmHgxGBhJl
AoGAVqFTXZp6ea5s+kKBHAqhQzkmkDqGiuHTXU1gn2xHhUrw5C1TtlI2o4JGHZK3
om+SUW+Pd2lh8dNqGTLV5NWFM0dwNdjZSmliSaHIjru+Z4XgPB+/wuuO24kt5+TO
Q3D+XNBG4JqMXGbfDaUVJPAcvvXBH2y5Pk8+5+mwz5+FQMQ=
-----END RSA PRIVATE KEY-----"""


@pytest.fixture
def rsa_public_key():
    """RSA public key for JWT verification in tests."""
    return """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4f5wg5l2hKsTeNem/V41
fGnJm6gOdrj8ym3rFkEjWT2btYhAz2R6rvAjPOr9EqXQQrAqJqsJFF7dw3NK3F5p
6anKpz07hrxhbU9Wye2u5EzIukE7k2D/WjjHVx1pa4196+5EnQJiMuHaFLu5i5gQ
a4gyNb6d9UlyJZjvCpVKjNqKnKBHrAHGfbdHQQhcbPsKXjKWpliQHC6HrXrs5wPA
OiYbxIGxYo5cPiMNU9hBXaLDk/XKHq1MHiKnlqHaLLjfHfqJmyQdtehHFe9KvQs7
eKGSxDuHsxF9qatUa9Er4Dlz4AwV5mfpqUXzsjHnMZ/GVHptkHuHuHqk3hABfXsN
XwIDAQAB
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
