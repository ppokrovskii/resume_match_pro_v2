# Shared Models Package - Solution Design

## Overview
Auto-generated Pydantic models from microservice OpenAPI specs. Ensures type safety and API compatibility across Resume Match Pro services.

## Architecture

### Tech Stack
- **Models**: Pydantic v2 with type annotations
- **Generation**: datamodel-code-generator from live OpenAPI endpoints
- **Distribution**: Python package via Azure Artifacts
- **CI/CD**: Automated generation and publishing

### Package Structure
```
shared-models/
├── pyproject.toml           # Package config
├── scripts/generate_models.py  # Generation logic
├── src/shared_models/
│   ├── base.py             # ✅ COMMIT - Base classes
│   └── generated/          # ❌ DON'T COMMIT - Auto-generated
│       ├── document_service/
│       └── ai_text_extract/
└── tests/                  # Model validation tests
```

## Model Generation

### Source Services
Services expose OpenAPI specs at `/openapi.json`:
- Document Service: `https://api.resumematch.com/document-service/openapi.json`
- AI Text Extract: `https://api.resumematch.com/ai-text-extract/openapi.json`

### Generation Script
```python
# scripts/generate_models.py
async def fetch_openapi_spec(service: str, environment: str) -> Dict:
    url = SERVICES[service][environment]
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        return response.json()

def generate_models_for_service(service: str, spec: Dict) -> None:
    output_dir = Path(f"src/shared_models/generated/{service}")
    generate(json.dumps(spec), output=output_dir / "models.py")
```

## Development Workflow

### What Gets Committed
- ✅ **Base classes** (`base.py`)
- ✅ **Generation scripts** (`scripts/`)
- ✅ **Tests** (`tests/`)
- ✅ **Package config** (`pyproject.toml`)
- ❌ **Generated models** (auto-generated fresh)

### CI/CD Process
1. Service deploys → OpenAPI spec available
2. Shared-models fetches spec → generates models
3. Tests pass → publishes to Azure Artifacts
4. Consumer services update dependency

### Usage
```python
# Install from Azure Artifacts
pip install resume-match-shared-models --index-url https://pkgs.dev.azure.com/resumematch/_packaging/shared-packages/pypi/simple/

# Use
from shared_models.generated.document_service import DocumentUpdateRequest

request = DocumentUpdateRequest(
    file_type="cv",
    markdown_content="# John Doe\n\n## Experience\n...",
    features=[FeatureModel(name="Python", type="skill")]
)
```

## Benefits
- **Type Safety**: Compile-time validation, IDE support
- **Consistency**: Single source of truth from live APIs  
- **Automation**: Zero manual model maintenance
- **Reliability**: Always up-to-date with service APIs