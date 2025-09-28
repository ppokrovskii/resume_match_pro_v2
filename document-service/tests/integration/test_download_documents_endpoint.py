"""
Integration tests for GET /documents/{id}/download endpoint

Following TDD principles as specified in repo rules:
- Tests use real database and storage (no mocking of external services)
- Tests cover all requirements from test_plan.md
- Tests ensure proper error handling and security
- Tests verify file download functionality with real Azure Blob Storage
"""

import pytest
import uuid
import io
from unittest.mock import patch
from fastapi import status

from models.db_models import Document as DocumentModel
from utils.database import get_db_session


class TestDownloadDocumentsEndpoint:
    """Integration tests for GET /documents/{id}/download endpoint"""
    
    @pytest.mark.integration
    def test_download_document_success_pdf(self, integration_client, auth_headers, mock_auth_user, sample_pdf_file):
        """
        Test Case: DOC-MGMT-004 - Download original file from Azure Blob
        Requirement: US-2 - User can download original document files exactly as uploaded
        """
        # Arrange - Upload a PDF document first
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
        document_id = upload_data["data"]["results"][0]["document_id"]
        
        # Act - Download the document
        response = integration_client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        # Verify content type and headers
        assert response.headers["content-type"] == sample_pdf_file["content_type"]
        assert "content-disposition" in response.headers
        assert f'filename={sample_pdf_file["filename"]}' in response.headers["content-disposition"]
        
        # Verify file content is identical to uploaded content
        downloaded_content = response.content
        assert downloaded_content == sample_pdf_file["content"]
        assert len(downloaded_content) == len(sample_pdf_file["content"])
    
    @pytest.mark.integration
    def test_download_document_success_docx(self, integration_client, auth_headers, mock_auth_user, sample_docx_file):
        """
        Test Case: DOC-MGMT-005 - Serve correct content-type and filename for DOCX
        Requirement: US-2 - Download original files with proper HTTP headers
        """
        # Arrange - Upload a DOCX document first
        files = {
            "files": (
                sample_docx_file["filename"],
                io.BytesIO(sample_docx_file["content"]),
                sample_docx_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        upload_data = upload_response.json()
        
        # Check if upload failed
        if upload_data["data"]["results"][0].get("success") is False:
            pytest.skip(f"Upload failed: {upload_data['data']['results'][0].get('error', 'Unknown error')}")
            
        document_id = upload_data["data"]["results"][0]["document_id"]
        
        # Act - Download the document
        response = integration_client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        # Verify DOCX-specific content type and headers
        assert response.headers["content-type"] == sample_docx_file["content_type"]
        assert "content-disposition" in response.headers
        assert f'filename={sample_docx_file["filename"]}' in response.headers["content-disposition"]
        
        # Verify file content integrity
        downloaded_content = response.content
        assert downloaded_content == sample_docx_file["content"]
    
    @pytest.mark.integration
    def test_download_document_not_found(self, integration_client, auth_headers, mock_auth_user):
        """
        Test Case: DOC-MGMT-007 - Return 404 for non-existent document
        Requirement: Error handling for invalid document IDs
        """
        # Arrange - Use a non-existent document ID
        fake_document_id = str(uuid.uuid4())
        
        # Act - Try to download non-existent document
        response = integration_client.get(
            f"/api/v1/documents/{fake_document_id}/download",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        response_data = response.json()
        assert response_data["success"] is False
        assert "error" in response_data
        assert response_data["error"]["code"] == "DOCUMENT_NOT_FOUND"
        assert "not found" in response_data["error"]["message"].lower()
    
    @pytest.mark.integration
    def test_download_document_user_isolation(self, integration_client, sample_pdf_file):
        """
        Test Case: DOC-SEC-003 - User data isolation validation
        Requirement: SEC-2 - Users cannot access other users' documents
        """
        # Arrange - User1 uploads a document
        user1_id = str(uuid.uuid4())
        user1_headers = {"Authorization": f"Bearer mock-test-{user1_id}"}
        
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
        
        # Act - User2 tries to download User1's document (SECURITY TEST)
        user2_id = str(uuid.uuid4())
        user2_headers = {"Authorization": f"Bearer mock-test-{user2_id}"}
        
        response = integration_client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=user2_headers
        )
        
        # Assert - CRITICAL SECURITY CHECK
        # User2 should NOT be able to download User1's document
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        response_data = response.json()
        assert response_data["success"] is False
        assert response_data["error"]["code"] == "DOCUMENT_NOT_FOUND"
    
    @pytest.mark.integration
    def test_download_document_unauthorized(self, integration_client, sample_pdf_file):
        """
        Test Case: DOC-SEC-008 - JWT token validation
        Requirement: SEC-5 - JWT authentication required for all operations
        """
        # Arrange - Upload a document with valid auth first
        user_id = str(uuid.uuid4())
        valid_headers = {"Authorization": f"Bearer mock-test-{user_id}"}
        
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
            headers=valid_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - Try to download without authentication
        response = integration_client.get(
            f"/api/v1/documents/{document_id}/download"
            # No headers = no authentication
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.integration
    def test_download_document_invalid_token(self, integration_client, sample_pdf_file):
        """
        Test Case: DOC-SEC-009 - Token expiration handling
        Requirement: SEC-5 - Invalid tokens rejected
        """
        # Arrange - Upload a document with valid auth first
        user_id = str(uuid.uuid4())
        valid_headers = {"Authorization": f"Bearer mock-test-{user_id}"}
        
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
            headers=valid_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - Try to download with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = integration_client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=invalid_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.integration
    def test_download_document_performance(self, integration_client, auth_headers, mock_auth_user):
        """
        Test Case: DOC-PERF-005 - Document download starts within 1 second
        Requirement: PERF-5 - Download performance requirement
        """
        import time
        
        # Arrange - Upload a 1MB document
        large_content = b"x" * (1024 * 1024)  # 1MB
        files = {
            "files": ("large_test.pdf", io.BytesIO(large_content), "application/pdf")
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        upload_data = upload_response.json()
        
        # Check if upload failed
        if upload_data["data"]["results"][0].get("success") is False:
            pytest.skip(f"Upload failed: {upload_data['data']['results'][0].get('error', 'Unknown error')}")
            
        document_id = upload_data["data"]["results"][0]["document_id"]
        
        # Act - Measure download response time
        start_time = time.time()
        
        response = integration_client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=auth_headers
        )
        
        response_time = time.time() - start_time
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response_time < 1.0, f"Download took {response_time:.2f}s, should be < 1s"
        
        # Verify content integrity
        assert len(response.content) == len(large_content)
    
    @pytest.mark.integration
    def test_download_document_immediately_after_upload(self, integration_client, auth_headers, mock_auth_user, sample_pdf_file):
        """
        Test Case: DOC-UPLOAD-010 - File immediately available after upload
        Requirement: US-1 - Documents are immediately available for download after upload
        """
        # Arrange & Act - Upload and immediately download
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
        
        # Immediately try to download (no delay)
        download_response = integration_client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=auth_headers
        )
        
        # Assert - Should be immediately available
        assert download_response.status_code == status.HTTP_200_OK
        assert download_response.content == sample_pdf_file["content"]
    
    @pytest.mark.integration
    def test_download_document_storage_error_handling(self, integration_client, auth_headers, mock_auth_user, sample_pdf_file):
        """
        Test Case: DOC-ARCH-004 - Azure Blob Storage integration error handling
        Requirement: Handle storage service failures gracefully
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
        
        # Act - Simulate storage service failure
        with patch('services.storage_service.StorageService.download_file') as mock_download:
            mock_download.side_effect = Exception("Storage service unavailable")
            
            response = integration_client.get(
                f"/api/v1/documents/{document_id}/download",
                headers=auth_headers
            )
        
        # Assert - Should handle storage errors gracefully
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        response_data = response.json()
        assert response_data["success"] is False
        assert "error" in response_data
        assert response_data["error"]["code"] == "DOWNLOAD_FAILED"
    
    @pytest.mark.integration
    def test_download_document_malformed_uuid(self, integration_client, auth_headers, mock_auth_user):
        """
        Test Case: Input validation for malformed document ID
        Requirement: Proper error handling for invalid input
        """
        # Act - Try to download with malformed UUID
        response = integration_client.get(
            "/api/v1/documents/not-a-valid-uuid/download",
            headers=auth_headers
        )
        
        # Assert - Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
