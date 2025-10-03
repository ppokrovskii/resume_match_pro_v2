# Document Service - Solution Design

## Overview
Serverless document CRUD microservice using FastAPI and Azure services. Handles file storage, metadata management, and event publishing.

## Responsibilities
- File upload/download (Azure Blob Storage)
- Document CRUD operations
- Metadata storage (PostgreSQL)
- Event publishing for external services
- API for external services to update properties

## Architecture

### Tech Stack
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with pgvector
- **Storage**: Azure Blob Storage
- **Queue**: Azure Storage Queues
- **Auth**: Auth0 JWT validation
- **Monitoring**: OpenTelemetry

### Project Structure
```
document-service/
├── main.py                   # FastAPI app
├── routers/documents.py      # Document CRUD
├── models/document.py        # Pydantic models
├── services/document_service.py  # Business logic
├── utils/storage_service.py  # Blob storage
└── middleware/auth0_middleware.py  # Auth
```

## Core Models

### Document Model
```python
class Document(BaseModel):
    id: str
    user_id: str
    organization_id: Optional[str]
    filename: str
    file_type: Optional[str]  # 'cv' | 'jd'
    content_type: str
    file_size: int
    text_content: Optional[str]  # Extracted text (markdown format)
    role: Optional[str]  # "Python Developer"
    features: List[Feature]  # Skills (CV) or Requirements (JD)
    metadata: dict
    created_at: datetime
    updated_at: datetime
```

### Feature Model
```python
class Feature(BaseModel):
    name: str  # "Python", "AWS Certification"
    type: str  # "skill", "certification", "experience"
    properties: dict  # {"years": 5, "level": "expert"}
```

## API Endpoints

### Document Management
- `POST /documents/upload` - Upload files
- `GET /documents` - List user documents
- `GET /documents/{id}` - Get document details
- `GET /documents/{id}/download` - Download file
- `PUT /documents/{id}` - Update metadata (external services)
- `DELETE /documents/{id}` - Delete document

### Authentication
- `POST /auth/swagger-token` - Get token for Swagger UI

## Event Publishing

### Events Published
```python
# On document upload
{
    "eventType": "document.created",
    "documentId": "uuid",
    "fileName": "resume.pdf",
    "userId": "uuid",
    "organizationId": "uuid"
}

# On metadata update
{
    "eventType": "document.updated", 
    "documentId": "uuid",
    "changes": ["text_content", "features"]
}
```

## External Service Integration

### Document Update API
- PUT /documents/{id} for metadata updates
- Supports: file_type, text_content (in markdown format), role, features
- Atomic updates with validation
- Publishes `document.updated` event after successful update

## Security & Access Control

### Authentication
- Auth0 JWT validation
- User/Organization isolation
- Service-to-service authentication for external updates

### Data Protection
- Row Level Security (RLS) in PostgreSQL
- Secure file upload validation
- Audit logging for all operations

## Database Schema

### Documents Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    organization_id UUID,
    filename VARCHAR NOT NULL,
    file_type VARCHAR CHECK (file_type IN ('cv', 'jd')),
    content_type VARCHAR NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path VARCHAR,
    doc_metadata JSONB DEFAULT '{}',  -- text_content, role, features
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Configuration
```python
# Environment Variables
DATABASE_URL = "postgresql://..."
AZURE_STORAGE_CONNECTION_STRING = "..."
AUTH0_DOMAIN = "tenant.auth0.com"
AZURE_STORAGE_QUEUE_CONNECTION = "..."
```

## Deployment
- Azure Container Apps (serverless containers)
- PostgreSQL Flexible Server
- Azure Blob Storage
- Infrastructure as Code (Terraform)