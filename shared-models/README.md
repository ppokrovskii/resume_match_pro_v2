# Shared Models Package

Auto-generated Pydantic models from microservice OpenAPI specifications for Resume Match Pro.

*Updated for dev branch auto-publishing workflow*

## Overview

This package provides type-safe Python models automatically generated from the OpenAPI specifications of Resume Match Pro microservices. It ensures API compatibility and type safety across all services while maintaining a single source of truth for data structures.

## Installation

```bash
# Install from Azure Artifacts (production)
pip config set global.index-url https://pkgs.dev.azure.com/ppokrovskii/resume_match_pro_v2/_packaging/python_packages/pypi/simple/
pip config set global.extra-index-url https://pypi.org/simple/
pip install resume-match-shared-models

# Or install directly with authentication
pip install --index-url https://pkgs.dev.azure.com/ppokrovskii/resume_match_pro_v2/_packaging/python_packages/pypi/simple/ --extra-index-url https://pypi.org/simple/ resume-match-shared-models

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

Simple workflow: Push to dev branch → automatic publishing to Azure Artifacts.

### GitHub Workflow Setup

Required configuration:
1. **GitHub Environment**: Create a `dev` environment in repository settings
2. **Environment Secret**: Add `AZURE_ARTIFACTS_TOKEN` to the `dev` environment
   - Go to Settings → Environments → `dev` → Add Secret
   - Name: `AZURE_ARTIFACTS_TOKEN`
   - Value: Your Azure DevOps Personal Access Token with Packaging (Read & Write) permissions

Workflow behavior:
- **Push to dev**: Runs tests, builds package, publishes to Azure Artifacts

### Azure DevOps Setup

1. Create Personal Access Token:
   - Go to Azure DevOps → User Settings → Personal Access Tokens
   - Create token with **Packaging (Read & Write)** permissions
   - Copy the token (you won't see it again)

2. Configure GitHub Secrets:
   - `AZURE_ARTIFACTS_TOKEN`: The Personal Access Token from step 1

3. Azure Artifacts Feed Configuration:
   ```
   Repository: https://pkgs.dev.azure.com/ppokrovskii/resume_match_pro_v2/_packaging/python_packages/pypi/upload/
   Index URL: https://pkgs.dev.azure.com/ppokrovskii/resume_match_pro_v2/_packaging/python_packages/pypi/simple/
   ```

## Benefits

- **Type Safety**: Compile-time validation and IDE support
- **Consistency**: Single source of truth from live APIs  
- **Automation**: Zero manual model maintenance
- **Reliability**: Always up-to-date with service APIs
- **Validation**: Pydantic provides runtime data validation

## License

Proprietary - All Rights Reserved

This software is proprietary and confidential. Unauthorized copying, distribution, or use of this software, via any medium, is strictly prohibited without the express written permission of the copyright holder.