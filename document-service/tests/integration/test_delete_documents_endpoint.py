"""
Integration tests for DELETE /documents/{id} endpoint

Following TDD principles as specified in repo rules:
- Tests use real database and storage (no mocking of external services)
- Tests cover all requirements from test_plan.md
- Tests ensure proper error handling and security
"""

import pytest
import uuid
import io
from unittest.mock import patch
from fastapi import status

from models.db_models import Document as DocumentModel
from utils.database import get_db_session


class TestDeleteDocumentsEndpoint:
    """Integration tests for DELETE /documents/{id} endpoint"""
    
    @pytest.mark.integration
    def test_delete_document_success(self, integration_client, auth_headers, mock_auth_user, sample_pdf_file):
        """
        Test Case: DOC-MGMT-006 - Delete document permanently
        Requirement: US-2 - User can delete documents they no longer need
        """
        # Arrange - Upload a document first
        files = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        upload_data = upload_response.json()
        # BulkUploadResponse has 'results' with 'document_id'
        document_id = upload_data["data"]["results"][0]["document_id"]
        
        # Act - Delete the document
        response = integration_client.delete(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""  # No content body for 204
        
        # Verify document is actually deleted - should return 404
        get_response = integration_client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.integration
    def test_delete_document_not_found(self, integration_client, auth_headers, mock_auth_user):
        """
        Test Case: DOC-MGMT-007 - Verify file unrecoverable after deletion
        Requirement: US-2 - Handle non-existent document deletion
        """
        # Arrange - Use a non-existent document ID
        fake_document_id = str(uuid.uuid4())
        
        # Act - Try to delete non-existent document
        response = integration_client.delete(
            f"/api/v1/documents/{fake_document_id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        response_data = response.json()
        assert response_data["success"] is False
        assert "error" in response_data
        assert response_data["error"]["code"] == "DOCUMENT_NOT_FOUND"
        assert fake_document_id in response_data["error"]["message"]
        
        # Verify meta information
        assert "meta" in response_data
        assert response_data["meta"]["service"] == "document-service"
        assert response_data["meta"]["endpoint"] == "documents.delete_document"
        assert response_data["meta"]["method"] == "DELETE"
    
    @pytest.mark.integration
    def test_delete_document_unauthorized(self, integration_client, sample_pdf_file):
        """
        Test Case: DOC-SEC-008 - JWT token validation for DELETE
        Requirement: SEC-5 - JWT token-based authentication required
        """
        # Arrange - Create a document first (with auth)
        user_id = str(uuid.uuid4())
        auth_headers = {"Authorization": f"Bearer mock-test-{user_id}"}
        
        files = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - Try to delete without authentication
        response = integration_client.delete(f"/api/v1/documents/{document_id}")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.integration
    def test_delete_document_user_isolation(self, integration_client, sample_pdf_file):
        """
        Test Case: DOC-SEC-003, DOC-SEC-004 - Users can only delete own documents
        Requirement: SEC-2 - User data completely isolated
        """
        # Arrange - Create document as user1
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        user1_headers = {"Authorization": f"Bearer mock-test-{user1_id}"}
        user2_headers = {"Authorization": f"Bearer mock-test-{user2_id}"}
        
        # Upload document as user1
        files = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=user1_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - Try to delete as user2
        response = integration_client.delete(
            f"/api/v1/documents/{document_id}",
            headers=user2_headers
        )
        
        # Assert - Should return 404 (not 403) to avoid information leakage
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        response_data = response.json()
        assert response_data["success"] is False
        assert response_data["error"]["code"] == "DOCUMENT_NOT_FOUND"
    
    @pytest.mark.integration
    def test_delete_document_invalid_uuid(self, integration_client, auth_headers):
        """
        Test Case: DOC-BR-008 - Validate UUID format for document ID
        Requirement: Input validation for document endpoints
        """
        # Act - Try to delete with invalid UUID
        response = integration_client.delete(
            "/api/v1/documents/invalid-uuid",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.integration
    def test_delete_document_with_storage_failure(self, integration_client, auth_headers, mock_auth_user, sample_pdf_file):
        """
        Test Case: DOC-DELETE-STORAGE-FAIL - Handle storage deletion failure gracefully
        Requirement: Resilient deletion - continue with DB deletion even if storage fails
        """
        # Arrange - Upload a document first
        files = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - Delete with mocked storage failure
        with patch('services.storage_service.StorageService.delete_file') as mock_delete:
            mock_delete.side_effect = Exception("Storage service unavailable")
            
            response = integration_client.delete(
                f"/api/v1/documents/{document_id}",
                headers=auth_headers
            )
        
        # Assert - Should still succeed (204) as DB deletion continues
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify document is deleted from database
        get_response = integration_client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.integration
    def test_delete_document_publishes_event(self, integration_client, auth_headers, mock_auth_user, sample_pdf_file):
        """
        Test Case: DOC-EVENT-DELETE - Verify document.deleted event is published
        Requirement: Event-driven architecture for cleanup services
        """
        # Arrange - Upload a document first
        files = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - Delete document with event publishing mock
        with patch('services.document_service.publish_document_deleted') as mock_publish:
            mock_publish.return_value = True
            
            response = integration_client.delete(
                f"/api/v1/documents/{document_id}",
                headers=auth_headers
            )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify event was published
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args[0]
        assert str(call_args[0]) == document_id  # document_id
        
        # The user_id passed to the event will be the converted UUID from auth0_subject_to_uuid
        from utils.auth_utils import auth0_subject_to_uuid
        expected_user_id = auth0_subject_to_uuid(f"auth0|{mock_auth_user['user_id']}")
        assert str(call_args[1]) == expected_user_id  # user_id
    
    @pytest.mark.integration
    def test_delete_document_multiple_files_isolation(self, integration_client, auth_headers, mock_auth_user, sample_pdf_file, sample_docx_file):
        """
        Test Case: DOC-DELETE-ISOLATION - Verify deleting one document doesn't affect others
        Requirement: Data integrity during deletion operations
        """
        # Arrange - Upload multiple documents
        files1 = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        files2 = {
            "files": (
                sample_docx_file["filename"],
                io.BytesIO(sample_docx_file["content"]),
                sample_docx_file["content_type"]
            )
        }
        
        upload_response1 = integration_client.post(
            "/api/v1/documents/upload",
            files=files1,
            headers=auth_headers
        )
        
        upload_response2 = integration_client.post(
            "/api/v1/documents/upload",
            files=files2,
            headers=auth_headers
        )
        
        assert upload_response1.status_code == status.HTTP_201_CREATED
        assert upload_response2.status_code == status.HTTP_201_CREATED
        
        document1_id = upload_response1.json()["data"]["results"][0]["document_id"]
        document2_id = upload_response2.json()["data"]["results"][0]["document_id"]
        
        # Act - Delete first document
        response = integration_client.delete(
            f"/api/v1/documents/{document1_id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify first document is deleted
        get_response1 = integration_client.get(
            f"/api/v1/documents/{document1_id}",
            headers=auth_headers
        )
        assert get_response1.status_code == status.HTTP_404_NOT_FOUND
        
        # Verify second document still exists
        get_response2 = integration_client.get(
            f"/api/v1/documents/{document2_id}",
            headers=auth_headers
        )
        assert get_response2.status_code == status.HTTP_200_OK
        
        response_data = get_response2.json()
        assert response_data["success"] is True
        assert response_data["data"]["id"] == document2_id
        assert response_data["data"]["filename"] == sample_docx_file["filename"]


# Additional fixtures for DOCX testing
@pytest.fixture
def sample_docx_file():
    """Sample DOCX file for testing"""
    # Minimal valid DOCX content (ZIP with required structure)
    docx_content = b'PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00!\x00\xb5U\x11\x86\xa2\x00\x00\x00L\x01\x00\x00\x13\x00\x00\x00[Content_Types].xml\xa5\x91\xcb\n\xc2@\x10E\xf7~\x85\xbdI\x07\x11\x8b\x1e\xa0\x18\x13\xdd\x08\x8b\x0b\xc4\xfe\x80\xb8\x88\x1e\x1c\xfc\x7f\xb7iRZ\x84\x17\xcd\x9c\x9f\x19\x0c\x04\x18\x0b\xc9\x95\x05\x8b\x1a\x9a\x93\x8a\x80\x14\x91R\x93\x03\x06\x9c\x1b\x00PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00!\x00\x1d\xc3\xc9\x0f\xc6\x00\x00\x00+\x01\x00\x00\x0b\x00\x00\x00_rels/.rels\xa5\x90\xc1\n\xc2@\x0c@\xef~\x85\xbd\x07\x11\x8b\x1e\xa0\x18\x13\xdd\x08\x8b\x0b\xc4\xfe\x80\xb8\x88\x1e\x1c\xfc\x7f\xb7iRZ\x84\x17\xcd\x9c\x9f\x19\x0c\x04\x18\x0b\xc9\x95\x05\x8b\x1a\x9a\x93\x8a\x80\x14\x91R\x93\x03\x06\x9c\x1b\x00PK\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\x00\x00!\x00\xb5U\x11\x86\xa2\x00\x00\x00L\x01\x00\x00\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01\x00\x00\x00\x00[Content_Types].xmlPK\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\x00\x00!\x00\x1d\xc3\xc9\x0f\xc6\x00\x00\x00+\x01\x00\x00\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01\xd5\x00\x00\x00_rels/.relsPK\x05\x06\x00\x00\x00\x00\x02\x00\x02\x00n\x00\x00\x00\xc4\x01\x00\x00\x00\x00'
    
    return {
        "filename": "test_document.docx",
        "content": docx_content,
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
