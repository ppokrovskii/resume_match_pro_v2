# Resume Match Pro AI - Solution Design

## Architecture Overview

**Architecture Pattern**: Event-Driven Serverless Microservices  
**Language**: Python 3.11+ (Backend), TypeScript (Frontend)  
**Framework**: FastAPI with Azure Functions  
**Package Manager**: uv  
**Infrastructure**: Azure-native with PostgreSQL  
**Frontend**: React with TypeScript  
**Authentication**: Auth0 (managed service)  
**Message Queue**: Azure Storage Queues  
**Deployment**: Infrastructure as Code (Terraform)  
**Observability**: OpenTelemetry for distributed tracing  

## Microservices Architecture

### Service Decomposition

The system is decomposed into 6 core components:

1. **Frontend Application** (`frontend/`) - React TypeScript SPA
2. **API Gateway** (`api-gateway/`) - Request routing and auth validation
3. **Document Service** (`document-service/`) - Document CRUD and storage
4. **AI Text Extract Service** (`ai-text-extract/`) - Text extraction and file type detection
5. **Matches Service** (`matches-service/`) - Match results CRUD and orchestration
6. **AI Match Service** (`ai-match/`) - Match score calculation

**Note**: Authentication is handled by Auth0 (managed service)

### Service Communication

- **Synchronous**: REST APIs for user-facing operations (via API Gateway)
- **Asynchronous**: Azure Storage Queues for event-driven processing
- **Authentication**: Auth0 JWT validation at API Gateway only
- **Service-to-Service**: Trusted internal communication (no auth between services)
- **Observability**: OpenTelemetry for distributed tracing

## Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand (lightweight)
- **UI Library**: Tailwind CSS + Headless UI
- **Auth**: Supabase Auth client
- **Hosting**: Vercel (free tier) or Netlify

### Backend Services
- **Runtime**: Python 3.11+
- **Web Framework**: FastAPI (async, high-performance)
- **Package Management**: uv (fast Python package installer)
- **Serverless**: Azure Functions (consumption plan)
- **Container Runtime**: Support for both Azure Functions and Container Apps

### Authentication & User Management
- **Auth Service**: Auth0 (managed service)
- **JWT Validation**: Auth0 JWT with RS256
- **User Database**: PostgreSQL (user profiles and organizations)
- **Shared Auth**: Reusable auth middleware package

### Data Layer
- **Document Metadata**: PostgreSQL with proper indexing
- **File Storage**: Azure Blob Storage
- **Message Queue**: Azure Storage Queues
- **Cache**: Redis (for performance optimization)

### AI/ML Stack
- **Text Extraction**: Azure AI Document Intelligence + local processing
- **Embeddings**: Azure OpenAI (pay-per-use)
- **File Type Detection**: Azure OpenAI GPT models
- **Vector Similarity**: Custom similarity algorithms

### Infrastructure & DevOps
- **IaC**: Terraform (multi-cloud flexibility)
- **Observability**: OpenTelemetry + Jaeger (self-hosted)
- **CI/CD**: GitHub Actions (free tier)
- **Monitoring**: Basic logging + health checks

## Service Details

### 1. Frontend Application (`frontend/`)

**Technology Stack:**
- React 18 with TypeScript
- Auth0 client integration
- Tailwind CSS + Headless UI
- Zustand for state management

**Key Features:**
- Drag-and-drop file uploads
- Dual-pane CV/JD interface
- Real-time search and filtering
- Responsive design

**API Integration:**
- All requests go through API Gateway
- Auth0 JWT tokens for authentication
- Real-time updates via polling or WebSockets

### 2. API Gateway (`api-gateway/`)

**Responsibilities:**
- Single entry point for all frontend requests
- Auth0 JWT token validation
- Request routing to appropriate microservices
- CORS handling and rate limiting
- Response aggregation for complex queries

**Technology Stack:**
- FastAPI with Azure Functions
- Auth0 JWT validation
- Request/response transformation
- OpenTelemetry tracing

