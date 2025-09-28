"""
Unit tests to reproduce and fix DELETE endpoint exception handling bug

The bug: When get_document() raises DatabaseError, DELETE returns 500 instead of 404
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from fastapi import HTTPException

from routers.documents import delete_document
from utils.fastapi_error_handler import DatabaseError


class TestDeleteExceptionHandling:
    """Test DELETE endpoint exception handling"""
    
    @pytest.mark.unit
    def test_delete_document_database_error_should_return_404(self):
        """
        Test Case: DELETE should return 404 when get_document raises DatabaseError
        
        BUG: Currently returns 500 because DatabaseError is not caught as "not found"
        FIX: Should catch DatabaseError and return 404
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Mock document service that raises DatabaseError in get_document
        mock_service = Mock()
        mock_service.delete_document.side_effect = DatabaseError("Database connection failed")
        
        # Act & Assert - This should raise HTTPException with 404, not 500
        with patch('routers.documents.get_document_service') as mock_get_service:
            mock_get_service.return_value = mock_service
            
            with pytest.raises(HTTPException) as exc_info:
                # This is an async function, but we're testing the exception handling
                import asyncio
                asyncio.run(delete_document(document_id, user_id))
            
            # Currently this fails because DatabaseError causes 500
            # After fix, this should be 404
            print(f"Exception status code: {exc_info.value.status_code}")
            print(f"Exception detail: {exc_info.value.detail}")
            
            # This assertion will FAIL initially (reproducing the bug)
            # After we fix it, this should PASS
            assert exc_info.value.status_code == 404, f"Expected 404, got {exc_info.value.status_code}"
            assert "DOCUMENT_NOT_FOUND" in str(exc_info.value.detail)
    
    @pytest.mark.unit
    def test_delete_document_file_not_found_returns_404(self):
        """
        Test Case: DELETE should return 404 when service raises FileNotFoundError
        This case should already work correctly
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Mock document service that raises FileNotFoundError
        mock_service = Mock()
        mock_service.delete_document.side_effect = FileNotFoundError("Document not found")
        
        # Act & Assert
        with patch('routers.documents.get_document_service') as mock_get_service:
            mock_get_service.return_value = mock_service
            
            with pytest.raises(HTTPException) as exc_info:
                import asyncio
                asyncio.run(delete_document(document_id, user_id))
            
            # This should work correctly (return 404)
            assert exc_info.value.status_code == 404
            assert "DOCUMENT_NOT_FOUND" in str(exc_info.value.detail)
    
    @pytest.mark.unit
    def test_delete_document_generic_error_returns_500(self):
        """
        Test Case: DELETE should return 500 for genuine server errors
        This should continue to work as expected
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Mock document service that raises a generic error
        mock_service = Mock()
        mock_service.delete_document.side_effect = RuntimeError("Storage service crashed")
        
        # Act & Assert
        with patch('routers.documents.get_document_service') as mock_get_service:
            mock_get_service.return_value = mock_service
            
            with pytest.raises(HTTPException) as exc_info:
                import asyncio
                asyncio.run(delete_document(document_id, user_id))
            
            # This should return 500 for genuine server errors
            assert exc_info.value.status_code == 500
            assert "DELETE_FAILED" in str(exc_info.value.detail)
