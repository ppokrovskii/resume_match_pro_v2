"""
Health check routes for FastAPI
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from services.document_service import DocumentService

router = APIRouter()

# Pydantic response models
class HealthResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    meta: Dict[str, str]



def get_document_service():
    """Lazy initialization of document service"""
    if not hasattr(get_document_service, '_service'):
        get_document_service._service = DocumentService()
    return get_document_service._service


@router.get("/", response_model=HealthResponse, summary="Health Check")
@router.get("/check", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """
    Comprehensive health check endpoint
    
    Returns the health status of all service components:
    - Database connectivity
    - Storage service availability
    - Overall service health
    """
    try:
        health_status = get_document_service().health_check()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        response = HealthResponse(
            success=True,
            data=health_status,
            meta={
                "service": "document-service",
                "version": "1.0.0"
            }
        )
        
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=response.dict())
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": {
                    "code": "HEALTH_CHECK_FAILED",
                    "message": str(e)
                },
                "meta": {
                    "service": "document-service",
                    "version": "1.0.0"
                }
            }
        )





