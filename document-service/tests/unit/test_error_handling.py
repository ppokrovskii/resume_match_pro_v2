"""
Unit tests for error handling and standardized responses
Following TDD approach as per project requirements
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from utils.fastapi_error_handler import (
    DocumentServiceError,
    FileNotFoundError,
    FileValidationError,
    StorageError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    create_error_response,
    document_service_error_handler,
    validation_error_handler,
    http_exception_handler,
    general_exception_handler,
    register_exception_handlers
)


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_document_service_error_default(self):
        """Test DocumentServiceError with default values"""
        error = DocumentServiceError("Test error")
        
        assert error.message == "Test error"
        assert error.code == "DOCUMENT_SERVICE_ERROR"
        assert error.status_code == 500
        assert str(error) == "Test error"
    
    def test_document_service_error_custom(self):
        """Test DocumentServiceError with custom values"""
        error = DocumentServiceError("Custom error", "CUSTOM_CODE", 400)
        
        assert error.message == "Custom error"
        assert error.code == "CUSTOM_CODE"
        assert error.status_code == 400
    
    def test_file_not_found_error(self):
        """Test FileNotFoundError"""
        error = FileNotFoundError("File missing")
        
        assert error.message == "File missing"
        assert error.code == "FILE_NOT_FOUND"
        assert error.status_code == 404
    
    def test_file_not_found_error_default(self):
        """Test FileNotFoundError with default message"""
        error = FileNotFoundError()
        
        assert error.message == "File not found"
        assert error.code == "FILE_NOT_FOUND"
        assert error.status_code == 404
    
    def test_file_validation_error(self):
        """Test FileValidationError"""
        error = FileValidationError("Invalid file format")
        
        assert error.message == "Invalid file format"
        assert error.code == "FILE_VALIDATION_ERROR"
        assert error.status_code == 400
    
    def test_storage_error_default(self):
        """Test StorageError with default values"""
        error = StorageError("Storage failed")
        
        assert error.message == "Storage failed"
        assert error.code == "STORAGE_ERROR"
        assert error.status_code == 500
    
    def test_storage_error_custom(self):
        """Test StorageError with custom values"""
        error = StorageError("Upload failed", "UPLOAD_ERROR", 503)
        
        assert error.message == "Upload failed"
        assert error.code == "UPLOAD_ERROR"
        assert error.status_code == 503
    
    def test_database_error(self):
        """Test DatabaseError"""
        error = DatabaseError("Connection failed")
        
        assert error.message == "Connection failed"
        assert error.code == "DATABASE_ERROR"
        assert error.status_code == 500
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError("Invalid token")
        
        assert error.message == "Invalid token"
        assert error.code == "AUTHENTICATION_ERROR"
        assert error.status_code == 401
    
    def test_authorization_error(self):
        """Test AuthorizationError"""
        error = AuthorizationError("Insufficient permissions")
        
        assert error.message == "Insufficient permissions"
        assert error.code == "AUTHORIZATION_ERROR"
        assert error.status_code == 403


class TestErrorResponseCreation:
    """Test error response creation utility"""
    
    def test_create_error_response_minimal(self):
        """Test error response creation with minimal parameters"""
        response = create_error_response("TEST_ERROR", "Test message")
        
        assert response["success"] is False
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["message"] == "Test message"
        assert response["meta"]["service"] == "document-service"
        assert response["meta"]["version"] == "1.0.0"
        assert "details" not in response["error"]
    
    def test_create_error_response_with_details(self):
        """Test error response creation with details"""
        details = {"field": "filename", "issue": "required"}
        response = create_error_response(
            "VALIDATION_ERROR",
            "Validation failed",
            details=details,
            status_code=422
        )
        
        assert response["success"] is False
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Validation failed"
        assert response["error"]["details"] == details
        assert response["meta"]["service"] == "document-service"
    
    def test_create_error_response_with_request(self):
        """Test error response creation with request context"""
        mock_request = Mock()
        mock_request.url.path = "/api/v1/documents/upload"
        mock_request.method = "POST"
        
        response = create_error_response(
            "FILE_ERROR",
            "File processing failed",
            request=mock_request
        )
        
        assert response["meta"]["endpoint"] == "/api/v1/documents/upload"
        assert response["meta"]["method"] == "POST"


class TestErrorHandlers:
    """Test error handler functions"""
    
    @pytest.mark.asyncio
    async def test_document_service_error_handler(self):
        """Test DocumentServiceError handler"""
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        
        error = FileValidationError("Invalid file type")
        
        with patch('utils.fastapi_error_handler.logger') as mock_logger:
            response = await document_service_error_handler(mock_request, error)
            
            assert response.status_code == 400
            content = response.body.decode()
            assert "FILE_VALIDATION_ERROR" in content
            assert "Invalid file type" in content
            mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validation_error_handler(self):
        """Test RequestValidationError handler"""
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.method = "POST"
        
        # Create a mock validation error
        validation_errors = [
            {
                "loc": ("body", "filename"),
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
        
        # Mock RequestValidationError
        with patch('pydantic.error_wrappers.ErrorWrapper'):
            error = RequestValidationError(validation_errors)
            
            with patch('utils.fastapi_error_handler.logger') as mock_logger:
                response = await validation_error_handler(mock_request, error)
                
                assert response.status_code == 422
                content = response.body.decode()
                assert "VALIDATION_ERROR" in content
                assert "Request validation failed" in content
                mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_http_exception_handler_with_dict_detail(self):
        """Test HTTP exception handler with dict detail"""
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        
        error_detail = {
            "success": False,
            "error": {
                "code": "CUSTOM_ERROR",
                "message": "Custom error message"
            }
        }
        error = StarletteHTTPException(status_code=400, detail=error_detail)
        
        with patch('utils.fastapi_error_handler.logger') as mock_logger:
            response = await http_exception_handler(mock_request, error)
            
            assert response.status_code == 400
            content = response.body.decode()
            assert "CUSTOM_ERROR" in content
            mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_http_exception_handler_with_string_detail(self):
        """Test HTTP exception handler with string detail"""
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        
        error = StarletteHTTPException(status_code=404, detail="Not found")
        
        with patch('utils.fastapi_error_handler.logger') as mock_logger:
            response = await http_exception_handler(mock_request, error)
            
            assert response.status_code == 404
            content = response.body.decode()
            assert "HTTP_404" in content
            assert "Not found" in content
            mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_general_exception_handler(self):
        """Test general exception handler"""
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        
        error = Exception("Unexpected error")
        
        with patch('utils.fastapi_error_handler.logger') as mock_logger:
            response = await general_exception_handler(mock_request, error)
            
            assert response.status_code == 500
            content = response.body.decode()
            assert "INTERNAL_SERVER_ERROR" in content
            assert "An unexpected error occurred" in content
            mock_logger.error.assert_called_once_with(
                "Unexpected error: Unexpected error",
                exc_info=True
            )


class TestExceptionHandlerRegistration:
    """Test exception handler registration"""
    
    def test_register_exception_handlers(self):
        """Test registration of all exception handlers"""
        mock_app = Mock()
        
        with patch('utils.fastapi_error_handler.logger') as mock_logger:
            register_exception_handlers(mock_app)
            
            # Verify all handlers are registered
            expected_calls = [
                (DocumentServiceError,),
                (FileNotFoundError,),
                (FileValidationError,),
                (StorageError,),
                (DatabaseError,),
                (AuthenticationError,),
                (AuthorizationError,),
                (RequestValidationError,),
                (StarletteHTTPException,),
                (Exception,)
            ]
            
            assert mock_app.add_exception_handler.call_count == len(expected_calls)
            mock_logger.info.assert_called_once_with("Exception handlers registered successfully")


class TestErrorResponseConsistency:
    """Test error response format consistency"""
    
    @pytest.mark.asyncio
    async def test_all_error_responses_have_consistent_format(self):
        """Test that all error handlers produce consistent response format"""
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.method = "POST"
        
        # Test DocumentServiceError
        doc_error = FileValidationError("File error")
        doc_response = await document_service_error_handler(mock_request, doc_error)
        doc_content = eval(doc_response.body.decode())
        
        assert "success" in doc_content
        assert "error" in doc_content
        assert "meta" in doc_content
        assert doc_content["success"] is False
        assert "code" in doc_content["error"]
        assert "message" in doc_content["error"]
        
        # Test ValidationError
        validation_errors = [{"loc": ("field",), "msg": "error", "type": "value_error"}]
        val_error = RequestValidationError(validation_errors)
        val_response = await validation_error_handler(mock_request, val_error)
        val_content = eval(val_response.body.decode())
        
        assert "success" in val_content
        assert "error" in val_content
        assert "meta" in val_content
        assert val_content["success"] is False
        
        # Test HTTPException
        http_error = StarletteHTTPException(status_code=404, detail="Not found")
        http_response = await http_exception_handler(mock_request, http_error)
        http_content = eval(http_response.body.decode())
        
        assert "success" in http_content
        assert "error" in http_content
        assert "meta" in http_content
        assert http_content["success"] is False
        
        # Test General Exception
        gen_error = Exception("General error")
        gen_response = await general_exception_handler(mock_request, gen_error)
        gen_content = eval(gen_response.body.decode())
        
        assert "success" in gen_content
        assert "error" in gen_content
        assert "meta" in gen_content
        assert gen_content["success"] is False


class TestErrorCodeStandardization:
    """Test error code standardization across the application"""
    
    def test_error_codes_are_uppercase_snake_case(self):
        """Test that all error codes follow uppercase snake_case convention"""
        # Test custom exceptions
        assert DocumentServiceError("test").code == "DOCUMENT_SERVICE_ERROR"
        assert FileNotFoundError().code == "FILE_NOT_FOUND"
        assert FileValidationError().code == "FILE_VALIDATION_ERROR"
        assert StorageError().code == "STORAGE_ERROR"
        assert DatabaseError().code == "DATABASE_ERROR"
        assert AuthenticationError().code == "AUTHENTICATION_ERROR"
        assert AuthorizationError().code == "AUTHORIZATION_ERROR"
        
        # Test that codes don't contain spaces or special characters
        for error_class in [DocumentServiceError, FileNotFoundError, FileValidationError,
                           StorageError, DatabaseError, AuthenticationError, AuthorizationError]:
            error = error_class("test")
            assert " " not in error.code
            assert error.code.isupper()
            assert error.code.replace("_", "").isalnum()
    
    def test_error_messages_are_descriptive(self):
        """Test that error messages are descriptive and user-friendly"""
        # Test that default messages are meaningful
        assert "not found" in FileNotFoundError().message.lower()
        assert "validation" in FileValidationError().message.lower()
        assert "storage" in StorageError().message.lower()
        assert "database" in DatabaseError().message.lower()
        assert "authentication" in AuthenticationError().message.lower()
        assert "access" in AuthorizationError().message.lower()


class TestErrorLogging:
    """Test error logging functionality"""
    
    @pytest.mark.asyncio
    async def test_error_handlers_log_errors(self):
        """Test that error handlers properly log errors"""
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.method = "POST"
        
        with patch('utils.fastapi_error_handler.logger') as mock_logger:
            # Test DocumentServiceError logging
            error = FileValidationError("Test validation error")
            await document_service_error_handler(mock_request, error)
            mock_logger.error.assert_called_with("Document service error: Test validation error")
            
            mock_logger.reset_mock()
            
            # Test ValidationError logging
            validation_errors = [{"loc": ("field",), "msg": "error", "type": "value_error"}]
            val_error = RequestValidationError(validation_errors)
            await validation_error_handler(mock_request, val_error)
            mock_logger.error.assert_called_with(f"Validation error: {val_error.errors()}")
            
            mock_logger.reset_mock()
            
            # Test HTTPException logging
            http_error = StarletteHTTPException(status_code=404, detail="Not found")
            await http_exception_handler(mock_request, http_error)
            mock_logger.error.assert_called_with("HTTP error 404: Not found")
            
            mock_logger.reset_mock()
            
            # Test General Exception logging with exc_info
            gen_error = Exception("General error")
            await general_exception_handler(mock_request, gen_error)
            mock_logger.error.assert_called_with("Unexpected error: General error", exc_info=True)


# Integration tests for error handling
class TestErrorHandlingIntegration:
    """Integration tests for complete error handling flow"""
    
    def test_error_inheritance_hierarchy(self):
        """Test that custom errors inherit properly from DocumentServiceError"""
        # Test inheritance
        assert issubclass(FileNotFoundError, DocumentServiceError)
        assert issubclass(FileValidationError, DocumentServiceError)
        assert issubclass(StorageError, DocumentServiceError)
        assert issubclass(DatabaseError, DocumentServiceError)
        assert issubclass(AuthenticationError, DocumentServiceError)
        assert issubclass(AuthorizationError, DocumentServiceError)
        
        # Test that they're all exceptions
        for error_class in [FileNotFoundError, FileValidationError, StorageError,
                           DatabaseError, AuthenticationError, AuthorizationError]:
            assert issubclass(error_class, Exception)
    
    @pytest.mark.asyncio
    async def test_error_handler_chain(self):
        """Test that error handlers work correctly in a chain"""
        mock_request = Mock()
        mock_request.url.path = "/api/v1/documents"
        mock_request.method = "POST"
        
        # Test that more specific handlers are called for specific errors
        file_error = FileValidationError("Invalid file")
        response = await document_service_error_handler(mock_request, file_error)
        
        assert response.status_code == 400
        content = eval(response.body.decode())
        assert content["error"]["code"] == "FILE_VALIDATION_ERROR"
        
        # Test that general handler catches unexpected errors
        unexpected_error = ValueError("Unexpected value error")
        response = await general_exception_handler(mock_request, unexpected_error)
        
        assert response.status_code == 500
        content = eval(response.body.decode())
        assert content["error"]["code"] == "INTERNAL_SERVER_ERROR"

