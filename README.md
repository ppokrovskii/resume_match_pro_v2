# Resume Match Pro AI - MVP

AI-powered resume matching system with serverless microservices architecture.

## Architecture (Hybrid Cost-Optimized)

- **Frontend**: React 18 with TypeScript (Vercel/Netlify free tier)
- **Authentication**: Supabase Auth (managed service)
- **Document Service**: File upload, parsing, and text extraction (Azure Functions)
- **AI Service**: Embedding generation and semantic matching (Azure Functions + OpenAI)
- **API Gateway**: Request routing and service orchestration (Azure Functions)
- **Database**: Supabase PostgreSQL with pgvector
- **Storage**: Supabase Storage
- **Observability**: OpenTelemetry + self-hosted Jaeger

## Technology Stack (Cost-Optimized)

- **Language**: Python 3.11+ (Backend), TypeScript (Frontend)
- **Framework**: Flask (serverless), React 18
- **Package Manager**: uv
- **Infrastructure**: Terraform (multi-cloud)
- **Auth**: Supabase Auth (free tier: unlimited users)
- **Database**: Supabase PostgreSQL with pgvector (free tier: 500MB)
- **Storage**: Supabase Storage (free tier: 1GB)
- **AI**: Azure OpenAI (pay-per-use: ~$0.0001/1K tokens)
- **Compute**: Azure Functions consumption plan (free tier: 1M requests)
- **Frontend Hosting**: Vercel/Netlify (free tier)
- **Total Cost**: $0-50/month for MVP

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- uv package manager

### Local Development Setup

1. **Start local services**:
   ```bash
   docker-compose up -d
   ```

2. **Install dependencies**:
   ```bash
   pip install uv
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   # Backend services
   cd document-service && uv pip install -r requirements.txt && cd ..
   cd ai-service && uv pip install -r requirements.txt && cd ..
   cd api-gateway && uv pip install -r requirements.txt && cd ..
   
   # Frontend
   cd frontend && npm install && cd ..
   ```

4. **Set environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run tests**:
   ```bash
   pytest --cov=. --cov-report=html
   ```

## Project Structure

```
resume_match_pro_v2/
├── frontend/              # React TypeScript application
├── document-service/      # Document management microservice
├── ai-service/           # AI/ML operations microservice
├── api-gateway/          # API gateway microservice
├── infrastructure/       # Infrastructure as Code (Terraform)
│   └── sql/             # Database initialization scripts
├── tests/               # Integration tests
├── docker-compose.yml   # Local development stack
├── .cursorrules         # Development guidelines
└── solution_design.md   # Architecture documentation
```

Note: Authentication is handled by Supabase Auth (managed service)

## Services

### Frontend (React TypeScript)
- Drag-and-drop file uploads
- Dual-pane CV/JD interface
- Real-time search and filtering
- Supabase Auth integration

### Document Service  
- File upload/download via Supabase Storage
- PDF/Word parsing (local processing)
- Text extraction and preprocessing
- Metadata storage in PostgreSQL

### AI Service
- Embedding generation (Azure OpenAI)
- Vector similarity calculations using pgvector
- Semantic search and matching
- Cost-optimized caching

### API Gateway
- Request routing between services
- Supabase JWT token validation
- Rate limiting and CORS
- Response aggregation
- OpenTelemetry tracing

## Development Workflow

1. Create feature branch from `develop`
2. Write tests first (TDD approach)
3. Implement feature with 80%+ test coverage
4. Run pre-commit hooks (formatting, linting, tests)
5. Create pull request to `develop`
6. Monitor GitHub Actions until successful completion

## Testing

### Test Categories
- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`
- **E2E Tests**: `pytest tests/e2e/`

### Coverage Requirements
- Minimum 80% coverage for all modules
- 100% coverage for critical business logic
- Auto-tests required before fixing defects

## Deployment

### Infrastructure as Code (Terraform)
```bash
cd infrastructure
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### Application Deployment
- GitHub Actions CI/CD pipeline
- Automated testing and security scanning
- Blue/green deployment strategy
- Rollback procedures

## Monitoring (Cost-Optimized)

- **OpenTelemetry**: Distributed tracing and metrics
- **Self-hosted Jaeger**: Request flow visualization
- **Basic Logging**: Structured JSON logs
- **Health Checks**: Service availability monitoring
- **Cost Tracking**: Azure OpenAI token usage monitoring

## Security

- Supabase Auth with JWT tokens
- Row Level Security (RLS) in PostgreSQL
- Data encryption at rest and in transit
- Environment variables for secrets
- Input validation and sanitization
- CORS and security headers

## Performance (MVP Optimized)

- Azure Functions consumption plan (auto-scaling)
- Aggressive embedding caching (Redis)
- PostgreSQL pgvector for fast similarity search
- Async/await for I/O operations
- Frontend CDN via Vercel/Netlify

## Cost Optimization (Key for MVP)

- **Free Tiers Maximized**:
  - Supabase: 500MB DB, 1GB storage, unlimited auth
  - Azure Functions: 1M requests/month
  - Vercel/Netlify: Unlimited personal projects
  - GitHub Actions: 2000 minutes/month

- **Pay-per-use Only**:
  - Azure OpenAI: ~$0.0001 per 1K tokens
  - Additional Supabase usage: $25/month when needed

- **Aggressive Caching**: Reduce AI API calls by 90%+
- **Efficient Queries**: Optimize PostgreSQL for performance
- **Smart Batching**: Process embeddings in batches

## Contributing

1. Follow the development guidelines in `.cursorrules`
2. Ensure all tests pass before committing
3. Use conventional commit messages
4. Update documentation for new features
5. Never disable pre-commit hooks

## Support

For technical issues, check:
1. Application Insights logs
2. Service health endpoints  
3. Azure service status
4. Recent deployment changes

## License

MIT License - see LICENSE file for details.
