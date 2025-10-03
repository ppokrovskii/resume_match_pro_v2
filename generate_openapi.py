#!/usr/bin/env python3
"""
Generate OpenAPI spec from document-service FastAPI app
"""
import os
import sys
import json
from pathlib import Path

# Add document-service to path
sys.path.insert(0, str(Path(__file__).parent / "document-service"))

# Mock environment variables to avoid database connection
os.environ.setdefault("DATABASE_URL", "sqlite:///mock.db")
os.environ.setdefault("AUTH0_DOMAIN", "mock.auth0.com")
os.environ.setdefault("AUTH0_API_IDENTIFIER", "mock-api")
os.environ.setdefault("AZURE_STORAGE_CONNECTION_STRING", "mock")

try:
    # Import the FastAPI app
    from main import create_app
    
    # Create app without lifespan (to avoid database init)
    from fastapi import FastAPI
    from routers.documents import router as documents_router
    from routers.health import router as health_router
    from routers.auth import router as auth_router
    
    app = FastAPI(
        title="Document Service API",
        description="Pure document storage and management microservice",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Include routers
    app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    
    # Generate OpenAPI spec
    openapi_spec = app.openapi()
    
    # Save to file
    with open("document_service_openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
    
    print("✅ OpenAPI spec generated successfully: document_service_openapi.json")
    print(f"   Title: {openapi_spec.get('info', {}).get('title')}")
    print(f"   Version: {openapi_spec.get('info', {}).get('version')}")
    print(f"   Paths: {len(openapi_spec.get('paths', {}))}")
    print(f"   Components: {len(openapi_spec.get('components', {}).get('schemas', {}))}")
    
except Exception as e:
    print(f"❌ Error generating OpenAPI spec: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

