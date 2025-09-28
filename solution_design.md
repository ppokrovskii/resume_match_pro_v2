# Resume Match Pro AI - Solution Design

## Architecture Overview

**Architecture Pattern**: Serverless Microservices  
**Language**: Python 3.11+  
**Framework**: Flask with serverless deployment  
**Package Manager**: uv  
**Infrastructure**: Hybrid (Supabase Auth + Azure AI Services)  
**Frontend**: React with TypeScript  
**Deployment**: Infrastructure as Code (Terraform)  
**Observability**: OpenTelemetry for distributed tracing  

## Microservices Architecture

### Service Decomposition

The system is decomposed into 4 core components:

1. **Frontend Application** (`frontend/`) - React TypeScript SPA
2. **Document Service** (`document-service/`) - File processing microservice
3. **AI Service** (`ai-service/`) - ML/AI operations microservice
4. **Web API Gateway** (`api-gateway/`) - Request routing microservice

**Note**: Authentication is handled by Supabase Auth (managed service)

### Service Communication

- **Synchronous**: REST APIs for user-facing operations
- **Authentication**: Supabase Auth with JWT token validation
- **Observability**: OpenTelemetry for distributed tracing
- **Async Processing**: Simple queues for MVP (Redis-based)

## Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand (lightweight)
- **UI Library**: Tailwind CSS + Headless UI
- **Auth**: Supabase Auth client
- **Hosting**: Vercel (free tier) or Netlify

### Backend Services
- **Runtime**: Python 3.11+
- **Web Framework**: Flask 3.x with Flask-CORS
- **Package Management**: uv (fast Python package installer)
- **Serverless**: Azure Functions (consumption plan)
- **API Gateway**: Flask-based gateway (cost-optimized)

### Authentication & User Management
- **Auth Service**: Supabase Auth (managed)
- **User Database**: Supabase PostgreSQL
- **JWT Validation**: Supabase client libraries

### Data Layer (Cost-Optimized)
- **Document Metadata**: Supabase PostgreSQL
- **Vector Database**: Supabase pgvector extension
- **File Storage**: Supabase Storage
- **Cache**: Redis (free tier or local Redis)

### AI/ML Stack
- **Embeddings**: Azure OpenAI (pay-per-use)
- **Document Processing**: pypdf2/python-docx (local processing)
- **Vector Similarity**: PostgreSQL pgvector

### Infrastructure & DevOps
- **IaC**: Terraform (multi-cloud flexibility)
- **Observability**: OpenTelemetry + Jaeger (self-hosted)
- **CI/CD**: GitHub Actions (free tier)
- **Monitoring**: Basic logging + health checks

## Service Details

### 1. Frontend Application (React TypeScript)

**Technology Stack:**
- React 18 with TypeScript
- Supabase Auth client
- Tailwind CSS + Headless UI
- Zustand for state management

**Key Features:**
- Drag-and-drop file uploads
- Dual-pane CV/JD interface
- Real-time search and filtering
- Responsive design

**Authentication Flow:**
```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.REACT_APP_SUPABASE_URL!,
  process.env.REACT_APP_SUPABASE_ANON_KEY!
)

// Login with email/password
const { data, error } = await supabase.auth.signInWithPassword({
  email, password
})

// Google OAuth
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google'
})
```

### 2. Document Service (`document-service/`)

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

### 3. AI Service (`ai-service/`)

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

## Infrastructure Design (Cost-Optimized MVP)

### Hybrid Architecture

**Supabase (Primary - Free Tier):**
- Authentication and user management
- PostgreSQL database with pgvector
- File storage
- Real-time subscriptions
- Row-level security

**Azure (Pay-per-use):**
- Azure Functions (consumption plan)
- Azure OpenAI (embeddings only)

**Free/Cheap Services:**
- Frontend: Vercel/Netlify free tier
- Monitoring: Self-hosted Jaeger
- Cache: Redis free tier or local Redis

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