**Authentication Pattern:**
```python
# Only API Gateway validates JWT tokens
# Internal services trust the gateway
@app.middleware("http")
async def add_user_context(request: Request, call_next):
    # Validate JWT and extract user info
    user_context = await verify_auth0_token(request)
    # Add user context to internal service calls
    request.state.user = user_context
    return await call_next(request)
```

### 3. Document Service (`document-service/`) - **IMPLEMENTED**

**Responsibilities:**
- File upload/download management
- Document parsing (PDF/Word)
- Text extraction
- Metadata storage
- File validation

**Key Components:**
```
document-service/
├── app.py
├── routes/
│   ├── documents.py      # Document CRUD
│   └── upload.py         # File upload handling
├── models/
│   ├── document.py       # Document metadata
│   └── upload_session.py # Upload tracking
├── services/
│   ├── document_service.py    # Core document logic
│   ├── parser_service.py      # PDF/Word parsing
│   └── storage_service.py     # Blob storage interface
└── utils/
    ├── file_validators.py     # File validation
    └── text_extractors.py     # Text extraction
```

**Endpoints:**
- `POST /documents/upload` - Upload documents
- `GET /documents` - List user documents
- `GET /documents/{id}` - Get document details
- `GET /documents/{id}/download` - Download file
- `DELETE /documents/{id}` - Delete document

### 4. AI Text Extract Service (`ai-text-extract/`)

**Responsibilities:**
- Listen to `document.created` events from Azure Storage Queues
- Extract text from PDF/Word documents
- Detect document type (CV vs Job Description) using AI
- Extract structured data (role, skills, features)
- Update document metadata via Document Service API

**Technology Stack:**
- FastAPI with Azure Functions
- Azure AI Document Intelligence for PDF processing
- python-docx for Word document processing
- Azure OpenAI for file type detection and data extraction
- Shared auth middleware for API calls

### 5. Matches Service (`matches-service/`)

**Responsibilities:**
- Match results CRUD operations
- Listen to `document.properties.updated` events
- Find documents that need match score calculation
- Orchestrate match calculation requests
- Store and serve match results

### 6. AI Match Service (`ai-match/`)

**Responsibilities:**
- Embedding generation
- Similarity calculations
- Match score computation
- Semantic search
- Vector operations

**Key Components:**
```
ai-service/
├── app.py
├── routes/
│   ├── embeddings.py     # Embedding operations
│   ├── matching.py       # Match calculations
│   └── search.py         # Semantic search
├── models/
│   ├── embedding.py      # Embedding data model
│   └── match_result.py   # Match results
├── services/
│   ├── embedding_service.py   # Azure OpenAI integration
│   ├── matching_service.py    # Similarity calculations
│   └── search_service.py      # Vector search
└── utils/
    ├── vector_utils.py        # Vector operations
    └── similarity_metrics.py  # Distance calculations
```

**Endpoints:**
- `POST /ai/embeddings` - Generate embeddings
- `POST /ai/match` - Calculate match scores
- `POST /ai/search` - Semantic search
- `GET /ai/matches/{cv_id}/{jd_id}` - Get specific match

### 4. API Gateway (`api-gateway/`)

**Responsibilities:**
- Request routing
- Authentication middleware
- Rate limiting
- CORS handling
- Response aggregation

**Key Components:**
```
api-gateway/
├── app.py
├── middleware/
│   ├── auth_middleware.py     # JWT validation
│   ├── cors_middleware.py     # CORS handling
│   └── rate_limiter.py        # Rate limiting
├── routes/
│   ├── proxy.py              # Service proxy
│   └── health.py             # Health checks
├── services/
│   └── service_registry.py   # Service discovery
└── utils/
    ├── request_validator.py   # Input validation
    └── response_formatter.py  # Response formatting
```

## Event-Driven Architecture

### Message Flow

```
1. Frontend → API Gateway → Document Service
   ↓ (document.created event)
2. AI Text Extract Service → Document Service API
   ↓ (document.properties.updated event)  
3. Matches Service → AI Match Service
   ↓ (match.calculation.requested events)
4. AI Match Service → Matches Service API
   ↓ (results)
5. Frontend ← API Gateway ← Matches Service
```

### Event Schemas

