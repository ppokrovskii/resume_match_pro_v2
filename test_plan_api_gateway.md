# API Gateway - Test Plan

## Service Overview
**Service**: API Gateway  
**Responsibilities**: Request routing, authentication middleware, rate limiting, CORS handling, response aggregation  
**Tech Stack**: Python 3.11+, Flask, Supabase Auth, Redis  

---

## Test Categories

### 1. Unit Tests (GW-UNIT)
| Test ID | Component | Test Case | Priority |
|---------|-----------|-----------|----------|
| GW-U-001 | auth_middleware.py | Validate JWT tokens | High |
| GW-U-002 | auth_middleware.py | Reject invalid JWT tokens | High |
| GW-U-003 | auth_middleware.py | Handle expired tokens | High |
| GW-U-004 | auth_middleware.py | Extract user context from JWT | High |
| GW-U-005 | cors_middleware.py | Set CORS headers correctly | High |
| GW-U-006 | cors_middleware.py | Handle preflight requests | High |
| GW-U-007 | rate_limiter.py | Enforce rate limits per user | High |
| GW-U-008 | rate_limiter.py | Allow requests within limits | High |
| GW-U-009 | request_validator.py | Validate request schemas | High |
| GW-U-010 | response_formatter.py | Format error responses | High |

### 2. Integration Tests (GW-INT)
| Test ID | Component | Test Case | Priority |
|---------|-----------|-----------|----------|
| GW-I-001 | service_registry.py | Route to Document Service | High |
| GW-I-002 | service_registry.py | Route to AI Service | High |
| GW-I-003 | service_registry.py | Handle service unavailability | High |
| GW-I-004 | proxy.py | Forward requests with headers | High |
| GW-I-005 | proxy.py | Aggregate responses from services | Medium |
| GW-I-006 | Redis | Store rate limit counters | High |
| GW-I-007 | Supabase Auth | Validate tokens with Supabase | High |

### 3. API Tests (GW-API)
| Test ID | Endpoint | Test Case | Priority |
|---------|----------|-----------|----------|
| GW-A-001 | GET /health | Health check endpoint | High |
| GW-A-002 | POST /api/v1/documents/* | Route to Document Service | High |
| GW-A-003 | POST /api/v1/ai/* | Route to AI Service | High |
| GW-A-004 | All endpoints | Authentication required | High |
| GW-A-005 | All endpoints | CORS headers present | High |
| GW-A-006 | All endpoints | Rate limiting enforced | High |
| GW-A-007 | Invalid routes | 404 error handling | Medium |
| GW-A-008 | OPTIONS requests | Preflight handling | Medium |
| GW-A-009 | Malformed requests | Request validation | High |
| GW-A-010 | Service errors | Error propagation | High |

### 4. Performance Tests (GW-PERF)
| Test ID | Scenario | Test Case | Target |
|---------|----------|-----------|--------|
| GW-P-001 | Request Routing | Gateway response time | <100ms |
| GW-P-002 | Authentication | JWT validation time | <50ms |
| GW-P-003 | Rate Limiting | Rate limit check time | <10ms |
| GW-P-004 | Concurrent Requests | 100 concurrent requests | <2s |
| GW-P-005 | Service Proxy | End-to-end request time | <3s |

### 5. Security Tests (GW-SEC)
| Test ID | Security Aspect | Test Case | Priority |
|---------|----------------|-----------|----------|
| GW-S-001 | Authentication | Block requests without tokens | High |
| GW-S-002 | Authentication | Block requests with invalid tokens | High |
| GW-S-003 | Authorization | Enforce user-level access control | High |
| GW-S-004 | Rate Limiting | Prevent abuse/DDoS | High |
| GW-S-005 | Input Validation | Sanitize request inputs | High |
| GW-S-006 | CORS Security | Restrict cross-origin requests | High |
| GW-S-007 | Headers Security | Remove sensitive headers | Medium |

### 6. Error Handling Tests (GW-ERROR)
| Test ID | Error Scenario | Test Case | Priority |
|---------|---------------|-----------|----------|
| GW-E-001 | Service Timeout | Handle downstream timeouts | High |
| GW-E-002 | Service Error | Handle 500 errors from services | High |
| GW-E-003 | Network Error | Handle connection failures | High |
| GW-E-004 | Invalid JSON | Handle malformed request bodies | High |
| GW-E-005 | Rate Limit Exceeded | Return 429 status code | High |
| GW-E-006 | Auth Service Down | Handle Supabase Auth failures | High |

---

## Test Data Requirements
- Valid and invalid JWT tokens from Supabase Auth
- Test user accounts with different permissions
- Rate limiting test scenarios with burst requests
- Mock service responses for error conditions

## Mock Strategy
- **DO NOT MOCK**: Supabase Auth (use test project)
- **DO NOT MOCK**: Redis (use local instance)
- **Mock**: Downstream services for error testing
- **Mock**: Network failures for resilience testing

## Coverage Target
**Minimum**: 80% code coverage  
**Critical paths**: 100% coverage (authentication, routing, error handling)

## Test Environment
- Local Redis instance for rate limiting
- Supabase test project for authentication
- Mock HTTP servers for downstream services
- Load testing tools (Locust) for performance tests






