# Shared Auth Package - Requirements

## Overview
Reusable Auth0 JWT middleware for all Resume Match Pro microservices. Eliminates code duplication and ensures consistent authentication.

## Core Requirements

### 1. Easy Integration
**As a** developer  
**I want** to add authentication with minimal code  
**So that** I can focus on business logic

**Acceptance Criteria:**
- ✅ Install via `uv add resume-match-shared-auth --index-url https://pkgs.dev.azure.com/resumematch/_packaging/shared-packages/pypi/simple/`
- ✅ Setup requires max 3 lines of code
- ✅ FastAPI dependency injection out of the box
- ✅ No manual JWT/JWKS implementation needed

### 2. API Gateway Pattern
**As an** API Gateway  
**I want** to validate JWT tokens once  
**So that** internal services don't need token validation

**Acceptance Criteria:**
- ✅ Full JWT validation at gateway only
- ✅ User context passed via HTTP headers
- ✅ JWKS caching for performance
- ✅ Standard 401/403 error responses

### 3. Internal Service Pattern
**As an** internal service  
**I want** to trust the API Gateway  
**So that** I get user context without token overhead

**Acceptance Criteria:**
- ✅ Extract user from gateway headers
- ✅ FastAPI dependency injection
- ✅ Role-based access control
- ✅ Organization isolation support

## User Context

```python
@dataclass
class AuthUser:
    user_id: str
    email: str
    organization_id: Optional[str]
    roles: List[str]
```

## Dependencies

```python
# Available dependencies
require_auth          # Any authenticated user
require_admin         # Admin role required
require_organization  # Organization member required
```

## Performance Requirements

- Token validation: < 100ms (95th percentile)
- Memory usage: < 10MB per service
- Support 1000+ concurrent requests
- JWKS cache with TTL

## Security Requirements

- Auth0 RS256 JWT validation
- User data isolation
- Organization boundary enforcement
- No sensitive data in error messages
- Audit logging for auth events

## Business Rules

1. **API Gateway Only**: Only gateway validates JWT tokens
2. **Trust Internal**: Internal services trust gateway headers
3. **User Isolation**: Users see only their own data
4. **Organization Isolation**: Complete org separation
5. **Role-Based Access**: Declarative role checking

