# Document Service - Solution Design

## Service Overview

**Purpose**: Serverless document CRUD microservice  
**Technology**: Python 3.11+ with FastAPI  
**Deployment**: Container-based serverless deployment  
**Storage**: Azure Blob Storage, PostgreSQL  

## Responsibilities

- File upload/download management (pure storage)
- Document CRUD operations (Create, Read, Update, Delete)
- Document metadata storage and management
- File validation and security
- Event publishing for external microservices
- API for external services to update document properties
- No text extraction or AI processing (handled by separate applications)

## Architecture

### Core Components

```
document-service/
├── main.py                   # FastAPI app entry point
├── routers/
│   ├── documents.py         # Document CRUD operations
│   ├── health.py            # Health check endpoints
│   └── auth.py              # Authentication endpoints
├── models/
│   ├── document.py          # Document metadata model
│   └── db_models.py         # Database models
├── services/
│   ├── document_service.py  # Core document CRUD logic
│   └── storage_service.py   # Blob storage interface
├── utils/
│   ├── file_validators.py   # File validation utilities
│   ├── event_publisher.py   # Event publishing utilities
│   └── auth_utils.py        # Authentication utilities
└── middleware/              # Custom middleware
    └── auth0_middleware.py  # Auth0 JWT middleware
```

## API Endpoints

### Document Management (`/documents`)
- `POST /documents/upload` - Upload documents (single or multiple files)
- `GET /documents` - List user documents (with filtering)
- `GET /documents/{id}` - Get document details
- `GET /documents/{id}/download` - Download document file
- `PUT /documents/{id}` - Update document properties (type, extracted text, metadata)
- `DELETE /documents/{id}` - Delete document


## Data Models

### Document Model
```python
@dataclass
class Document:
    id: str
    user_id: str
    organization_id: Optional[str]  # Enterprise users belong to organizations
    filename: str
    file_type: Optional[str]  # 'cv' | 'jd' | null
    content_type: str
    file_size: int
    storage_path: str
    text_content: Optional[str]  # Extracted text content
    role: Optional[str]  # "Python Developer", "English Teacher", "Business Analyst"
    features: List[Feature]  # Skills (CV) or Requirements (JD)
    metadata: dict
    created_at: datetime
    updated_at: datetime

@dataclass 
class Feature:
    name: str  # Feature/skill name
    type: str  # "skill", "certification", "language", "tool", etc.
    properties: dict  # Flexible key-value properties

# Examples:
# Basic skill: 
# Feature(name="Python", type="skill", properties={"years": 5, "level": "expert"})

# Certification:
# Feature(name="AWS Solutions Architect", type="certification", 
#         properties={"grade": "A", "percentage": 92, "year_obtained": 2023, "expires": 2026})

# Language:
# Feature(name="Spanish", type="language", 
#         properties={"level": "fluent", "certification": "DELE B2"})

# Soft skill:
# Feature(name="Leadership", type="soft_skill", 
#         properties={"description": "Team leadership experience", "years": 3})
```

### Upload Session Model
```python
@dataclass
class UploadSession:
    id: str
    user_id: str
    filename: str
    total_size: int
    uploaded_chunks: List[int]
    status: str  # 'active' | 'completed' | 'failed'
    created_at: datetime
    expires_at: datetime
```

## File Processing Pipeline

### 1. Upload Validation
- File type validation (.pdf, .doc, .docx)
- File size limits (16MB max)
- Content type verification
- Basic file integrity checks

### 2. External Service Integration
- All text extraction handled by separate applications
- Document type classification handled by external AI services
- Advanced metadata extraction handled by external services
- Content analysis and scoring handled by external services
- Results updated via PUT /documents/{id} endpoint
- Document service remains stateless and focused on storage

## Storage Strategy

### Storage Structure
```
containers/
├── documents/
│   ├── {organization_id}/  # Enterprise users
│   │   └── {user_id}/
│   └── {user_id}/         # Individual users
└── temp-uploads/
```

### Database
- PostgreSQL with user/organization isolation
- Indexes: `user_id`, `organization_id`, `file_type`, `created_at`

## Dependencies

