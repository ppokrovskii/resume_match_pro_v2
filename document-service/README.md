# Document Service

Document CRUD microservice with event-driven architecture:
- **Pure storage**: No text processing in this service
- **Event publishing**: Azure Storage Queues for microservice communication
- **Organizations**: Enterprise user isolation

## Tech Stack
FastAPI + PostgreSQL + Azure Blob Storage + Azure Storage Queues + Auth0

## Quick Start
```bash
# Install & start local services
uv sync
docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16
# Azure services (Blob Storage, Storage Queues) configured via connection strings

# Setup & run
cp env.example .env
uv run alembic upgrade head
uv run python main.py
```

## API Endpoints
- `POST /documents/upload` - Upload documents (single or multiple)
- `GET /documents` - List documents  
- `GET /documents/{id}` - Get document
- `PUT /documents/{id}` - Update document (for external services)
- `DELETE /documents/{id}` - Delete document

## Documentation
- [Business Requirements](docs/requirements.md) - User stories and acceptance criteria
- [Solution Design](docs/solution_design.md) - Technical architecture and API design
- [Test Plan](docs/test_plan.md) - Testing strategy and test cases
- [Auth0 Setup](docs/auth0_setup.md) - Authentication configuration guide

