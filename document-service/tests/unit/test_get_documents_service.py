"""
Unit tests for DocumentService.get_user_documents method

Following TDD principles:
- Test individual components in isolation
- Mock external dependencies
- Cover all business logic paths
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from datetime import datetime

from services.document_service import DocumentService
from models.document import Document
from utils.fastapi_error_handler import DatabaseError


class TestDocumentServiceGetDocuments:
    """Unit tests for DocumentService.get_user_documents method"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock document repository"""
        return Mock()
    
    @pytest.fixture
    def mock_storage_service(self):
        """Mock storage service"""
        mock_service = Mock()
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
    def test_get_user_documents_empty_result(self, document_service, mock_repository):
        """
        Test getting documents for user with no documents
        """
        # Arrange
        user_id = uuid.uuid4()
        mock_repository.get_user_documents.return_value = []
        mock_repository.get_document_count.return_value = 0
        
        # Act
        documents, total_count = document_service.get_user_documents(user_id)
        
        # Assert
        assert documents == []
        assert total_count == 0
        
        mock_repository.get_user_documents.assert_called_once_with(user_id, None, 50, 0)
        mock_repository.get_document_count.assert_called_once_with(user_id, None)
    
    @pytest.mark.unit
    def test_get_user_documents_with_results(self, document_service, mock_repository):
        """
        Test getting documents for user with documents
        """
        # Arrange
        user_id = uuid.uuid4()
        document_id1 = uuid.uuid4()
        document_id2 = uuid.uuid4()
        
        mock_documents = [
            {
                'id': document_id1,
                'user_id': user_id,
                'organization_id': None,
                'filename': 'cv1.pdf',
                'file_type': 'cv',
                'content_type': 'application/pdf',
                'file_size': 1024,
                'storage_path': 'test/path/cv1.pdf',
                'text_content': 'CV content 1',
                'metadata': {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'id': document_id2,
                'user_id': user_id,
                'organization_id': None,
                'filename': 'jd1.docx',
                'file_type': 'jd',
                'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'file_size': 2048,
                'storage_path': 'test/path/jd1.docx',
                'text_content': 'JD content 1',
                'metadata': {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        mock_repository.get_user_documents.return_value = mock_documents
        mock_repository.get_document_count.return_value = 2
        
        # Act
        documents, total_count = document_service.get_user_documents(user_id)
        
        # Assert
        assert len(documents) == 2
        assert total_count == 2
        assert all(isinstance(doc, Document) for doc in documents)
        
        # Verify document details
        assert documents[0].id == document_id1
        assert documents[0].filename == 'cv1.pdf'
        assert documents[0].file_type == 'cv'
        
        assert documents[1].id == document_id2
        assert documents[1].filename == 'jd1.docx'
        assert documents[1].file_type == 'jd'
        
        mock_repository.get_user_documents.assert_called_once_with(user_id, None, 50, 0)
        mock_repository.get_document_count.assert_called_once_with(user_id, None)
    
    @pytest.mark.unit
    def test_get_user_documents_with_file_type_filter(self, document_service, mock_repository):
        """
        Test getting documents with file_type filter
        """
        # Arrange
        user_id = uuid.uuid4()
        file_type = "cv"
        
        mock_documents = [
            {
                'id': uuid.uuid4(),
                'user_id': user_id,
                'organization_id': None,
                'filename': 'cv1.pdf',
                'file_type': 'cv',
                'content_type': 'application/pdf',
                'file_size': 1024,
                'storage_path': 'test/path/cv1.pdf',
                'text_content': 'CV content 1',
                'metadata': {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        mock_repository.get_user_documents.return_value = mock_documents
        mock_repository.get_document_count.return_value = 1
        
        # Act
        documents, total_count = document_service.get_user_documents(
            user_id=user_id,
            file_type=file_type
        )
        
        # Assert
        assert len(documents) == 1
        assert total_count == 1
        assert documents[0].file_type == 'cv'
        
        mock_repository.get_user_documents.assert_called_once_with(user_id, file_type, 50, 0)
        mock_repository.get_document_count.assert_called_once_with(user_id, file_type)
    
    @pytest.mark.unit
    def test_get_user_documents_with_pagination(self, document_service, mock_repository):
        """
        Test getting documents with custom pagination parameters
        """
        # Arrange
        user_id = uuid.uuid4()
        limit = 10
        offset = 20
        
        mock_documents = [
            {
                'id': uuid.uuid4(),
                'user_id': user_id,
                'organization_id': None,
                'filename': 'cv1.pdf',
                'file_type': 'cv',
                'content_type': 'application/pdf',
                'file_size': 1024,
                'storage_path': 'test/path/cv1.pdf',
                'text_content': 'CV content 1',
                'metadata': {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        mock_repository.get_user_documents.return_value = mock_documents
        mock_repository.get_document_count.return_value = 50
        
        # Act
        documents, total_count = document_service.get_user_documents(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Assert
        assert len(documents) == 1
        assert total_count == 50
        
        mock_repository.get_user_documents.assert_called_once_with(user_id, None, limit, offset)
        mock_repository.get_document_count.assert_called_once_with(user_id, None)
    
    @pytest.mark.unit
    def test_get_user_documents_with_all_parameters(self, document_service, mock_repository):
        """
        Test getting documents with all parameters specified
        """
        # Arrange
        user_id = uuid.uuid4()
        file_type = "jd"
        limit = 5
        offset = 10
        
        mock_documents = []
        mock_repository.get_user_documents.return_value = mock_documents
        mock_repository.get_document_count.return_value = 0
        
        # Act
        documents, total_count = document_service.get_user_documents(
            user_id=user_id,
            file_type=file_type,
            limit=limit,
            offset=offset
        )
        
        # Assert
        assert documents == []
        assert total_count == 0
        
        mock_repository.get_user_documents.assert_called_once_with(user_id, file_type, limit, offset)
        mock_repository.get_document_count.assert_called_once_with(user_id, file_type)
    
    @pytest.mark.unit
    def test_get_user_documents_database_error(self, document_service, mock_repository):
        """
        Test error handling when database operation fails
        """
        # Arrange
        user_id = uuid.uuid4()
        mock_repository.get_user_documents.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            document_service.get_user_documents(user_id)
        
        assert "Failed to retrieve documents" in str(exc_info.value)
        mock_repository.get_user_documents.assert_called_once_with(user_id, None, 50, 0)
    
    @pytest.mark.unit
    def test_get_user_documents_count_error(self, document_service, mock_repository):
        """
        Test error handling when document count operation fails
        """
        # Arrange
        user_id = uuid.uuid4()
        mock_repository.get_user_documents.return_value = []
        mock_repository.get_document_count.side_effect = Exception("Count query failed")
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            document_service.get_user_documents(user_id)
        
        assert "Failed to retrieve documents" in str(exc_info.value)
        mock_repository.get_user_documents.assert_called_once_with(user_id, None, 50, 0)
        mock_repository.get_document_count.assert_called_once_with(user_id, None)
    
    @pytest.mark.unit
    def test_get_user_documents_document_conversion_error(self, document_service, mock_repository):
        """
        Test error handling when Document model conversion fails
        """
        # Arrange
        user_id = uuid.uuid4()
        
        # Mock document with invalid data that will cause Document model creation to fail
        mock_documents = [
            {
                'id': 'invalid-uuid',  # Invalid UUID format
                'user_id': user_id,
                'filename': 'cv1.pdf',
                'file_type': 'cv',
                'content_type': 'application/pdf',
                'file_size': 1024,
                'storage_path': 'test/path/cv1.pdf',
                'text_content': 'CV content 1',
                'metadata': {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        mock_repository.get_user_documents.return_value = mock_documents
        mock_repository.get_document_count.return_value = 1
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            document_service.get_user_documents(user_id)
        
        assert "Failed to retrieve documents" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_get_user_documents_default_parameters(self, document_service, mock_repository):
        """
        Test that default parameters are used correctly
        """
        # Arrange
        user_id = uuid.uuid4()
        mock_repository.get_user_documents.return_value = []
        mock_repository.get_document_count.return_value = 0
        
        # Act
        documents, total_count = document_service.get_user_documents(user_id)
        
        # Assert
        mock_repository.get_user_documents.assert_called_once_with(
            user_id, 
            None,  # Default file_type
            50,    # Default limit
            0      # Default offset
        )
        mock_repository.get_document_count.assert_called_once_with(user_id, None)
    
    @pytest.mark.unit
    def test_get_user_documents_return_type_validation(self, document_service, mock_repository):
        """
        Test that return types are correct
        """
        # Arrange
        user_id = uuid.uuid4()
        mock_documents = [
            {
                'id': uuid.uuid4(),
                'user_id': user_id,
                'organization_id': None,
                'filename': 'cv1.pdf',
                'file_type': 'cv',
                'content_type': 'application/pdf',
                'file_size': 1024,
                'storage_path': 'test/path/cv1.pdf',
                'text_content': 'CV content 1',
                'metadata': {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        mock_repository.get_user_documents.return_value = mock_documents
        mock_repository.get_document_count.return_value = 1
        
        # Act
        result = document_service.get_user_documents(user_id)
        
        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        documents, total_count = result
        assert isinstance(documents, list)
        assert isinstance(total_count, int)
        
        if documents:
            assert all(isinstance(doc, Document) for doc in documents)

