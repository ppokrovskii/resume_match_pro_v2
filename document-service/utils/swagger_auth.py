"""Swagger UI Auth0 Integration with Token Proxy"""

import os
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def configure_swagger_auth(app: FastAPI):
    """Configure OpenAPI schema with Auth0 security schemes"""
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT Bearer Token from Auth0"
            },
            "OAuth2": {
                "type": "oauth2",
                "description": "Auth0 OAuth2 via proxy endpoint",
                "flows": {
                    "clientCredentials": {
                        "tokenUrl": "/auth/swagger-token",  # Our proxy endpoint
                        "scopes": {
                            "read:documents": "Read documents",
                            "write:documents": "Create and update documents", 
                            "delete:documents": "Delete documents"
                        }
                    }
                }
            }
        }
        
        # Apply security to all endpoints
        for path in openapi_schema["paths"]:
            for method in openapi_schema["paths"][path]:
                if method in ["get", "post", "put", "delete", "patch"]:
                    if "/auth/" not in path and "/health" not in path:
                        openapi_schema["paths"][path][method]["security"] = [
                            {"BearerAuth": []},
                            {"OAuth2": ["read:documents", "write:documents", "delete:documents"]}
                        ]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi


def get_swagger_ui_init_oauth():
    """Get OAuth2 initialization parameters for Swagger UI"""
    return {
        "clientId": os.getenv('AUTH0_CLIENT_ID'),
        "clientSecret": os.getenv('AUTH0_CLIENT_SECRET'),  # This should make Swagger UI send Basic Auth
        "realm": "document-service",
        "appName": "Document Service API",
        "scopeSeparator": " ",
        "scopes": "read:documents write:documents delete:documents",
        "useBasicAuthenticationWithAccessCodeGrant": True,  # Force Basic Auth
        # Try to send audience in form data instead of query params
        "additionalQueryStringParams": {},  # Remove audience from query params
        "audience": os.getenv('AUTH0_API_IDENTIFIER', 'https://api.resumematch.com/document-service')  # This might work better
    }
