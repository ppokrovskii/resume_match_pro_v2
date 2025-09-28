# API Gateway - Solution Design

## Service Overview

**Purpose**: Centralized API gateway for microservices orchestration  
**Technology**: Python 3.11+ with Flask  
**Deployment**: Azure Functions (Consumption Plan)  
**Pattern**: Gateway Aggregation + Backend for Frontend (BFF)  
**Auth**: Supabase Auth JWT validation  

## Responsibilities

- Request routing and load balancing
- Authentication and authorization
- Rate limiting and throttling
- CORS handling
- Response aggregation
- API versioning
- Circuit breaker implementation
- Request/response transformation

## Architecture

### Core Components

```
api-gateway/
├── app.py                      # Flask app entry point
├── middleware/
│   ├── auth_middleware.py     # JWT validation
│   ├── cors_middleware.py     # CORS handling
│   ├── rate_limiter.py        # Rate limiting
│   └── circuit_breaker.py     # Circuit breaker
├── routes/
│   ├── proxy.py               # Service proxy routes
│   ├── health.py              # Health checks
│   └── aggregated.py          # Aggregated endpoints
├── services/
│   ├── service_registry.py    # Service discovery
│   ├── auth_client.py         # Auth service client
│   ├── document_client.py     # Document service client
│   └── ai_client.py           # AI service client
├── utils/
│   ├── request_validator.py   # Input validation
│   ├── response_formatter.py  # Response formatting
│   └── error_handler.py       # Error handling
└── tests/                     # Unit tests
```

## API Routing

### Authentication (Handled by Supabase)
- JWT token validation using Supabase client
- User context extraction from JWT claims
- No separate auth service needed

### Document Routes (`/api/v1/documents/*`)
- Proxy to document-service
- Authentication required
- File upload size validation
- Multipart form handling

### AI Routes (`/api/v1/ai/*`)
- Proxy to ai-service
- Authentication required
- Request throttling for expensive operations
- Response caching

### Aggregated Routes (`/api/v1/dashboard/*`)
- `GET /dashboard/overview` - User dashboard data
- `GET /dashboard/matches/{cv_id}` - CV matches with details
- `POST /dashboard/search` - Unified search across services

## Middleware Stack

### 1. CORS Middleware
```python
CORS_CONFIG = {
    "origins": ["http://localhost:3000", "https://app.resumematch.pro"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["X-Total-Count", "X-Rate-Limit-Remaining"],
    "supports_credentials": True
}
```

### 2. Authentication Middleware
- JWT token validation
- User context extraction
- Organization membership verification
- Role-based access control

### 3. Rate Limiting Middleware
```python
RATE_LIMITS = {
    "default": "100/hour",
    "auth": "10/minute",
    "upload": "20/hour",
    "ai": "50/hour",
    "search": "200/hour"
}
```

### 4. Circuit Breaker
- Service health monitoring
- Automatic failover
- Graceful degradation
- Recovery detection

## Service Integration

### Service Discovery
```python
@dataclass
class ServiceConfig:
    name: str
    base_url: str
    health_endpoint: str
    timeout: int
    retry_count: int
    circuit_breaker_threshold: int
```

### HTTP Client Configuration
- Connection pooling
- Timeout handling
- Retry logic with exponential backoff
- Request/response logging

### Service Clients

#### Auth Service Client
```python
class AuthServiceClient:
    async def validate_token(self, token: str) -> dict
    async def get_user_info(self, user_id: str) -> dict
    async def check_organization_access(self, user_id: str, org_id: str) -> bool
```

#### Document Service Client
```python
class DocumentServiceClient:
    async def get_user_documents(self, user_id: str, doc_type: str) -> List[dict]
    async def upload_document(self, user_id: str, file_data: bytes) -> dict
    async def delete_document(self, user_id: str, doc_id: str) -> bool
```

#### AI Service Client
```python
class AIServiceClient:
    async def calculate_matches(self, cv_id: str, jd_ids: List[str]) -> List[dict]
    async def semantic_search(self, query: str, user_id: str) -> List[dict]
    async def generate_embeddings(self, text: str) -> List[float]
```

## Request/Response Transformation

### Request Enrichment
- Add user context from JWT
- Inject correlation IDs
- Add request timestamps
- Validate input schemas

### Response Standardization
```python
STANDARD_RESPONSE = {
    "success": bool,
    "data": any,
    "error": {
        "code": str,
        "message": str,
        "details": dict
    },
    "meta": {
        "request_id": str,
        "timestamp": str,
        "version": str
    }
}
```

## Aggregated Endpoints

