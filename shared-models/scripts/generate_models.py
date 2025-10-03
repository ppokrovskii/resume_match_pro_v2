#!/usr/bin/env python3
"""
Generate Pydantic models from microservice OpenAPI specifications.

This script fetches OpenAPI specs from running services and generates
type-safe Pydantic models using datamodel-code-generator.
"""

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx

# Service configuration
SERVICES = {
    "document_service": {
        "local": "http://localhost:5001/openapi.json",
        "dev": "https://api-dev.resumematch.com/document-service/openapi.json",
        "staging": "https://api-staging.resumematch.com/document-service/openapi.json",
        "prod": "https://api.resumematch.com/document-service/openapi.json",
    },
    "ai_text_extract": {
        "local": "http://localhost:5002/openapi.json",
        "dev": "https://api-dev.resumematch.com/ai-text-extract/openapi.json",
        "staging": "https://api-staging.resumematch.com/ai-text-extract/openapi.json",
        "prod": "https://api.resumematch.com/ai-text-extract/openapi.json",
    },
    "matches_service": {
        "local": "http://localhost:5003/openapi.json",
        "dev": "https://api-dev.resumematch.com/matches-service/openapi.json",
        "staging": "https://api-staging.resumematch.com/matches-service/openapi.json",
        "prod": "https://api.resumematch.com/matches-service/openapi.json",
    },
}

# Base directory for generated models
BASE_DIR = Path(__file__).parent.parent
GENERATED_DIR = BASE_DIR / "src" / "shared_models" / "generated"


async def fetch_openapi_spec(service: str, environment: str) -> Dict:
    """Fetch OpenAPI specification from service endpoint."""
    if service not in SERVICES:
        raise ValueError(
            f"Unknown service: {service}. Available: {list(SERVICES.keys())}"
        )

    if environment not in SERVICES[service]:
        raise ValueError(
            f"Unknown environment: {environment}. Available: {list(SERVICES[service].keys())}"
        )

    url = SERVICES[service][environment]
    print(f"Fetching OpenAPI spec from {url}...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to fetch OpenAPI spec from {url}: {e}")


def load_openapi_spec_from_file(file_path: str) -> Dict:
    """Load OpenAPI specification from local file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to load OpenAPI spec from {file_path}: {e}")


def generate_models_for_service(service: str, spec: Dict) -> None:
    """Generate Pydantic models from OpenAPI specification."""
    print(f"Generating models for {service}...")

    # Create output directory
    output_dir = GENERATED_DIR / service
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save spec to temporary file
    temp_spec_file = output_dir / "temp_openapi.json"
    with open(temp_spec_file, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)

    # Generate models using datamodel-code-generator
    output_file = output_dir / "models.py"
    cmd = [
        sys.executable,
        "-m",
        "datamodel_codegen",
        "--input",
        str(temp_spec_file),
        "--output",
        str(output_file),
        "--target-python-version",
        "3.11",
        "--use-annotated",
        "--use-generic-container-types",
        "--field-constraints",
        "--use-schema-description",
        "--disable-timestamp",
        "--use-default-kwarg",
        "--use-double-quotes",
        "--use-union-operator",
        "--collapse-root-models",
        "--use-standard-collections",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Generated models for {service}")

        # Add generation header to the file
        add_generation_header(output_file, service, spec)

        # Create __init__.py file
        create_init_file(output_dir, service)

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate models for {service}: {e.stderr}")
        raise
    finally:
        # Clean up temporary file
        if temp_spec_file.exists():
            temp_spec_file.unlink()


def add_generation_header(file_path: Path, service: str, spec: Dict) -> None:
    """Add generation metadata header to the generated file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract service info from spec
    info = spec.get("info", {})
    title = info.get("title", "Unknown Service")
    version = info.get("version", "Unknown")
    description = info.get("description", "")

    header = f'''"""
Auto-generated Pydantic models from {title} OpenAPI specification.

Service: {title}
Version: {version}
Description: {description}
Generated: {datetime.utcnow().isoformat()}Z

DO NOT EDIT MANUALLY - Use scripts/generate_models.py to regenerate.
"""

'''

    # Add imports for base classes
    imports = """from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from ..base import BaseSharedModel, TimestampMixin, UserContextMixin, MetadataMixin

"""

    # Replace the generated imports with our enhanced imports
    lines = content.split("\n")

    # Find where the actual model definitions start (after imports)
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("class ") or line.strip().startswith("def "):
            start_idx = i
            break

    # Reconstruct the file
    model_content = "\n".join(lines[start_idx:])

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header + imports + model_content)


