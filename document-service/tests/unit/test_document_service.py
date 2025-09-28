"""
Unit tests for DocumentService class

Following TDD principles:
- Test individual components in isolation
- Mock external dependencies
- Cover all business logic paths
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from services.document_service import DocumentService
from models.document import Document
from utils.fastapi_error_handler import DocumentServiceError, DatabaseError


class TestDocumentService:
    """Unit tests for DocumentService class"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock document repository"""
        return Mock()
    
    @pytest.fixture
    def mock_storage_service(self):
        """Mock storage service"""
        mock_service = Mock()
        mock_service.upload_file.return_value = "test/path/document.pdf"
        mock_service.download_file.return_value = (b"file content", "application/pdf")
        mock_service.delete_file.return_value = True
        mock_service.health_check.return_value = True
        return mock_service
    
    @pytest.fixture
    def document_service(self, mock_repository, mock_storage_service):
        """Create DocumentService with mocked dependencies"""
        with patch('services.document_service.DocumentRepository') as mock_repo_class:
            mock_repo_class.return_value = mock_repository
            
            with patch('services.document_service.get_storage_service') as mock_storage:
                mock_storage.return_value = mock_storage_service
                
                service = DocumentService()
                service.repository = mock_repository
                service.storage_service = mock_storage_service
                return service
    
    @pytest.mark.unit
    def test_upload_document_success(self, document_service, mock_repository, mock_storage_service):
        """
        Test Case: DOC-FUNC-004 - Parse and validate .docx Word document
        Requirement: REQ-2.1.4 - Accept Word (.doc, .docx) formats
        """
        # Arrange
        user_id = uuid.uuid4()
        file_data = b"sample file content"
        filename = "test_document.docx"
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        file_type = None
        
        # No text extraction in pure storage service
        with patch('services.document_service.sanitize_filename') as mock_sanitize:
            mock_sanitize.return_value = "test_document_sanitized.docx"
            
            # Mock repository methods
            document_id = uuid.uuid4()
            mock_repository.create_document.return_value = document_id
            mock_repository.get_document.return_value = {
                'id': document_id,
                'user_id': user_id,
                'organization_id': None,
                'filename': filename,
                'file_type': file_type,
                'content_type': content_type,
                'file_size': len(file_data),
                'storage_path': 'test/path/document.docx',
                'text_content': None,  # No text extraction
                'metadata': {"sanitized_filename": "test_document_sanitized.docx"},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Act
            result = document_service.upload_document(
                file_data=file_data,
                filename=filename,
                content_type=content_type,
                file_type=file_type,
                user_id=user_id
            )
            
            # Assert
            assert isinstance(result, Document)
            assert result.id == document_id
            assert result.filename == filename
            assert result.file_type == file_type
            assert result.text_content is None  # No text extraction
            
            # Verify storage service was called
            mock_storage_service.upload_file.assert_called_once_with(
                file_data=file_data,
                filename="test_document_sanitized.docx",
                content_type=content_type,
                user_id=str(user_id),
                file_type=file_type
            )
        
        # Verify repository was called
        mock_repository.create_document.assert_called_once()
        mock_repository.get_document.assert_called_once_with(document_id, user_id)
    
    @pytest.mark.unit
    def test_upload_document_text_extraction_failure(self, document_service, mock_repository, mock_storage_service):
        """
        Test Case: DOC-ERROR-004 - Handle corrupted Word file gracefully
        Requirement: REQ-7.1.2 - Handle corrupted documents gracefully
        """
        # Arrange
        user_id = uuid.uuid4()
        file_data = b"corrupted file content"
        filename = "corrupted_document.docx"
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        file_type = None
        
        # No text extraction in pure storage service
        with patch('services.document_service.sanitize_filename') as mock_sanitize:
            mock_sanitize.return_value = "corrupted_document_sanitized.docx"
            
            # Mock repository methods
            document_id = uuid.uuid4()
            mock_repository.create_document.return_value = document_id
            mock_repository.get_document.return_value = {
                'id': document_id,
                'user_id': user_id,
                'organization_id': None,
                'filename': filename,
                'file_type': file_type,
                'content_type': content_type,
                'file_size': len(file_data),
                'storage_path': 'test/path/document.docx',
                'text_content': None,  # No text extraction
                'metadata': {'sanitized_filename': 'corrupted_document_sanitized.docx'},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Act
            result = document_service.upload_document(
                file_data=file_data,
                filename=filename,
                content_type=content_type,
                file_type=file_type,
                user_id=user_id
            )
            
            # Assert - Upload should succeed (pure storage)
            assert isinstance(result, Document)
            assert result.text_content is None
            assert result.file_type == file_type
        
        # Verify storage and repository were still called
        mock_storage_service.upload_file.assert_called_once()
        mock_repository.create_document.assert_called_once()
    
    @pytest.mark.unit
    def test_upload_document_storage_failure_cleanup(self, document_service, mock_repository, mock_storage_service):
        """
        Test storage failure and cleanup behavior
        """
        # Arrange
        user_id = uuid.uuid4()
        file_data = b"sample file content"
        filename = "test_document.pdf"
        content_type = "application/pdf"
        file_type = None
        
        # Mock storage failure
        mock_storage_service.upload_file.side_effect = Exception("Storage upload failed")
        
        with patch('services.document_service.sanitize_filename') as mock_sanitize:
            mock_sanitize.return_value = "test_document_sanitized.pdf"
            
            # Act & Assert
            with pytest.raises(DocumentServiceError) as exc_info:
                document_service.upload_document(
                    file_data=file_data,
                    filename=filename,
                    content_type=content_type,
                    file_type=file_type,
                    user_id=user_id
                )
            
            assert "Document upload failed" in str(exc_info.value)
        
        # Verify repository was not called since storage failed
        mock_repository.create_document.assert_not_called()
    
    @pytest.mark.unit
    def test_get_document_success(self, document_service, mock_repository):
        """
        Test successful document retrieval
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_repository.get_document.return_value = {
            'id': document_id,
            'user_id': user_id,
            'organization_id': None,
            'filename': 'test.pdf',
            'file_type': None,
            'content_type': 'application/pdf',
            'file_size': 1024,
            'storage_path': 'test/path/document.pdf',
            'text_content': 'Sample content',
            'metadata': {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Act
        result = document_service.get_document(document_id, user_id)
        
        # Assert
        assert isinstance(result, Document)
        assert result.id == document_id
        assert result.user_id == user_id
        
        mock_repository.get_document.assert_called_once_with(document_id, user_id)
    
    @pytest.mark.unit
    def test_get_document_not_found(self, document_service, mock_repository):
        """
        Test document not found scenario
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_repository.get_document.return_value = None
        
        # Act
        result = document_service.get_document(document_id, user_id)
        
        # Assert
        assert result is None
        mock_repository.get_document.assert_called_once_with(document_id, user_id)
    
    @pytest.mark.unit
    def test_get_user_documents_with_pagination(self, document_service, mock_repository):
        """
        Test user documents retrieval with pagination
        """
        # Arrange
        user_id = uuid.uuid4()
        file_type = None
        limit = 10
        offset = 0
        
        mock_documents = [
            {
                'id': uuid.uuid4(),
                'user_id': user_id,
                'organization_id': None,
                'filename': f'document_{i}.pdf',
                'file_type': None,
                'content_type': 'application/pdf',
                'file_size': 1024,
                'storage_path': f'test/path/document_{i}.pdf',
                'text_content': f'Content {i}',
                'metadata': {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            for i in range(5)
        ]
        
        mock_repository.get_user_documents.return_value = mock_documents
        mock_repository.get_document_count.return_value = 25
        
        # Act
        documents, total_count = document_service.get_user_documents(
            user_id=user_id,
            file_type=file_type,
            limit=limit,
            offset=offset
        )
        
        # Assert
        assert len(documents) == 5
        assert total_count == 25
        assert all(isinstance(doc, Document) for doc in documents)
        
        mock_repository.get_user_documents.assert_called_once_with(user_id, file_type, limit, offset)
        mock_repository.get_document_count.assert_called_once_with(user_id, file_type)
    
    @pytest.mark.unit
    def test_delete_document_success(self, document_service, mock_repository, mock_storage_service):
        """
        Test successful document deletion
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_document_data = {
            'id': document_id,
            'user_id': user_id,
            'organization_id': None,
            'filename': 'test.pdf',
            'file_type': None,
            'content_type': 'application/pdf',
            'file_size': 1024,
            'storage_path': 'test/path/document.pdf',
            'text_content': 'Sample content',
            'metadata': {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_repository.get_document.return_value = mock_document_data
        mock_repository.delete_document.return_value = True
        
        # Act
        result = document_service.delete_document(document_id, user_id)
        
        # Assert
        assert result is True
        
        mock_repository.get_document.assert_called_once_with(document_id, user_id)
        mock_storage_service.delete_file.assert_called_once_with('test/path/document.pdf')
        mock_repository.delete_document.assert_called_once_with(document_id, user_id)
    
    @pytest.mark.unit
    def test_delete_document_not_found(self, document_service, mock_repository):
        """
        Test deletion of non-existent document
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_repository.get_document.return_value = None
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            document_service.delete_document(document_id, user_id)
        
        mock_repository.get_document.assert_called_once_with(document_id, user_id)
        mock_repository.delete_document.assert_not_called()
    
    @pytest.mark.unit
    def test_delete_document_storage_failure_continues(self, document_service, mock_repository, mock_storage_service):
        """
        Test that document deletion continues even if storage deletion fails
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_document_data = {
            'id': document_id,
            'user_id': user_id,
            'organization_id': None,
            'filename': 'test.pdf',
            'file_type': None,
            'content_type': 'application/pdf',
            'file_size': 1024,
            'storage_path': 'test/path/document.pdf',
            'text_content': 'Sample content',
            'metadata': {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_repository.get_document.return_value = mock_document_data
        mock_repository.delete_document.return_value = True
        mock_storage_service.delete_file.side_effect = Exception("Storage service unavailable")
        
        # Act
        result = document_service.delete_document(document_id, user_id)
        
        # Assert - Should still succeed despite storage failure
        assert result is True
        mock_repository.get_document.assert_called_once_with(document_id, user_id)
        mock_storage_service.delete_file.assert_called_once_with('test/path/document.pdf')
        mock_repository.delete_document.assert_called_once_with(document_id, user_id)
    
    @pytest.mark.unit
    def test_delete_document_no_storage_path(self, document_service, mock_repository, mock_storage_service):
        """
        Test document deletion when document has no storage path
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_document_data = {
            'id': document_id,
            'user_id': user_id,
            'organization_id': None,
            'filename': 'test.pdf',
            'file_type': None,
            'content_type': 'application/pdf',
            'file_size': 1024,
            'storage_path': None,  # No storage path
            'text_content': 'Sample content',
            'metadata': {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_repository.get_document.return_value = mock_document_data
        mock_repository.delete_document.return_value = True
        
        # Act
        result = document_service.delete_document(document_id, user_id)
        
        # Assert
        assert result is True
        mock_repository.get_document.assert_called_once_with(document_id, user_id)
        mock_storage_service.delete_file.assert_not_called()  # Should not try to delete from storage
        mock_repository.delete_document.assert_called_once_with(document_id, user_id)
    
    @pytest.mark.unit
    def test_delete_document_database_failure(self, document_service, mock_repository, mock_storage_service):
        """
        Test document deletion when database deletion fails
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_document_data = {
            'id': document_id,
            'user_id': user_id,
            'organization_id': None,
            'filename': 'test.pdf',
            'file_type': None,
            'content_type': 'application/pdf',
            'file_size': 1024,
            'storage_path': 'test/path/document.pdf',
            'text_content': 'Sample content',
            'metadata': {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_repository.get_document.return_value = mock_document_data
        mock_repository.delete_document.return_value = False  # Database deletion fails
        
        # Act
        result = document_service.delete_document(document_id, user_id)
        
        # Assert
        assert result is False
        mock_repository.get_document.assert_called_once_with(document_id, user_id)
        mock_storage_service.delete_file.assert_called_once_with('test/path/document.pdf')
        mock_repository.delete_document.assert_called_once_with(document_id, user_id)
    
    @pytest.mark.unit  
    def test_delete_document_publishes_event_on_success(self, document_service, mock_repository, mock_storage_service):
        """
        Test that document.deleted event is published on successful deletion
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_document_data = {
            'id': document_id,
            'user_id': user_id,
            'organization_id': None,
            'filename': 'test.pdf',
            'file_type': None,
            'content_type': 'application/pdf',
            'file_size': 1024,
            'storage_path': 'test/path/document.pdf',
            'text_content': 'Sample content',
            'metadata': {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_repository.get_document.return_value = mock_document_data
        mock_repository.delete_document.return_value = True
        
        # Act
        with patch('services.document_service.publish_document_deleted') as mock_publish:
            mock_publish.return_value = True
            result = document_service.delete_document(document_id, user_id)
        
        # Assert
        assert result is True
        mock_publish.assert_called_once_with(document_id, user_id)
    
    @pytest.mark.unit
    def test_delete_document_event_publish_failure_does_not_fail_deletion(self, document_service, mock_repository, mock_storage_service):
        """
        Test that event publishing failure does not cause deletion to fail
        """
        # Arrange
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        mock_document_data = {
            'id': document_id,
            'user_id': user_id,
            'organization_id': None,
            'filename': 'test.pdf',
            'file_type': None,
            'content_type': 'application/pdf',
            'file_size': 1024,
            'storage_path': 'test/path/document.pdf',
            'text_content': 'Sample content',
            'metadata': {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_repository.get_document.return_value = mock_document_data
        mock_repository.delete_document.return_value = True
        
        # Act
        with patch('services.document_service.publish_document_deleted') as mock_publish:
            mock_publish.side_effect = Exception("Event publishing failed")
            result = document_service.delete_document(document_id, user_id)
        
        # Assert - Deletion should still succeed
        assert result is True
        mock_publish.assert_called_once_with(document_id, user_id)
    
    @pytest.mark.unit
    def test_search_documents(self, document_service, mock_repository):
        """
        Test document search functionality
        """
        # Arrange
        user_id = uuid.uuid4()
        query = "python developer"
        file_type = None
        limit = 20
        offset = 0
        
        mock_search_results = [
            {
                'id': uuid.uuid4(),
                'user_id': user_id,
                'organization_id': None,
                'filename': 'python_dev_cv.pdf',
                'file_type': None,
                'content_type': 'application/pdf',
                'file_size': 1024,
                'storage_path': 'test/path/python_dev_cv.pdf',
                'text_content': 'Python developer with 5 years experience',
                'metadata': {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        mock_repository.search_documents.return_value = mock_search_results
        
        # Act
        results = document_service.search_documents(
            user_id=user_id,
            query=query,
            file_type=file_type,
            limit=limit,
            offset=offset
        )
        
        # Assert
        assert len(results) == 1
        assert isinstance(results[0], Document)
        assert "python" in results[0].text_content.lower()
        
        mock_repository.search_documents.assert_called_once_with(
            user_id, query, file_type, limit, offset
        )
    
    @pytest.mark.unit
    def test_health_check(self, document_service, mock_repository, mock_storage_service):
        """
        Test service health check
        """
        # Arrange
        mock_storage_service.health_check.return_value = True
        
        # Act
        health_status = document_service.health_check()
        
        # Assert
        assert health_status['status'] == 'healthy'
        assert health_status['database'] == 'healthy'
        assert health_status['storage'] == 'healthy'
        assert 'timestamp' in health_status
        
        mock_storage_service.health_check.assert_called_once()
    
    @pytest.mark.unit
    def test_health_check_database_unhealthy(self, document_service, mock_repository, mock_storage_service):
        """
        Test health check with database issues
        """
        # Arrange
        mock_repository.get_document_count.side_effect = Exception("Database connection failed")
        mock_storage_service.health_check.return_value = True
        
        # Act
        health_status = document_service.health_check()
        
        # Assert
        assert health_status['status'] == 'unhealthy'
        assert health_status['database'] == 'unhealthy'
        assert health_status['storage'] == 'healthy'
    
    @pytest.mark.unit
    def test_health_check_storage_unhealthy(self, document_service, mock_repository, mock_storage_service):
        """
        Test health check with storage issues
        """
        # Arrange
        mock_storage_service.health_check.return_value = False
        
        # Act
        health_status = document_service.health_check()
        
        # Assert
        assert health_status['status'] == 'unhealthy'
        assert health_status['database'] == 'healthy'
        assert health_status['storage'] == 'unhealthy'




