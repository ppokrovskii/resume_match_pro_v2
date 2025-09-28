"""
Error handling utilities for FastAPI application
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    """Base exception for document service"""
    
    def __init__(self, message: str, code: str = "DOCUMENT_SERVICE_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class FileNotFoundError(DocumentServiceError):
    """File not found error"""
    
    def __init__(self, message: str = "File not found"):
        super().__init__(message, "FILE_NOT_FOUND", 404)


class FileValidationError(DocumentServiceError):
    """File validation error"""
    
    def __init__(self, message: str = "File validation failed"):
        super().__init__(message, "FILE_VALIDATION_ERROR", 400)


class StorageError(DocumentServiceError):
    """Storage operation error"""
    
    def __init__(self, message: str = "Storage operation failed", error_code: str = "STORAGE_ERROR", status_code: int = 500):
        super().__init__(message, error_code, status_code)


class DatabaseError(DocumentServiceError):
    """Database operation error"""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR", 500)


class AuthenticationError(DocumentServiceError):
    """Authentication error"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class AuthorizationError(DocumentServiceError):
    """Authorization error"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR", 403)


def create_error_response(
    error_code: str,
    message: str,
    details: Dict[str, Any] = None,
    status_code: int = 500,
    request: Request = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    
    error_response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message
        },
        "meta": {
            "service": "document-service",
            "version": "1.0.0"
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request:
        error_response["meta"].update({
            "endpoint": str(request.url.path),
            "method": request.method
        })
    
    return error_response


async def document_service_error_handler(request: Request, exc: DocumentServiceError):
    """Handle custom document service errors"""
    logger.error(f"Document service error: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            request=request
        )
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"validation_errors": exc.errors()},
            status_code=422,
            request=request
        )
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    
    # If detail is already a dict (from our custom exceptions), return it
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            status_code=exc.status_code,
            request=request
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            status_code=500,
            request=request
        )
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app"""
    
    # Custom exception handlers
    app.add_exception_handler(DocumentServiceError, document_service_error_handler)
    app.add_exception_handler(FileNotFoundError, document_service_error_handler)
    app.add_exception_handler(FileValidationError, document_service_error_handler)
    app.add_exception_handler(StorageError, document_service_error_handler)
    app.add_exception_handler(DatabaseError, document_service_error_handler)
    app.add_exception_handler(AuthenticationError, document_service_error_handler)
    app.add_exception_handler(AuthorizationError, document_service_error_handler)
    
    # Built-in exception handlers
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered successfully")