def create_init_file(output_dir: Path, service: str) -> None:
    """Create __init__.py file for the service module."""
    init_file = output_dir / "__init__.py"

    # Read the generated models file to extract class names
    models_file = output_dir / "models.py"
    if not models_file.exists():
        return

    with open(models_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract class names
    class_names = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("class ") and "(" in line:
            class_name = line.split("class ")[1].split("(")[0].strip()
            if class_name:
                class_names.append(class_name)

    # Create __init__.py content
    init_content = f'''"""
Generated models for {service} service.

This module contains auto-generated Pydantic models from the {service} OpenAPI specification.
"""

from .models import (
{chr(10).join(f"    {name}," for name in sorted(class_names))}
)

__all__ = [
{chr(10).join(f'    "{name}",' for name in sorted(class_names))}
]
'''

    with open(init_file, "w", encoding="utf-8") as f:
        f.write(init_content)


def create_generated_init_file() -> None:
    """Create __init__.py file for the generated package."""
    init_file = GENERATED_DIR / "__init__.py"

    # Find all service directories
    service_dirs = [
        d.name
        for d in GENERATED_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]

    init_content = '''"""
Generated models from microservice OpenAPI specifications.

This package contains auto-generated Pydantic models for all Resume Match Pro services.
"""

# Service modules are imported dynamically to avoid import errors
# if not all services are available in all environments.

__all__ = []
'''

    with open(init_file, "w", encoding="utf-8") as f:
        f.write(init_content)


async def generate_models(
    services: Optional[List[str]] = None,
    environment: str = "local",
    file_path: Optional[str] = None,
    service_name: Optional[str] = None,
) -> None:
    """Generate models for specified services."""

    # Ensure generated directory exists
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    if file_path:
        # Generate from local file
        if not service_name:
            raise ValueError("--service is required when using --file")

        print(f"Loading OpenAPI spec from file: {file_path}")
        spec = load_openapi_spec_from_file(file_path)
        generate_models_for_service(service_name, spec)

    else:
        # Generate from service endpoints
        target_services = services or list(SERVICES.keys())

        for service in target_services:
            try:
                spec = await fetch_openapi_spec(service, environment)
                generate_models_for_service(service, spec)
            except Exception as e:
                print(f"❌ Failed to generate models for {service}: {e}")
                if len(target_services) == 1:
                    # If only one service was requested, re-raise the error
                    raise
                else:
                    # Continue with other services
                    continue

    # Create package __init__.py files
    create_generated_init_file()

    print("✅ Model generation completed!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Pydantic models from OpenAPI specs"
    )
    parser.add_argument(
        "--service",
        action="append",
        choices=list(SERVICES.keys()),
        help="Service to generate models for (can be specified multiple times)",
    )
    parser.add_argument(
        "--environment",
        choices=["local", "dev", "staging", "prod"],
        default="local",
        help="Environment to fetch specs from",
    )
    parser.add_argument(
        "--file",
        help="Generate from local OpenAPI JSON file instead of service endpoint",
    )
    parser.add_argument(
        "--service-name", help="Service name when using --file (required with --file)"
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            generate_models(
                services=args.service,
                environment=args.environment,
                file_path=args.file,
                service_name=args.service_name,
            )
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