#### Document Created Event
```json
{
  "event_type": "document.created",
  "document_id": "uuid",
  "content_type": "application/pdf",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Document Properties Updated Event
```json
{
  "event_type": "document.properties.updated", 
  "document": {
    "id": "uuid",
    "file_type": "cv",
    "text_content": "extracted text...",
    "role": "Python Developer",
    "features": [...]
  }
}
```

#### Match Calculation Requested Event
```json
{
  "event_type": "match.calculation.requested",
  "cv_document": { /* full CV document data */ },
  "jd_document": { /* full JD document data */ },
  "request_id": "uuid"
}
```

### Azure Storage Queues Configuration

- **Queue Names**: `document-events`, `match-events`
- **Message TTL**: 7 days
- **Dead Letter Queue**: Enabled for failed processing
- **Visibility Timeout**: 30 seconds
- **Max Delivery Count**: 3

## Shared Authentication Middleware

### Reusable Auth Package

Create a shared Python package for all microservices:

```python
# shared-auth/auth_middleware.py
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer
import jwt
import requests
from functools import lru_cache

class Auth0Middleware:
    def __init__(self, domain: str, api_identifier: str):
        self.domain = domain
        self.api_identifier = api_identifier
        self.security = HTTPBearer(auto_error=False)
    
    @lru_cache()
    def get_jwks(self):
        """Cache JWKS for performance"""
        response = requests.get(f"https://{self.domain}/.well-known/jwks.json")
        return response.json()
    
    async def verify_token(self, credentials = Depends(security)):
        """Verify Auth0 JWT token"""
        # Implementation from document-service/middleware/auth0_middleware.py
        pass

# Usage in each microservice:
from shared_auth import Auth0Middleware

auth = Auth0Middleware(
    domain=os.getenv("AUTH0_DOMAIN"),
    api_identifier=os.getenv("AUTH0_API_IDENTIFIER")
)

@app.get("/protected")
async def protected_route(user = Depends(auth.verify_token)):
    return {"user": user}
```

### API Gateway Pattern

Only API Gateway validates JWT tokens:

```python
# api-gateway: Full JWT validation
@app.middleware("http") 
async def auth_middleware(request: Request, call_next):
    user = await verify_auth0_token(request)
    # Add user context to internal service calls
    request.state.user = user
    return await call_next(request)

# Internal services: Trust the gateway
@app.middleware("http")
async def trust_gateway(request: Request, call_next):
    # Extract user context from gateway headers
    user_id = request.headers.get("X-User-ID")
    org_id = request.headers.get("X-Organization-ID") 
    request.state.user = {"user_id": user_id, "org_id": org_id}
    return await call_next(request)