### Core Dependencies
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
azure-storage-blob==12.19.0
```

### Authentication & Security
```
python-jose[cryptography]==3.3.0
authlib==1.2.1
```

### Event Publishing
```
azure-storage-queue==12.8.0
azure-identity==1.15.0
```

## Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://...
AUTH0_DOMAIN=tenant.auth0.com
AUTH0_API_IDENTIFIER=https://api.resumematch.com/document-service
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_NAME=documents
AZURE_STORAGE_QUEUE_NAME=document-events
MAX_FILE_SIZE=16777216  # 16MB
```

## Processing Workflow

### Upload Flow (Single or Multiple Files)
1. Accept 1-N files in single request
2. Process each file: Validate → Store in Azure Blob Storage → Save metadata in PostgreSQL
3. **Publish Event**: `document.uploaded` to Azure Storage Queue for text extraction service
4. Return array of document results immediately
5. Files available for download immediately

### Update Flow (External Services)
1. External service calls PUT /documents/{id} with extracted data
2. Update document metadata in PostgreSQL
3. **Publish Event**: `document.updated` to Azure Storage Queue for AI matching service
4. Return success response

### Event-Driven Architecture
- **Text Extraction Service** listens to `document.uploaded` events from Azure Storage Queue
- **AI Matching Service** listens to `document.updated` events from Azure Storage Queue  
- Document service remains stateless - only publishes events
- Azure Storage Queues provide reliable message delivery and poison message handling

## Event Schemas

### Document Uploaded Event
```json
{
  "event_type": "document.uploaded",
  "document_id": "uuid",
  "content_type": "application/pdf", // optional
  "timestamp": "2024-01-15T10:30:00Z" // optional
}
```

**Design Rationale:**
- ❌ **No storage_path**: Avoids exposing internal storage structure
- ❌ **No user_id/org_id**: Consumer services don't need this info
- ✅ **Minimal data**: Only what's needed for text extraction
- ✅ **Security**: Consumer calls GET /documents/{id} with proper auth if needed

### Document Updated Event
```json
{
  "event_type": "document.updated",
  "document": {
    // full document response model
}
```

**Design Rationale:**
- ✅ **Full document data**: AI matching service gets everything it needs
- ✅ **No additional API calls**: Reduces load on document service
- ✅ **Efficient**: One event contains all matching data
- ❌ **No user/org data**: Consumer doesn't need identity info for matching
- ✅ **Atomic**: Complete state for AI processing

## API Integration

### External Service Authentication
- Services must authenticate with JWT tokens
- API rate limiting applied per service
- Audit logging for all external updates

### Document Update API
- PUT /documents/{id} for metadata updates
- Supports: file_type, text_content, role, features
- Atomic updates with validation
- Publishes `document.updated` event after successful update

## Security & Access Control

### User/Organization Isolation
- Individual users: Access only own documents
- Enterprise users: Access organization documents based on role
- Storage paths: `/{organization_id}/{user_id}/` or `/{user_id}/`
- Database queries: Always filter by user_id + organization_id

### File Security  
- JWT authentication required for all operations
- File type validation (PDF, DOC, DOCX only)
- File size limits enforced (16MB maximum)
- Encryption at rest via Azure Blob Storage
- Secure file deletion (permanent removal)
- Content-type verification to prevent malicious uploads

### API Security
- Rate limiting per user/service (100 requests/minute)
- Request/response logging for audit trails
- Input validation and sanitization
- CORS configuration for web clients
- Secure error messages (no sensitive data exposure)

## Performance & Scalability

### Performance Targets
- **Upload**: Complete within 5 seconds for 16MB files
- **Download**: Start streaming within 1 second
- **List Documents**: Load 50 documents in under 2 seconds
- **Bulk Upload**: Process 10 files within 15 seconds
- **API Response**: 95th percentile under 500ms

### Scalability Design
- **Stateless Service**: No in-memory state, scales horizontally
- **Database Connection Pooling**: Efficient PostgreSQL connections
- **Blob Storage**: Azure handles file storage scaling automatically
- **Event Publishing**: Azure Storage Queues handle message scaling
- **Container Deployment**: Kubernetes/Azure Container Apps ready

### Caching Strategy
- **No File Caching**: Files served directly from Azure Blob Storage
- **Metadata Caching**: Database queries optimized with indexes
- **Static Content**: CDN for API documentation and assets

## Monitoring & Observability

### Health Checks
- **Database**: Connection and query health
- **Storage**: Azure Blob Storage connectivity
- **Event Publisher**: Azure Storage Queue connectivity
- **Overall**: Composite health status

