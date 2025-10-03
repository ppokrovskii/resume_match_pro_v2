# Shared Models Package

Auto-generated Pydantic models from microservice OpenAPI specifications for Resume Match Pro.

## Overview

This package provides type-safe Python models automatically generated from the OpenAPI specifications of Resume Match Pro microservices. It ensures API compatibility and type safety across all services while maintaining a single source of truth for data structures.

## Installation

```bash
# Install from Azure Artifacts (production)
pip install resume-match-shared-models --index-url https://pkgs.dev.azure.com/resumematch/_packaging/shared-packages/pypi/simple/

# Or install in development mode
pip install -e .
```

## Usage

```python
from shared_models.generated.document_service import (
    DocumentUpdateRequest,
    DocumentResponse, 
    Feature,
    FeatureProperties
)

# Type-safe model creation
feature = Feature(
    name="Python",
    type="skill",
    properties=FeatureProperties(
        years=5,
        level="expert"
    )
)

# Type-safe API request
update_request = DocumentUpdateRequest(
    file_type="cv",
    text_content="# John Doe\nSoftware Engineer...",
    role="Senior Python Developer",
    features=[feature],
    metadata={"confidence_score": 0.95}
)
```

## Development

### Generating Models

Models are automatically generated from live service OpenAPI specs:

```bash
# Generate models from all services
python scripts/generate_models.py

# Generate from specific service
python scripts/generate_models.py --service document_service

# Generate from local OpenAPI file
python scripts/generate_models.py --file path/to/openapi.json --service document_service
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/shared_models --cov-report=html

# Run specific tests
pytest tests/test_document_service_models.py
```

## Package Structure

```
shared-models/
├── src/shared_models/
│   ├── base.py              # Base classes and utilities
│   └── generated/           # Auto-generated models (not committed)
│       ├── document_service/
│       └── ai_text_extract/
├── scripts/
│   └── generate_models.py   # Model generation script
├── tests/                   # Model validation tests
└── pyproject.toml          # Package configuration
```

## CI/CD Integration

Models are automatically updated when service APIs change:

1. Service deploys → OpenAPI spec becomes available
2. Shared-models CI fetches spec → generates models  
3. Tests pass → publishes to PyPI
4. Consumer services update dependency

### GitHub Workflow Setup

Required secrets in repository settings:
- `PYPI_API_TOKEN` - Production PyPI publishing
- `TEST_PYPI_API_TOKEN` - Test PyPI validation

Workflow behavior:
- **PRs**: Validation and testing only
- **Push to develop**: Test PyPI publishing  
- **Push to main**: Full PyPI release with GitHub release

## Benefits

- **Type Safety**: Compile-time validation and IDE support
- **Consistency**: Single source of truth from live APIs  
- **Automation**: Zero manual model maintenance
- **Reliability**: Always up-to-date with service APIs
- **Validation**: Pydantic provides runtime data validation

## License

MIT License - see LICENSE file for details.
