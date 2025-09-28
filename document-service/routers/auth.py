"""
Auth0 authentication endpoints for Swagger UI integration
Provides token generation and validation endpoints
"""

import os
import logging
import requests
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Form, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Pydantic models
class TokenRequest(BaseModel):
    """Token request model for client credentials flow"""
    client_id: str
    client_secret: str
    audience: Optional[str] = None
    grant_type: str = "client_credentials"







@router.post("/swagger-token", summary="Get Token for Swagger UI")
async def get_swagger_token(
    request: Request,
    grant_type: str = Form(...),
    scope: str = Form(...),
    audience: str = Form(None)  # Standard OAuth2 way
):
    """
    Proxy endpoint for Swagger UI to get Auth0 tokens
    
    Handles both Authorization header (Basic Auth) and form data for client credentials.
    This endpoint converts Swagger UI's form-encoded request to Auth0's JSON format.
    """
    try:
        auth0_domain = os.getenv('AUTH0_DOMAIN')
        api_audience = os.getenv('AUTH0_API_IDENTIFIER')
        
        # Try to get client credentials from Authorization header first
        client_id = None
        client_secret = None
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            # Decode Basic Auth header
            import base64
            try:
                encoded_credentials = auth_header.split(' ')[1]
                decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
                client_id, client_secret = decoded_credentials.split(':', 1)
                logger.info("Using client credentials from Authorization header")
            except Exception as e:
                logger.warning(f"Failed to decode Basic Auth header: {e}")
        
        # Fallback to environment variables if not in header
        if not client_id or not client_secret:
            client_id = os.getenv('AUTH0_CLIENT_ID')
            client_secret = os.getenv('AUTH0_CLIENT_SECRET')
            logger.info("Using client credentials from environment variables")
        
        if not all([auth0_domain, client_id, client_secret, api_audience]):
            logger.error("Missing Auth0 configuration")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_client",
                    "error_description": "Client authentication failed - missing configuration"
                }
            )
        
        # Get audience from form data first (correct OAuth2 way), then query params (Swagger UI quirk), then default
        target_audience = audience
        if not target_audience:
            # Fallback to query parameter if Swagger UI sends it there
            target_audience = request.query_params.get('audience')
        if not target_audience:
            # Final fallback to default
            target_audience = api_audience
            
        logger.info(f"Requesting token for audience: {target_audience}")
        
        # Make request to Auth0 with proper format
        token_url = f"https://{auth0_domain}/oauth/token"
        
        # Auth0 expects client credentials in the request body for M2M
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": target_audience,
            "grant_type": grant_type
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Making token request to: {token_url}")
        response = requests.post(token_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            token_data = response.json()
            logger.info("Successfully obtained Auth0 token")
            # Return in the format Swagger UI expects
            return {
                "access_token": token_data["access_token"],
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in", 3600),
                "scope": token_data.get("scope", scope)
            }
        else:
            error_data = response.json()
            logger.error(f"Auth0 token request failed: {response.status_code} - {error_data}")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token proxy failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "server_error", 
                "error_description": f"Token generation failed: {str(e)}"
            }
        )