### Dashboard Overview
```python
async def get_dashboard_overview(user_id: str):
    # Parallel service calls
    documents = await document_client.get_user_documents(user_id)
    recent_matches = await ai_client.get_recent_matches(user_id)
    
    return {
        "document_count": len(documents),
        "recent_matches": recent_matches,
        "activity_summary": calculate_activity_summary(documents)
    }
```

### Unified Search
```python
async def unified_search(query: str, user_id: str, filters: dict):
    # Search across document and AI services
    doc_results = await document_client.search_documents(query, user_id)
    ai_results = await ai_client.semantic_search(query, user_id)
    
    return merge_and_rank_results(doc_results, ai_results)
```

## Error Handling

### Error Categories
- **Client Errors (4xx)**: Validation, authentication, authorization
- **Server Errors (5xx)**: Service unavailable, internal errors
- **Gateway Errors**: Timeout, circuit breaker, rate limiting

### Error Response Format
```python
{
    "error": {
        "code": "SERVICE_UNAVAILABLE",
        "message": "Document service is temporarily unavailable",
        "details": {
            "service": "document-service",
            "retry_after": 30,
            "correlation_id": "abc-123"
        }
    },
    "meta": {
        "request_id": "req-456",
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

## Dependencies

### Core Dependencies
```
flask==3.0.0
flask-cors==4.0.0
supabase==2.0.0
aiohttp==3.9.0
redis==5.0.0
pydantic==2.5.0
opentelemetry-api==1.21.0
opentelemetry-instrumentation-flask==0.42b0
```

### Monitoring Dependencies
```
prometheus-client==0.19.0
azure-monitor-opentelemetry==1.1.0
```

## Configuration

### Environment Variables
- `AUTH_SERVICE_URL` - Authentication service endpoint
- `DOCUMENT_SERVICE_URL` - Document service endpoint
- `AI_SERVICE_URL` - AI service endpoint
- `REDIS_URL` - Redis cache connection string
- `JWT_SECRET_KEY` - JWT validation key
- `RATE_LIMIT_STORAGE` - Rate limiting backend

### Service Configuration
```python
SERVICES = {
    "auth": {
        "url": os.getenv("AUTH_SERVICE_URL"),
        "timeout": 10,
        "retries": 3,
        "circuit_breaker_threshold": 5
    },
    "document": {
        "url": os.getenv("DOCUMENT_SERVICE_URL"),
        "timeout": 30,  # Higher for file operations
        "retries": 2,
        "circuit_breaker_threshold": 3
    },
    "ai": {
        "url": os.getenv("AI_SERVICE_URL"),
        "timeout": 60,  # Higher for AI operations
        "retries": 1,
        "circuit_breaker_threshold": 2
    }
}
```

## Caching Strategy

### Response Caching
- Cache GET requests with TTL
- Cache search results
- Cache user profile data
- Invalidate on relevant updates

### Cache Keys
```python
CACHE_PATTERNS = {
    "user_profile": "user:{user_id}:profile",
    "documents": "user:{user_id}:documents:{type}",
    "matches": "user:{user_id}:matches:{cv_id}",
    "search": "search:{query_hash}:{user_id}"
}
```

## Security Implementation

### Request Validation
- Input sanitization
- Schema validation
- File type validation
- Size limit enforcement

### Security Headers
```python
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}
```

## Monitoring & Observability

### Metrics Collection
- Request count by endpoint
- Response times by service
- Error rates
- Circuit breaker states
- Cache hit rates

### Distributed Tracing
- Request correlation IDs
- Service call tracing
- Performance bottleneck identification
- Error propagation tracking

### Health Checks
```python
async def health_check():
    services_status = {}
    for service_name, client in service_clients.items():
        try:
            await client.health_check()
            services_status[service_name] = "healthy"
        except Exception:
            services_status[service_name] = "unhealthy"
    
    return {
        "status": "healthy" if all(s == "healthy" for s in services_status.values()) else "degraded",
        "services": services_status
    }
```

## Performance Optimization

### Connection Management
- HTTP connection pooling
- Keep-alive connections
- Connection timeout optimization
- DNS caching

### Async Processing
- Async/await for I/O operations
- Parallel service calls
- Non-blocking request handling
- Background task processing

## Testing Strategy

### Unit Tests
- Middleware functionality
- Service client operations
- Error handling logic
- Request/response transformation

### Integration Tests
- End-to-end request flows
- Service integration
- Circuit breaker behavior
- Rate limiting functionality

### Load Testing
- Concurrent request handling
- Service degradation scenarios
- Circuit breaker triggering
- Performance under load
