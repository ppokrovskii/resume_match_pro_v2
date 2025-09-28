"""
Unit tests for document download service methods

Following TDD principles as specified in repo rules:
- Tests focus on business logic and individual functions
- Tests use mocks for external dependencies
- Tests cover error scenarios and edge cases
- Tests ensure proper validation and error handling
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from io import BytesIO

from services.document_service import DocumentService
from services.storage_service import StorageService
from utils.fastapi_error_handler import DocumentServiceError, StorageError


class TestDocumentDownloadService:
    """Unit tests for document download service methods"""
    
    @pytest.fixture
    def mock_storage_service(self):
        """Mock storage service for unit tests"""
        mock_service = Mock(spec=StorageService)
        mock_service.download_file.return_value = (b"test file content", "application/pdf")
        return mock_service
    
    @pytest.fixture
    def document_service(self, mock_storage_service):
        """Document service with mocked dependencies"""
        service = DocumentService()
        service.storage_service = mock_storage_service
        return service
    
    def test_download_document_success(self, document_service, mock_storage_service):
        """
        Test Case: DOC-UNIT-001 - Successful document download
        Requirement: Core download functionality works correctly
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        from models.document import Document
        expected_document = Document(
            id=document_id,
            user_id=user_id,
            filename='test_document.pdf',
            content_type='application/pdf',
            storage_path='user123/documents/test_document.pdf',
            file_size=2048
        )
        
        # Mock the get_document method
        with patch.object(document_service, 'get_document', return_value=expected_document):
            mock_storage_service.download_file.return_value = (b"PDF content here", "application/pdf")
            
            # Act
            file_data, content_type, filename = document_service.download_document(document_id, user_id)
            
            # Assert
            assert file_data == b"PDF content here"
            assert content_type == "application/pdf"
            assert filename == "test_document.pdf"
            
            # Verify method calls
            mock_storage_service.download_file.assert_called_once_with('user123/documents/test_document.pdf')
    
    def test_download_document_not_found(self, document_service):
        """
        Test Case: DOC-UNIT-002 - Document not found in database
        Requirement: Handle missing documents gracefully
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Mock get_document to return None
        with patch.object(document_service, 'get_document', return_value=None):
            # Act & Assert
            with pytest.raises(DocumentServiceError, match="Document download failed"):
                document_service.download_document(document_id, user_id)
    
    def test_download_document_no_storage_path(self, document_service):
        """
        Test Case: DOC-UNIT-003 - Document exists but has no storage path
        Requirement: Handle corrupted document metadata
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        from models.document import Document
        document_without_storage = Document(
            id=document_id,
            user_id=user_id,
            filename='test.pdf',
            content_type='application/pdf',
            storage_path=None,  # Missing storage path
            file_size=1024
        )
        
        with patch.object(document_service, 'get_document', return_value=document_without_storage):
            # Act & Assert
            with pytest.raises(DocumentServiceError, match="Document download failed"):
                document_service.download_document(document_id, user_id)
    
    def test_download_document_empty_storage_path(self, document_service):
        """
        Test Case: DOC-UNIT-004 - Document has empty storage path
        Requirement: Handle edge cases in document metadata
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        from models.document import Document
        document_with_empty_storage = Document(
            id=document_id,
            user_id=user_id,
            filename='test.pdf',
            content_type='application/pdf',
            storage_path='',  # Empty storage path
            file_size=1024
        )
        
        with patch.object(document_service, 'get_document', return_value=document_with_empty_storage):
            # Act & Assert
            with pytest.raises(DocumentServiceError, match="Document download failed"):
                document_service.download_document(document_id, user_id)
    
    def test_download_document_storage_error(self, document_service, mock_storage_service):
        """
        Test Case: DOC-UNIT-005 - Storage service error handling
        Requirement: Handle storage service failures
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        from models.document import Document
        expected_document = Document(
            id=document_id,
            user_id=user_id,
            filename='test.pdf',
            content_type='application/pdf',
            storage_path='user123/documents/test.pdf',
            file_size=1024
        )
        
        with patch.object(document_service, 'get_document', return_value=expected_document):
            mock_storage_service.download_file.side_effect = StorageError("Blob not found")
            
            # Act & Assert
            with pytest.raises(StorageError, match="Blob not found"):
                document_service.download_document(document_id, user_id)
    
    def test_download_document_generic_exception(self, document_service, mock_storage_service):
        """
        Test Case: DOC-UNIT-006 - Generic exception handling
        Requirement: Handle unexpected errors gracefully
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        from models.document import Document
        expected_document = Document(
            id=document_id,
            user_id=user_id,
            filename='test.pdf',
            content_type='application/pdf',
            storage_path='user123/documents/test.pdf',
            file_size=1024
        )
        
        with patch.object(document_service, 'get_document', return_value=expected_document):
            mock_storage_service.download_file.side_effect = Exception("Unexpected error")
            
            # Act & Assert
            with pytest.raises(DocumentServiceError, match="Document download failed"):
                document_service.download_document(document_id, user_id)
    
    def test_download_document_different_file_types(self, document_service, mock_storage_service):
        """
        Test Case: DOC-UNIT-007 - Different file types handling
        Requirement: Support PDF, DOC, DOCX file types
        """
        test_cases = [
            {
                'filename': 'resume.pdf',
                'content_type': 'application/pdf',
                'file_content': b'%PDF-1.4 test content'
            },
            {
                'filename': 'resume.docx',
                'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'file_content': b'PK\x03\x04 docx content'
            },
            {
                'filename': 'resume.doc',
                'content_type': 'application/msword',
                'file_content': b'\xd0\xcf\x11\xe0 doc content'
            }
        ]
        
        for test_case in test_cases:
            # Arrange
            document_id = uuid.uuid4()
            user_id = uuid.uuid4()
            
            from models.document import Document
            document_data = Document(
                id=document_id,
                user_id=user_id,
                filename=test_case['filename'],
                content_type=test_case['content_type'],
                storage_path=f'user123/documents/{test_case["filename"]}',
                file_size=len(test_case['file_content'])
            )
            
            with patch.object(document_service, 'get_document', return_value=document_data):
                mock_storage_service.download_file.return_value = (
                    test_case['file_content'], 
                    test_case['content_type']
                )
                
                # Act
                file_data, content_type, filename = document_service.download_document(document_id, user_id)
                
                # Assert
                assert file_data == test_case['file_content']
                assert content_type == test_case['content_type']
                assert filename == test_case['filename']
    
    def test_download_document_large_file(self, document_service, mock_storage_service):
        """
        Test Case: DOC-UNIT-008 - Large file download handling
        Requirement: Handle large files up to 16MB
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Simulate 16MB file
        large_file_content = b"x" * (16 * 1024 * 1024)
        
        from models.document import Document
        large_document = Document(
            id=document_id,
            user_id=user_id,
            filename='large_document.pdf',
            content_type='application/pdf',
            storage_path='user123/documents/large_document.pdf',
            file_size=len(large_file_content)
        )
        
        with patch.object(document_service, 'get_document', return_value=large_document):
            mock_storage_service.download_file.return_value = (large_file_content, "application/pdf")
            
            # Act
            file_data, content_type, filename = document_service.download_document(document_id, user_id)
            
            # Assert
            assert len(file_data) == 16 * 1024 * 1024
            assert content_type == "application/pdf"
            assert filename == "large_document.pdf"
    
    def test_download_document_return_tuple_format(self, document_service, mock_storage_service):
        """
        Test Case: DOC-UNIT-009 - Verify return tuple format
        Requirement: Method returns (file_data, content_type, filename) tuple
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        from models.document import Document
        expected_document = Document(
            id=document_id,
            user_id=user_id,
            filename='test_return_format.pdf',
            content_type='application/pdf',
            storage_path='user123/documents/test_return_format.pdf',
            file_size=1024
        )
        
        with patch.object(document_service, 'get_document', return_value=expected_document):
            mock_storage_service.download_file.return_value = (b"test content", "application/pdf")
            
            # Act
            result = document_service.download_document(document_id, user_id)
            
            # Assert
            assert isinstance(result, tuple)
            assert len(result) == 3
            
            file_data, content_type, filename = result
            assert isinstance(file_data, bytes)
            assert isinstance(content_type, str)
            assert isinstance(filename, str)
    
    def test_download_document_user_isolation_logic(self, document_service):
        """
        Test Case: DOC-UNIT-010 - User isolation in service layer
        Requirement: Service layer enforces user isolation
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Mock get_document to return None (simulating user isolation)
        with patch.object(document_service, 'get_document', return_value=None):
            # Act & Assert
            with pytest.raises(DocumentServiceError, match="Document download failed"):
                document_service.download_document(document_id, user_id)