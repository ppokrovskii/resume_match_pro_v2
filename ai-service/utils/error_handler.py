"""
Error handling utilities for AI service
"""

import logging
from typing import Dict, Any
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Base exception for AI service"""
    
    def __init__(self, message: str, code: str = "AI_SERVICE_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class EmbeddingGenerationError(AIServiceError):
    """Embedding generation error"""
    
    def __init__(self, message: str = "Embedding generation failed"):
        super().__init__(message, "EMBEDDING_GENERATION_ERROR", 500)


class SimilaritySearchError(AIServiceError):
    """Similarity search error"""
    
    def __init__(self, message: str = "Similarity search failed"):
        super().__init__(message, "SIMILARITY_SEARCH_ERROR", 500)


class MatchingError(AIServiceError):
    """Document matching error"""
    
    def __init__(self, message: str = "Document matching failed"):
        super().__init__(message, "MATCHING_ERROR", 500)


class DatabaseError(AIServiceError):
    """Database operation error"""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR", 500)


class AuthenticationError(AIServiceError):
    """Authentication error"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class AuthorizationError(AIServiceError):
    """Authorization error"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR", 403)


class RateLimitError(AIServiceError):
    """Rate limit exceeded error"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429)


class ModelUnavailableError(AIServiceError):
    """AI model unavailable error"""
    
    def __init__(self, message: str = "AI model temporarily unavailable"):
        super().__init__(message, "MODEL_UNAVAILABLE", 503)


def create_error_response(
    error_code: str,
    message: str,
    details: Dict[str, Any] = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {}
        },
        "meta": {
            "request_id": getattr(request, 'request_id', None),
            "endpoint": request.endpoint if request else None,
            "method": request.method if request else None,
            "service": "ai-service"
        }
    }


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for Flask application"""
    
    @app.errorhandler(AIServiceError)
    def handle_ai_service_error(error: AIServiceError):
        """Handle custom AI service errors"""
        logger.error(f"AI service error: {error.message}", exc_info=True)
        response = create_error_response(
            error.code,
            error.message,
            status_code=error.status_code
        )
        return jsonify(response), error.status_code
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        """Handle Pydantic validation errors"""
        logger.warning(f"Validation error: {error}")
        response = create_error_response(
            "VALIDATION_ERROR",
            "Request validation failed",
            {"validation_errors": error.errors()},
            400
        )
        return jsonify(response), 400
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP error {error.code}: {error.description}")
        response = create_error_response(
            f"HTTP_{error.code}",
            error.description or "HTTP error",
            status_code=error.code
        )
        return jsonify(response), error.code
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Handle rate limit errors"""
        response = create_error_response(
            "RATE_LIMIT_EXCEEDED",
            "Too many requests. Please try again later.",
            {"retry_after": 60},
            429
        )
        return jsonify(response), 429
    
    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Handle service unavailable errors"""
        response = create_error_response(
            "SERVICE_UNAVAILABLE",
            "AI service is temporarily unavailable",
            {"retry_after": 30},
            503
        )
        return jsonify(response), 503
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        """Handle unexpected errors"""
        logger.error(f"Unexpected error: {error}", exc_info=True)
        response = create_error_response(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred",
            status_code=500
        )
        return jsonify(response), 500
    
    @app.before_request
    def before_request():
        """Add request ID for tracing"""
        import uuid
        request.request_id = str(uuid.uuid4())
        logger.info(f"Request {request.request_id}: {request.method} {request.path}")
    
    @app.after_request
    def after_request(response):
        """Log response"""
        if hasattr(request, 'request_id'):
            logger.info(f"Response {request.request_id}: {response.status_code}")
        return response