### Metrics & Logging
- **Application Metrics**: Request count, response times, error rates
- **Business Metrics**: Upload success/failure rates, file sizes, user activity
- **Infrastructure Metrics**: CPU, memory, network, storage usage
- **Structured Logging**: JSON format with correlation IDs

### Distributed Tracing
- **OpenTelemetry**: Request tracing across service boundaries
- **Jaeger Integration**: Optional tracing export for debugging
- **Correlation IDs**: Track requests through external service calls

## Deployment & Operations

### Container Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration
- **Development**: Local PostgreSQL + Azurite emulator
- **Staging**: Azure PostgreSQL + Azure Storage (non-production)
- **Production**: Azure PostgreSQL + Azure Storage (production tier)

### Database Migrations
- **Alembic**: Database schema versioning and migrations
- **Automated**: Migrations run during deployment
- **Rollback**: Support for schema rollbacks if needed

### Backup & Recovery
- **Database**: Automated PostgreSQL backups (Azure)
- **Files**: Geo-redundant storage with Azure Blob Storage
- **Configuration**: Infrastructure as Code (Terraform/ARM)

## Error Handling & Resilience

### Error Categories
- **Validation Errors**: 400 Bad Request with detailed field errors
- **Authentication Errors**: 401 Unauthorized with clear messages
- **Authorization Errors**: 403 Forbidden for access violations
- **Not Found Errors**: 404 Not Found for missing resources
- **Server Errors**: 500 Internal Server Error with correlation IDs

### Retry Logic
- **Database Operations**: Automatic retry with exponential backoff
- **Storage Operations**: Azure SDK handles retries automatically
- **Event Publishing**: Retry failed events with dead letter queue

### Circuit Breaker Pattern
- **External Services**: Protect against cascading failures
- **Graceful Degradation**: Continue core operations when possible
- **Health Monitoring**: Automatic recovery detection

## API Versioning & Evolution

### Versioning Strategy
- **URL Versioning**: `/api/v1/documents` for clear version identification
- **Backward Compatibility**: Maintain previous versions for 12 months
- **Deprecation Policy**: 6-month notice for breaking changes

### API Evolution
- **Additive Changes**: New optional fields, new endpoints
- **Breaking Changes**: Require new version (v2, v3, etc.)
- **Documentation**: OpenAPI spec with version-specific schemas

## Integration Patterns

### Event-Driven Integration
- **Publish Events**: Document lifecycle events to Azure Storage Queues
- **Consume Events**: External services process events asynchronously
- **Event Schemas**: Versioned schemas for backward compatibility
- **Dead Letter Handling**: Failed events routed to dead letter queue

### API Integration
- **External Service Updates**: PUT /documents/{id} for metadata updates
- **Authentication**: JWT tokens for service-to-service communication
- **Rate Limiting**: Per-service quotas to prevent abuse
- **Audit Logging**: Track all external service interactions

### Webhook Support (Future)
- **Document Events**: Optional webhooks for real-time notifications
- **Retry Logic**: Exponential backoff for failed webhook deliveries
- **Security**: HMAC signatures for webhook verification

## Testing Strategy

### Test Pyramid
- **Unit Tests**: Business logic, utilities, models (80% coverage)
- **Integration Tests**: Database, storage, external APIs (real services)
- **E2E Tests**: Complete workflows through HTTP API
- **Contract Tests**: API schema validation and backward compatibility

### Test Environment
- **Testcontainers**: PostgreSQL, Azurite for integration tests
- **Mock Services**: External dependencies for unit tests
- **Test Data**: Realistic test documents and scenarios
- **Performance Tests**: Load testing for scalability validation

## Future Enhancements

### Planned Features
- **Document Versioning**: Track document history and changes
- **Advanced Search**: Full-text search with Elasticsearch integration
- **Webhook Notifications**: Real-time event notifications
- **Document Thumbnails**: Preview generation for supported formats
- **Bulk Operations**: Batch delete, update, and export operations

### Technical Improvements
- **GraphQL API**: Alternative to REST for flexible queries
- **Streaming Uploads**: Support for large file uploads (>16MB)
- **Content Delivery Network**: Global file distribution
- **Advanced Analytics**: Document usage and performance metrics

---

## Conclusion

This document service provides a clean, focused CRUD API for document management with strong separation of concerns. By keeping AI and text processing in external services, the document service remains simple, scalable, and maintainable while providing reliable storage and metadata management for the Resume Match Pro platform.