```

## Infrastructure Design (Cost-Optimized MVP)

### Azure-Native Architecture

**Core Azure Services:**
- Azure Functions (consumption plan) - Serverless compute
- Azure PostgreSQL Flexible Server - Database
- Azure Blob Storage - File storage
- Azure Storage Queues - Message queues
- Azure OpenAI - AI/ML services
- Azure AI Document Intelligence - Text extraction

**Authentication & Identity:**
- Auth0 (managed service) - JWT authentication
- PostgreSQL - User profiles and organizations

**Development & Monitoring:**
- Frontend: Vercel/Netlify free tier
- Monitoring: Self-hosted Jaeger + OpenTelemetry
- Cache: Azure Redis Cache (basic tier)

**Infrastructure as Code (Terraform):**
```
infrastructure/
├── main.tf                 # Main configuration
├── modules/
│   ├── azure-functions.tf  # Azure Functions
│   ├── openai.tf          # Azure OpenAI
│   └── monitoring.tf      # Basic monitoring
├── variables.tf           # Variables
├── outputs.tf             # Outputs
└── terraform.tfvars.example
```

### Cost Optimization Strategy

**Free Tier Usage:**
- Supabase: 500MB database, 1GB storage, 2GB bandwidth
- Vercel: Unlimited personal projects
- GitHub Actions: 2000 minutes/month
- Azure Functions: 1M requests/month free

**Pay-per-use:**
- Azure OpenAI: ~$0.0001 per 1K tokens
- Additional Supabase usage: $25/month when needed

**Total MVP Cost: $0-50/month**

## Data Models

### User Data (Supabase Auth + PostgreSQL)
```sql
-- Handled by Supabase Auth
-- Additional user profile data in PostgreSQL:
CREATE TABLE user_profiles (
  id UUID REFERENCES auth.users PRIMARY KEY,
  organization_id UUID,
  role TEXT DEFAULT 'member',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Document Metadata (Supabase PostgreSQL)
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  organization_id UUID,
  filename TEXT NOT NULL,
  file_type TEXT CHECK (file_type IN ('cv', 'job_description')),
  content_type TEXT,
  storage_path TEXT, -- Supabase Storage path
  text_content TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Embeddings (PostgreSQL with pgvector)
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents,
  embedding VECTOR(1536), -- OpenAI embedding dimension
  text_chunks TEXT[],
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

## Security Implementation

### Authentication Flow
1. User login → JWT token issued by Supabase Auth
2. Token validation at API gateway using Supabase client
3. User context extracted from JWT claims
4. Row-level security (RLS) in PostgreSQL for data isolation

### Data Protection
- Encryption at rest (Supabase built-in encryption)
- Encryption in transit (TLS 1.3)
- Row-level security (RLS) in PostgreSQL
- Environment variables for secrets
- Supabase built-in security features

## Performance Optimization

### Caching Strategy
- Redis cache for frequently accessed data
- CDN for static assets
- Application-level caching for embeddings
- Database query optimization

### Scalability
- Auto-scaling Azure Functions
- Cosmos DB auto-scale
- Cognitive Search scaling units
- Load balancing via API Management

## Testing Strategy

### Local Development
```
docker-compose.yml          # Local development stack
├── cosmos-emulator        # Cosmos DB emulator
├── azurite               # Blob storage emulator
├── redis                 # Redis cache
└── servicebus-emulator   # Service Bus emulator
```

### Test Categories
- **Unit Tests**: pytest with 80%+ coverage
- **Integration Tests**: testcontainers for Azure services
- **Contract Tests**: Pact for service communication
- **E2E Tests**: Playwright for user workflows
- **Performance Tests**: Locust for load testing

## Monitoring & Observability (OpenTelemetry)

### Distributed Tracing
```python
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Auto-instrumentation
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Custom spans
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("process_document") as span:
    span.set_attribute("user.id", user_id)
    span.set_attribute("document.type", doc_type)
```

### Logging
- Structured logging (JSON format)
- Automatic correlation IDs via OpenTelemetry
- Basic log aggregation
- Error tracking

### Metrics (Basic MVP)
- Request count and latency
- Error rates
- Document processing times
- User activity metrics

### Cost-Effective Monitoring
- Self-hosted Jaeger for tracing
- Basic health checks
- Simple alerting via email/Slack webhooks

## Development Workflow

### Project Structure
```
resume_match_pro_v2/
├── auth-service/          # Authentication microservice
├── document-service/      # Document management
├── ai-service/           # AI/ML operations
├── api-gateway/          # API gateway
├── infrastructure/       # IaC templates
├── tests/               # Integration tests
├── docker-compose.yml   # Local development
├── .cursorrules         # Development guidelines
└── solution_design.md   # This document
```

### Development Guidelines
- Feature branch workflow
- Pre-commit hooks for code quality
- Test-driven development
- Code review requirements
- Automated deployment on merge to develop

## MVP Development Approach

### Lean Development Strategy
- Start with Supabase free tier
- Use Azure Functions consumption plan (free tier)
- Implement core features first
- Scale when revenue justifies costs

### Technical Risks & Mitigations
- **Embedding costs**: Aggressive caching, batch processing
- **Free tier limits**: Monitor usage, optimize queries
- **Vector search performance**: Use PostgreSQL pgvector with proper indexing
- **Cold starts**: Accept for MVP, optimize later

### Cost Monitoring
- Track Azure OpenAI token usage
- Monitor Supabase database size
- Set up billing alerts
- Optimize queries and caching

This solution design provides a cost-optimized, scalable architecture for the Resume Match Pro AI MVP using a hybrid approach with Supabase for rapid development and Azure for AI services, while maintaining modern development practices and keeping costs under $50/month.
