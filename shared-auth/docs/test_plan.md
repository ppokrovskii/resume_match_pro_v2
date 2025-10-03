# Shared Auth Package - Test Plan

## Overview
**Package**: resume-match-shared-auth  
**Coverage Target**: 100% requirement coverage  
**Test Types**: Unit, Integration, Contract  

## Test Categories

### Unit Tests (AUTH-UNIT-*)

| Test ID | Requirement | Test Case | Priority |
|---------|-------------|-----------|----------|
| AUTH-UNIT-001 | Easy Integration | Package installs via Azure Artifacts | High |
| AUTH-UNIT-002 | Easy Integration | Auth setup with 3 lines of code | High |
| AUTH-UNIT-003 | Easy Integration | FastAPI dependency injection works | High |
| AUTH-UNIT-004 | API Gateway Pattern | JWT token validation with Auth0 JWKS | High |
| AUTH-UNIT-005 | API Gateway Pattern | User context extraction from JWT claims | High |
| AUTH-UNIT-006 | API Gateway Pattern | JWKS caching functionality | Medium |
| AUTH-UNIT-007 | API Gateway Pattern | Standard 401/403 error responses | High |
| AUTH-UNIT-008 | Internal Service Pattern | Extract user from gateway headers | High |
| AUTH-UNIT-009 | Internal Service Pattern | FastAPI dependency injection | High |
| AUTH-UNIT-010 | Internal Service Pattern | Role-based access control | High |
| AUTH-UNIT-011 | Internal Service Pattern | Organization isolation support | High |

### Integration Tests (AUTH-INT-*)

| Test ID | Requirement | Test Case | Priority |
|---------|-------------|-----------|----------|
| AUTH-INT-001 | API Gateway Pattern | Real Auth0 JWT validation | High |
| AUTH-INT-002 | Performance | Token validation < 100ms | High |
| AUTH-INT-003 | Performance | 1000+ concurrent requests | Medium |
| AUTH-INT-004 | Security | Auth0 RS256 JWT validation | High |
| AUTH-INT-005 | Security | User data isolation | High |
| AUTH-INT-006 | Security | Organization boundary enforcement | High |

### Contract Tests (AUTH-CONTRACT-*)

| Test ID | Requirement | Test Case | Priority |
|---------|-------------|-----------|----------|
| AUTH-CONTRACT-001 | User Context | AuthUser model structure | High |
| AUTH-CONTRACT-002 | Dependencies | require_auth dependency | High |
| AUTH-CONTRACT-003 | Dependencies | require_admin dependency | High |
| AUTH-CONTRACT-004 | Dependencies | require_organization dependency | High |

## Test Implementation

### Unit Test Examples

```python
# tests/test_middleware.py
import pytest
from shared_auth import Auth0Middleware, AuthUser
from shared_auth.exceptions import InvalidTokenError

@pytest.mark.asyncio
async def test_valid_jwt_validation():
    """AUTH-UNIT-004: JWT token validation"""
    auth = Auth0Middleware("test.auth0.com", "test-api")
    # Mock JWKS and validate token
    
@pytest.mark.asyncio
async def test_user_context_extraction():
    """AUTH-UNIT-005: User context from JWT"""
    # Test user_id, email, organization_id, roles extraction

def test_role_based_access():
    """AUTH-UNIT-010: Role-based access control"""
    user = AuthUser(user_id="123", email="test@test.com", roles=["admin"])
    assert user.is_admin == True
```

### Integration Test Examples

```python
# tests/test_integration.py
@pytest.mark.integration
async def test_auth0_real_validation():
    """AUTH-INT-001: Real Auth0 integration"""
    # Use test Auth0 tenant for realistic testing

@pytest.mark.performance
async def test_token_validation_performance():
    """AUTH-INT-002: Performance < 100ms"""
    # Measure token validation latency
```

### Mock Utilities

```python
# tests/conftest.py
@pytest.fixture
def mock_auth_user():
    return AuthUser(
        user_id="test-user-123",
        email="test@example.com",
        organization_id="org-456",
        roles=["member"]
    )

@pytest.fixture
def mock_jwt_token():
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."
```

## Requirements Traceability Matrix

| Requirement | Test Cases | Coverage |
|-------------|------------|----------|
| Easy Integration | AUTH-UNIT-001, AUTH-UNIT-002, AUTH-UNIT-003 | ✓ |
| API Gateway Pattern | AUTH-UNIT-004, AUTH-UNIT-005, AUTH-UNIT-006, AUTH-UNIT-007, AUTH-INT-001 | ✓ |
| Internal Service Pattern | AUTH-UNIT-008, AUTH-UNIT-009, AUTH-UNIT-010, AUTH-UNIT-011 | ✓ |
| User Context | AUTH-CONTRACT-001 | ✓ |
| Dependencies | AUTH-CONTRACT-002, AUTH-CONTRACT-003, AUTH-CONTRACT-004 | ✓ |
| Performance | AUTH-INT-002, AUTH-INT-003 | ✓ |
| Security | AUTH-INT-004, AUTH-INT-005, AUTH-INT-006 | ✓ |
| Business Rules | AUTH-UNIT-010, AUTH-UNIT-011, AUTH-INT-005, AUTH-INT-006 | ✓ |

**Total Requirements**: 8  
**Total Test Cases**: 17  
**Coverage**: 100% ✓

## Test Execution

### Local Testing
```bash
cd shared-auth
pytest tests/ --cov=src/shared_auth --cov-report=html
```

### CI/CD Testing
```yaml
# .github/workflows/test-shared-auth.yml
- name: Run tests
  run: |
    cd shared-auth
    pytest tests/ --cov=src/shared_auth --cov-report=xml
    pytest tests/ --benchmark-only  # Performance tests
```

### Test Data
- Mock JWT tokens for different scenarios
- Test Auth0 tenant for integration tests
- Sample user contexts for all role types

## Performance Testing

### Benchmarks
- Token validation latency: < 100ms (95th percentile)
- Memory usage: < 10MB per service instance
- Concurrent requests: 1000+ requests/second

### Load Testing
```python
@pytest.mark.benchmark
def test_token_validation_benchmark(benchmark):
    """Performance benchmark for token validation"""
    result = benchmark(auth.verify_token, test_token)
    assert result.user_id == "test-user"
```

## Security Testing

### Test Scenarios
- Invalid JWT tokens
- Expired tokens
- Malformed tokens
- Missing required claims
- Role escalation attempts
- Organization boundary violations

## Test Environment

### Dependencies
```toml
[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-benchmark>=4.0.0",
    "httpx>=0.25.0",
    "pytest-mock>=3.11.0"
]
```

### Test Configuration
```python
# tests/conftest.py
@pytest.fixture
def auth_config():
    return {
        "domain": "test.auth0.com",
        "api_identifier": "test-api",
        "algorithms": ["RS256"]
    }
```

## Acceptance Criteria

### Test Completion Criteria
- All unit tests pass (100%)
- Integration tests pass with real Auth0
- Performance benchmarks meet requirements
- Security tests validate all attack vectors
- 100% requirement coverage achieved
- No critical security vulnerabilities
