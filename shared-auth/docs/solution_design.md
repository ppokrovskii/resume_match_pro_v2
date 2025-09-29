# Shared Auth Package - Solution Design

## Overview

**Purpose**: Reusable Auth0 JWT middleware for FastAPI microservices  
**Tech Stack**: Python 3.11+, FastAPI, Auth0 JWT  
**Distribution**: GitHub Packages  

## Architecture

```
shared-auth/
├── src/shared_auth/
│   ├── middleware.py    # Auth0 middleware
│   ├── models.py        # User models
│   └── exceptions.py    # Auth exceptions
├── tests/
└── pyproject.toml
```

## Usage Patterns

### API Gateway (Full JWT Validation)
```python
from shared_auth import Auth0Middleware

auth = Auth0Middleware(domain=AUTH0_DOMAIN, api_identifier=API_IDENTIFIER)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    user = await auth.verify_token_from_request(request)
    request.state.user = user
    return await call_next(request)
```

### Internal Services (Trust Gateway)
```python
from shared_auth import get_user_from_headers, require_auth

@app.middleware("http")
async def trust_gateway(request: Request, call_next):
    user = get_user_from_headers(request.headers)
    request.state.user = user
    return await call_next(request)

@app.get("/documents")
async def list_docs(user = Depends(require_auth)):
    return get_user_documents(user.user_id)
```

## User Model

```python
@dataclass
class AuthUser:
    user_id: str
    email: str
    organization_id: Optional[str]
    roles: List[str]
    
    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles
```

## Dependencies

```python
# FastAPI dependencies
async def require_auth(user: AuthUser = Depends(auth.get_current_user)) -> AuthUser
async def require_admin(user: AuthUser = Depends(require_auth)) -> AuthUser
async def require_organization_member(user: AuthUser = Depends(require_auth)) -> AuthUser
```

## Configuration

```bash
# Environment variables
AUTH0_DOMAIN=tenant.auth0.com
AUTH0_API_IDENTIFIER=https://api.resumematch.com/service-name
```

```toml
# pyproject.toml
[project]
name = "resume-match-shared-auth"
dependencies = [
    "fastapi>=0.104.1",
    "python-jose[cryptography]>=3.3.0",
    "requests>=2.31.0"
]
```

## Installation

```bash
# In microservices
uv add resume-match-shared-auth

# Local development
cd shared-auth && uv pip install -e .
```
